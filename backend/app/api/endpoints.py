# backend/app/api/endpoints.py
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import Optional
from ..models.schemas import (
    GradeRequest, GradeResponse, TutorRequest, TutorResponse, HealthResponse, Deduction,
    SaveGradeRequest,
)
from ..models.database_models import Question, Grade, User, Class
from ..core.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import func
import sys
import os
import json
import httpx
import hashlib
from pydantic import BaseModel
from datetime import datetime

try:
    import orjson as json_lib
except ImportError:
    import json as json_lib


def sse_json_dumps(obj):
    """SSE 响应的 JSON 序列化，使用标准 json 库以支持 ensure_ascii=False"""
    return json.dumps(obj, ensure_ascii=False)

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from zhipuai import ZhipuAI
from config.settings import get_settings
from backend.app.core.agents import Coordinator
from backend.app.core.cache_service import get_cache
from backend.app.core.websocket.manager import ws_manager

settings = get_settings()
coordinator = Coordinator(settings.zhipu_api_key)
client = ZhipuAI(api_key=settings.zhipu_api_key)

USE_LOCAL_MODEL = settings.use_local_model
LOCAL_MODEL_NAME = settings.local_model_name
LOCAL_MODEL_URL = settings.local_model_url
CACHE_TTL = settings.redis_ttl

router = APIRouter()

# ================= 数据库操作接口 =================

# 获取所有题目
@router.get("/questions")
async def get_all_questions(db: Session = Depends(get_db)):
    questions = db.query(Question).filter(Question.question_id != "").all()
    result = []
    for q in questions:
        result.append({
            "id": q.question_id,
            "title": q.title,
            "description": q.description,
            "python": {
                "template": q.python_template or "",
                "description": q.python_description or q.description or "",
                "rubrics": q.python_rubrics or q.rubrics or ""
            },
            "java": {
                "template": q.java_template or "",
                "description": q.java_description or q.description or "",
                "rubrics": q.java_rubrics or q.rubrics or ""
            },
            "rubrics": q.rubrics,
            "difficulty": q.difficulty,
            "created_at": q.created_at.isoformat() if q.created_at else None
        })
    return {"questions": result}

# 获取单个题目
@router.get("/questions/{question_id}")
async def get_question(question_id: str, db: Session = Depends(get_db)):
    question = db.query(Question).filter(Question.question_id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")
    return {
        "id": question.question_id,
        "title": question.title,
        "description": question.description,
        "python": {"template": question.python_template},
        "java": {"template": question.java_template},
        "rubrics": question.rubrics,
        "difficulty": question.difficulty
    }

# 添加题目
@router.post("/questions")
async def create_question(
    question_id: str = None,
    title: str = None,
    description: str = "",
    python_template: str = "",
    java_template: str = "",
    rubrics: str = "",
    difficulty: str = "简单",
    db: Session = Depends(get_db)
):
    if not question_id:
        max_id = db.query(func.max(Question.question_id)).scalar()
        if max_id is None or max_id == "":
            question_id = "1"
        else:
            try:
                question_id = str(int(max_id) + 1)
            except ValueError:
                existing_ids = [int(q.question_id) for q in db.query(Question.question_id).all() if q.question_id.isdigit()]
                question_id = str(max(existing_ids) + 1) if existing_ids else "1"
    else:
        existing = db.query(Question).filter(Question.question_id == question_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="题目ID已存在")
    
    question = Question(
        question_id=question_id,
        title=title,
        description=description,
        python_template=python_template,
        java_template=java_template,
        rubrics=rubrics,
        difficulty=difficulty,
        updated_at=datetime.now()
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    
    await ws_manager.broadcast(
        "question_created",
        {
            "question_id": question.question_id,
            "title": question.title,
            "python_template": question.python_template or "",
            "java_template": question.java_template or "",
            "python_description": question.python_description or "",
            "java_description": question.java_description or "",
        }
    )
    
    return {"success": True, "message": "题目添加成功", "question_id": question_id}

# 更新题目
@router.put("/questions/{question_id}")
async def update_question(
    question_id: str,
    title: str = None,
    description: str = None,
    python_template: str = "",
    python_description: str = None,
    python_rubrics: str = None,
    java_template: str = "",
    java_description: str = None,
    java_rubrics: str = None,
    rubrics: str = None,
    difficulty: str = None,
    db: Session = Depends(get_db)
):
    print(f"[DEBUG] update_question called with question_id={question_id}")
    print(f"[DEBUG] python_template received: {repr(python_template)}")
    print(f"[DEBUG] java_template received: {repr(java_template)}")
    
    question = db.query(Question).filter(Question.question_id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")
    
    if title is not None:
        question.title = title
    if description is not None:
        question.description = description
    if python_template is not None and python_template != "":
        question.python_template = python_template
        print(f"[DEBUG] Updated python_template to: {repr(python_template[:50] if python_template else None)}...")
    if python_description is not None:
        question.python_description = python_description
    if python_rubrics is not None:
        question.python_rubrics = python_rubrics
    if java_template is not None and java_template != "":
        question.java_template = java_template
        print(f"[DEBUG] Updated java_template to: {repr(java_template[:50] if java_template else None)}...")
    if java_description is not None:
        question.java_description = java_description
    if java_rubrics is not None:
        question.java_rubrics = java_rubrics
    if rubrics is not None:
        question.rubrics = rubrics
    if difficulty is not None:
        question.difficulty = difficulty
    question.updated_at = datetime.now()
    
    db.commit()
    db.refresh(question)
    
    print(f"[DEBUG] After commit, python_template in DB: {repr(question.python_template[:50] if question.python_template else None)}...")
    
    await ws_manager.broadcast(
        "question_updated",
        {
            "question_id": question.question_id,
            "title": question.title,
            "python_template": question.python_template or "",
            "java_template": question.java_template or "",
            "python_description": question.python_description or "",
            "java_description": question.java_description or "",
        }
    )
    
    return {"success": True, "message": "题目更新成功"}

# 删除题目
@router.delete("/questions/{question_id}")
async def delete_question(question_id: str, db: Session = Depends(get_db)):
    question = db.query(Question).filter(Question.question_id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")
    
    db.delete(question)
    db.commit()
    
    await ws_manager.broadcast(
        "question_deleted",
        {"question_id": question_id}
    )
    
    return {"success": True, "message": "题目删除成功"}

# 保存成绩
@router.post("/grades")
async def save_grade(request: SaveGradeRequest, db: Session = Depends(get_db)):
    question = db.query(Question).filter(Question.question_id == request.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")

    class_obj = db.query(Class).filter(Class.name == request.class_name).first()
    if not class_obj and request.class_name:
        class_obj = Class(name=request.class_name)
        db.add(class_obj)
        db.flush()

    class_id = class_obj.id if class_obj else None

    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if isinstance(request.deductions, str):
        try:
            deductions_json = json.loads(request.deductions)
        except json.JSONDecodeError:
            deductions_json = []
    else:
        deductions_json = request.deductions

    grade = Grade(
        user_id=request.user_id,
        user_name=request.user_name,
        question_id=question.id,
        class_id=class_id,
        code=request.code,
        language=request.language,
        overall_score=request.overall_score,
        summary=request.summary,
        deductions=deductions_json,
    )

    db.add(grade)
    db.commit()
    db.refresh(grade)

    await ws_manager.broadcast(
        "grade_saved",
        {
            "grade_id": grade.id,
            "user_id": request.user_id,
            "user_name": request.user_name,
            "question_id": request.question_id,
            "overall_score": request.overall_score,
            "class_name": request.class_name,
        },
    )

    return {"success": True, "message": "成绩保存成功", "grade_id": grade.id}

# 删除成绩
@router.delete("/grades/{grade_id}")
async def delete_grade(grade_id: int, db: Session = Depends(get_db)):
    grade = db.query(Grade).filter(Grade.id == grade_id).first()
    if not grade:
        raise HTTPException(status_code=404, detail="成绩不存在")
    
    db.delete(grade)
    db.commit()
    
    await ws_manager.broadcast(
        "grade_deleted",
        {"grade_id": grade_id}
    )
    
    return {"success": True, "message": "成绩删除成功"}
    
# 获取所有成绩
@router.get("/grades")
async def get_all_grades(db: Session = Depends(get_db)):
    grades = db.query(Grade).all()
    result = []
    for g in grades:
        question = db.query(Question).filter(Question.id == g.question_id).first()
        user = db.query(User).filter(User.id == g.user_id).first()
        class_obj = db.query(Class).filter(Class.id == g.class_id).first()
        
        result.append({
            "id": g.id,
            "user_id": g.user_id,
            "user_name": g.user_name if g.user_name else (user.name if user else "未知学生"),
            "question_id": question.question_id if question else "",
            "question_title": question.title if question else "",
            "class_name": class_obj.name if class_obj else "",
            "code": g.code,
            "language": g.language,
            "overall_score": g.overall_score,
            "summary": g.summary,
            "deductions": g.deductions,
            "submitted_at": g.submitted_at.isoformat() if g.submitted_at else None
        })
    return {"grades": result}

# 获取指定班级的成绩
@router.get("/grades/class/{class_name}")
async def get_grades_by_class(class_name: str, db: Session = Depends(get_db)):
    class_obj = db.query(Class).filter(Class.name == class_name).first()
    if not class_obj:
        raise HTTPException(status_code=404, detail="班级不存在")
    
    grades = db.query(Grade).filter(Grade.class_id == class_obj.id).all()
    result = []
    for g in grades:
        question = db.query(Question).filter(Question.id == g.question_id).first()
        user = db.query(User).filter(User.id == g.user_id).first()
        
        result.append({
            "id": g.id,
            "user_id": g.user_id,
            "user_name": g.user_name if g.user_name else (user.name if user else "未知学生"),
            "question_id": question.question_id if question else "",
            "question_title": question.title if question else "",
            "class_name": class_obj.name,
            "code": g.code,
            "language": g.language,
            "overall_score": g.overall_score,
            "summary": g.summary,
            "deductions": g.deductions,
            "submitted_at": g.submitted_at.isoformat() if g.submitted_at else None
        })
    return {"grades": result}

# 获取指定用户的成绩
@router.get("/grades/user/{user_id}")
async def get_grades_by_user(user_id: int, db: Session = Depends(get_db)):
    grades = db.query(Grade).filter(Grade.user_id == user_id).all()
    result = []
    for g in grades:
        question = db.query(Question).filter(Question.id == g.question_id).first()
        class_obj = db.query(Class).filter(Class.id == g.class_id).first()
        user = db.query(User).filter(User.id == g.user_id).first()
        
        result.append({
            "id": g.id,
            "user_id": g.user_id,
            "user_name": g.user_name if g.user_name else (user.name if user else "未知学生"),
            "question_id": question.question_id if question else "",
            "question_title": question.title if question else "",
            "class_name": class_obj.name if class_obj else "",
            "code": g.code,
            "language": g.language,
            "overall_score": g.overall_score,
            "summary": g.summary,
            "deductions": g.deductions,
            "submitted_at": g.submitted_at.isoformat() if g.submitted_at else None
        })
    return {"grades": result}

# 获取所有用户
@router.get("/users")
async def get_all_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    result = []
    for u in users:
        result.append({
            "id": u.id,
            "username": u.username,
            "name": u.name,
            "role": u.role,
            "class_name": u.class_name,
            "created_at": u.created_at.isoformat() if u.created_at else None
        })
    return {"users": result}

# 获取所有班级
@router.get("/classes")
async def get_all_classes(db: Session = Depends(get_db)):
    classes = db.query(Class).all()
    result = []
    for c in classes:
        result.append({
            "id": c.id,
            "name": c.name,
            "created_at": c.created_at.isoformat() if c.created_at else None
        })
    return {"classes": result}

# 添加班级
@router.post("/classes")
async def create_class(name: str, db: Session = Depends(get_db)):
    existing = db.query(Class).filter(Class.name == name).first()
    if existing:
        raise HTTPException(status_code=400, detail="班级已存在")
    
    class_obj = Class(name=name)
    db.add(class_obj)
    db.commit()
    db.refresh(class_obj)
    
    return {"success": True, "message": "班级添加成功"}

# 添加用户
@router.post("/users")
async def create_user(
    username: str,
    password: str,
    name: str,
    role: str = "student",
    class_name: str = "",
    db: Session = Depends(get_db)
):
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    user = User(
        username=username,
        password=password,
        name=name,
        role=role,
        class_name=class_name
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {"success": True, "message": "用户添加成功", "user_id": user.id}

# 用户登录（兼容旧版 query 参数，推荐使用 /api/login JSON 接口）
@router.post("/login/legacy")
async def login_legacy(username: str, password: str, db: Session = Depends(get_db)):
    from app.core.auth import authenticate_user, create_access_token

    user = authenticate_user(db, username, password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = create_access_token({"sub": user.username, "role": user.role})
    return {
        "success": True,
        "message": "登录成功",
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "name": user.name,
            "role": user.role,
            "class_name": user.class_name or "",
        },
    }


def hash_code_content(code: str) -> str:
    """快速计算代码内容的哈希值"""
    return hashlib.md5(code.encode('utf-8')).hexdigest()


def make_grade_cache_key(code: str, question: str, rubrics: str) -> str:
    """生成批改结果的缓存键"""
    return f"grade:{hash_code_content(code)}:{hash_code_content(question)}:{hash_code_content(rubrics)}"


async def call_local_model(prompt: str) -> str:
    """调用本地 Ollama 模型"""
    try:
        async with httpx.AsyncClient(timeout=180.0) as http_client:
            response = await http_client.post(
                LOCAL_MODEL_URL,
                json={
                    "model": LOCAL_MODEL_NAME,
                    "prompt": prompt,
                    "stream": False
                }
            )
            result = response.json().get("response", "")
            print(f"✅ 本地模型已响应，返回长度: {len(result)}")
            return result
    except Exception as e:
        print(f"❌ 本地模型调用失败: {e}")
        return ""


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="ok", version="2.2.0")


@router.get("/cache/stats")
async def cache_stats():
    """获取缓存统计信息"""
    cache = get_cache()
    return cache.get_stats()


@router.post("/cache/clear")
async def clear_cache():
    """清空所有缓存"""
    cache = get_cache()
    cache.clear()
    return {"status": "ok", "message": "缓存已清空"}


@router.get("/model/status")
async def model_status():
    return {
        "use_local": USE_LOCAL_MODEL,
        "local_model": LOCAL_MODEL_NAME,
        "cloud_model": "glm-4-flash",
        "mode": "本地模型" if USE_LOCAL_MODEL else "云端模型",
        "cache_enabled": settings.redis_enabled
    }


class ModelToggleRequest(BaseModel):
    use_local: bool


@router.post("/model/toggle")
async def toggle_model(request: ModelToggleRequest):
    global USE_LOCAL_MODEL
    USE_LOCAL_MODEL = request.use_local
    return {
        "use_local": USE_LOCAL_MODEL,
        "mode": "本地模型" if USE_LOCAL_MODEL else "云端模型"
    }


@router.post("/grade", response_model=GradeResponse)
async def grade_code(request: GradeRequest):
    try:
        # 尝试从缓存获取
        cache = get_cache()
        cache_key = make_grade_cache_key(request.code, request.question, request.rubrics)
        cached_result = cache.get(cache_key)
        
        if cached_result is not None:
            print(f"✅ 命中缓存，直接返回")
            return GradeResponse(**cached_result)
        
        # 未命中缓存，执行批改
        result = coordinator.grade_workflow(
    request.code, 
    request.question, 
    request.rubrics,
    request.language
)
        evaluation = result["evaluation"]
        diagnosis = result.get("diagnosis", {})
        
        response = GradeResponse(
            overall_score=evaluation.get("overall_score", 0),
            summary=evaluation.get("summary", ""),
            deductions=[
                Deduction(
                    line=d.get("line", 0),
                    type=d.get("type", ""),
                    points_deducted=d.get("points_deducted", 0),
                    reason=d.get("reason", ""),
                    suggestion=d.get("suggestion", ""),
                    ai_generated=True
                ) for d in evaluation.get("deductions", [])
            ],
            diagnosis_summary=diagnosis.get("summary", ""),
            weak_knowledge_points=diagnosis.get("weak_knowledge_points", []),
            ai_generated=True
        )
        
        # 存入缓存
        cache.set(cache_key, response.model_dump(), ttl=CACHE_TTL)
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/grade/stream")
async def grade_code_stream(request: GradeRequest):
    """流式批改代码"""
    from app.core.utils.logger import setup_logger
    logger = setup_logger('grade_stream', 'logs/grade.log')
    
    async def generate():
        try:
            logger.info(f"开始批改: question_id={request.question[:50]}, code_length={len(request.code)}, language={request.language}")
            
            # 先检查缓存（非流式结果）
            cache = get_cache()
            cache_key = make_grade_cache_key(request.code, request.question, request.rubrics)
            cached_result = cache.get(cache_key)
            
            if cached_result is not None:
                logger.info(f"✅ 命中缓存: cache_key={cache_key}")
                print(f"✅ 命中缓存")
                yield f"data: {sse_json_dumps({'type': 'diagnosis', 'content': '从缓存加载数据中...'})}\n\n"
                
                # 输出评语
                for char in cached_result.get("summary", ""):
                    yield f"data: {sse_json_dumps({'type': 'review', 'content': char})}\n\n"
                
                # 输出结果
                result_data = {
                    'type': 'result', 
                    'data': {
                        'overall_score': cached_result['overall_score'],
                        'summary': cached_result['summary'],
                        'deductions': cached_result['deductions']
                    }
                }
                yield f"data: {sse_json_dumps(result_data)}\n\n"
                yield "data: [DONE]\n\n"
                return
            
            # 未命中缓存，正常执行
            logger.info("未命中缓存，开始诊断")
            diagnosis = coordinator.diagnostician.diagnose(
                code=request.code, 
                question=request.question
            )
            
            diag_msg = f"🔍 诊断完成：{diagnosis.get('summary', '')}"
            logger.info(f"诊断结果: {diagnosis.get('summary', '')}")
            yield f"data: {sse_json_dumps({'type': 'diagnosis', 'content': diag_msg})}\n\n"
            
            lang_hint = ""
            if request.language == "java":
                lang_hint = "请注意这是 Java 代码。"

            review_prompt = f"""{lang_hint}
你是一位编程导师"码途智伴"。请用自然语言对学生的代码进行评价。

题目：{request.question}
学生代码：
{request.code}

诊断信息：{diagnosis.get('summary', '')}

请用中文输出评语，包含：
1. 代码的整体评价
2. 指出存在的问题
3. 给出改进建议（如果涉及代码示例，请用 ```python 和 ``` 包裹代码块）

语气要耐心、鼓励性，字数在300字以内。"""
            
            review_system = "你是码途智伴，一位耐心又严谨的编程导师。请用自然语言评价学生代码，不要输出JSON格式。"
            
            review_text = ""
            if USE_LOCAL_MODEL:
                review_text = await call_local_model(f"{review_system}\n\n{review_prompt}")
                for char in review_text:
                    yield f"data: {sse_json_dumps({'type': 'review', 'content': char})}\n\n"
            else:
                response1 = client.chat.completions.create(
                    model="glm-4-flash",
                    messages=[
                        {"role": "system", "content": review_system},
                        {"role": "user", "content": review_prompt}
                    ],
                    stream=True,
                    temperature=0.5
                )
                for chunk in response1:
                    content = chunk.choices[0].delta.content
                    if content is not None:
                        review_text += content
                        yield f"data: {sse_json_dumps({'type': 'review', 'content': content})}\n\n"

            score_prompt = f"""请根据以下信息生成评分JSON。

题目：{request.question}
评分标准：{request.rubrics}
学生代码：
{request.code}

请直接输出JSON（不要用markdown代码块包裹）：
{{
    "overall_score": 整数(0-100),
    "deductions": [
        {{
            "line": 行号,
            "type": "错误类型",
            "points_deducted": 扣分,
            "reason": "扣分原因",
            "suggestion": "改进建议"
        }}
    ]
}}"""
            
            review_system = "你是一位严谨的Python编程导师'码途智伴'。你的任务是根据【诊断报告】【题目要求】【评分标准】批改学生代码。严格按JSON格式输出，不要输出任何其他内容。"
            
            # 直接生成完整的批改JSON（包含评语和评分）
            result_text = ""
            model_used = "本地模型" if USE_LOCAL_MODEL else "云端模型"
            logger.info(f"使用模型: {model_used}")
            
            # 使用score_prompt而不是review_prompt，因为review_prompt是生成评语的prompt
            grading_prompt = f"""{lang_hint}
你是一位严谨的Python编程导师'码途智伴'。
你的任务是根据【诊断报告】【题目要求】【评分标准】批改学生代码，参考知识库资料。

题目：{request.question}
评分标准：{request.rubrics or '无特定评分标准，请根据代码正确性、逻辑完整性、代码规范综合评分'}
学生代码：
{request.code}

诊断信息：{diagnosis.get('summary', '无')}

请严格按以下JSON格式输出，不要使用markdown代码块包裹：
{{
    "overall_score": 整数(0-100),
    "summary": "总体评价（需要详细分析代码的优点、存在的问题，给出具体的改进建议和示例代码）",
    "deductions": [
        {{
            "line": 行号(整数),
            "type": "错误类型字符串",
            "points_deducted": 扣分数(整数),
            "reason": "扣分原因字符串（要具体指出代码中的问题）",
            "suggestion": "改进建议字符串（要给出具体的改进方法和优化后的代码示例）"
        }}
    ]
}}

重要提醒：
- summary字段必须详细，包含：1)代码优点 2)存在的问题 3)具体的改进建议和示例代码
- deductions数组中的每个条目都必须包含完整的suggestion（改进建议）
- 如果代码有问题，必须在deductions中详细列出
- 只输出一个完整的JSON对象
- 不要输出任何其他文字
- 确保JSON格式完全正确"""
            
            if USE_LOCAL_MODEL:
                try:
                    result_text = await call_local_model(f"{review_system}\n\n{grading_prompt}")
                    logger.info(f"本地模型返回长度: {len(result_text)}")
                    
                    # 如果本地模型返回空内容，尝试使用云端模型作为fallback
                    if not result_text or len(result_text.strip()) == 0:
                        logger.warning("⚠️ 本地模型返回空内容，切换到云端模型")
                        if settings.zhipu_api_key:
                            response = client.chat.completions.create(
                                model="glm-4-flash",
                                messages=[
                                    {"role": "system", "content": review_system},
                                    {"role": "user", "content": grading_prompt}
                                ],
                                temperature=0.1
                            )
                            result_text = response.choices[0].message.content or ""
                            logger.info(f"云端模型返回长度: {len(result_text)}")
                        else:
                            logger.error("❌ 智谱AI API key未配置，无法使用云端模型")
                except Exception as e:
                    logger.error(f"❌ 本地模型调用失败: {e}", exc_info=True)
                    # 尝试使用云端模型作为fallback
                    if settings.zhipu_api_key:
                        logger.warning("⚠️ 本地模型调用失败，切换到云端模型")
                        try:
                            response = client.chat.completions.create(
                                model="glm-4-flash",
                                messages=[
                                    {"role": "system", "content": review_system},
                                    {"role": "user", "content": grading_prompt}
                                ],
                                temperature=0.1
                            )
                            result_text = response.choices[0].message.content or ""
                            logger.info(f"云端模型返回长度: {len(result_text)}")
                        except Exception as e2:
                            logger.error(f"❌ 云端模型也失败: {e2}", exc_info=True)
            else:
                response = client.chat.completions.create(
                    model="glm-4-flash",
                    messages=[
                        {"role": "system", "content": review_system},
                        {"role": "user", "content": grading_prompt}
                    ],
                    temperature=0.1
                )
                result_text = response.choices[0].message.content or ""
                logger.info(f"云端模型返回长度: {len(result_text)}")
            
            # 检查返回内容是否为空
            if not result_text or len(result_text.strip()) == 0:
                logger.error("❌ 模型返回内容为空")
                error_result = {'type': 'result', 'data': {
                    'overall_score': 10, 
                    'summary': '模型返回内容为空，请检查模型配置或网络连接。', 
                    'deductions': []
                }}
                yield f"data: {sse_json_dumps(error_result)}\n\n"
                yield "data: [DONE]\n\n"
                return
            
            # 记录原始返回内容（用于调试）
            logger.debug(f"模型原始返回内容（前500字符）: {result_text[:500]}")
            
            # 清理可能的markdown代码块包裹
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            elif result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            result_text = result_text.strip()
            
            logger.info(f"清理后的内容长度: {len(result_text)}")
            
            try:
                score_data = json_lib.loads(result_text)
                
                logger.info(f"评分JSON解析成功: overall_score={score_data.get('overall_score')}, deductions_count={len(score_data.get('deductions', []))}")
                logger.debug(f"完整JSON数据: {score_data}")
                
                # 验证JSON格式完整性
                if 'overall_score' not in score_data:
                    score_data['overall_score'] = 10
                    logger.warning("⚠️ JSON缺少overall_score字段，设置为默认值10分")
                
                if 'summary' not in score_data:
                    score_data['summary'] = '批改完成，请查看详细扣分情况。'
                    logger.warning("⚠️ JSON缺少summary字段，设置为默认值")
                
                if 'deductions' not in score_data:
                    score_data['deductions'] = []
                    logger.warning("⚠️ JSON缺少deductions字段，设置为空数组")
                
                # 验证并修正deductions中的每个条目
                valid_deductions = []
                for d in score_data.get('deductions', []):
                    if isinstance(d, dict) and 'type' in d and 'reason' in d:
                        valid_deduction = {
                            'line': d.get('line', 0),
                            'type': d.get('type', '未知错误'),
                            'points_deducted': d.get('points_deducted', 0),
                            'reason': d.get('reason', ''),
                            'suggestion': d.get('suggestion', '')
                        }
                        valid_deductions.append(valid_deduction)
                    else:
                        logger.warning(f"⚠️ 跳过一个无效的deduction条目: {d}")
                score_data['deductions'] = valid_deductions
                
                # 验证成绩计算逻辑
                total_deducted = sum(d.get('points_deducted', 0) for d in score_data.get('deductions', []))
                calculated_score = 100 - total_deducted
                
                logger.info(f"成绩验证: total_deducted={total_deducted}, calculated_score={calculated_score}")
                
                # 确保成绩在合理范围内
                if request.code.strip() and not request.code.strip().startswith('#') and 'pass' not in request.code.strip():
                    # 如果代码有实质内容，最低给10分
                    if score_data.get('overall_score', 0) < 10:
                        original_score = score_data.get('overall_score', 0)
                        score_data['overall_score'] = 10
                        logger.warning(f"⚠️ 成绩过低，从{original_score}调整为最低分10分")
                        print(f"⚠️ 成绩过低，调整为最低分10分")
                
                # 确保成绩不超过100分
                if score_data.get('overall_score', 0) > 100:
                    original_score = score_data.get('overall_score', 0)
                    score_data['overall_score'] = 100
                    logger.warning(f"⚠️ 成绩过高，从{original_score}调整为最高分100分")
                
                # 确保成绩不低于0分
                if score_data.get('overall_score', 0) < 0:
                    original_score = score_data.get('overall_score', 0)
                    score_data['overall_score'] = 0
                    logger.warning(f"⚠️ 成绩为负数，从{original_score}调整为0分")
                
                logger.info(f"最终成绩: overall_score={score_data['overall_score']}")
                
                # 缓存结果
                cache.set(cache_key, {
                    "overall_score": score_data["overall_score"],
                    "summary": score_data["summary"],
                    "deductions": score_data["deductions"]
                }, ttl=CACHE_TTL)
                
                # 先逐字输出评语（流式显示）
                logger.info("开始流式输出评语...")
                summary_text = score_data.get("summary", "")
                for char in summary_text:
                    yield f"data: {sse_json_dumps({'type': 'review', 'content': char})}\n\n"
                logger.info(f"评语输出完成，长度: {len(summary_text)}")
                
                # 然后输出完整的批改结果（包括扣分明细）
                result_data = {'type': 'result', 'data': score_data}
                yield f"data: {sse_json_dumps(result_data)}\n\n"
                logger.info("批改完成，结果已发送")
                
                # 发送完成信号并立即返回
                yield "data: [DONE]\n\n"
                logger.info("已发送[DONE]信号，批改流程正常结束")
                return
            except json_lib.JSONDecodeError as e:
                logger.error(f"❌ JSON解析失败: {e}", exc_info=True)
                logger.error(f"❌ 原始返回内容: {result_text[:500] if len(result_text) > 500 else result_text}")
                print(f"❌ JSON解析失败: {e}")
                print(f"❌ 原始返回内容: {result_text[:500] if len(result_text) > 500 else result_text}")
                import traceback
                traceback.print_exc()
                error_result = {'type': 'result', 'data': {'overall_score': 10, 'summary': '批改过程中出现错误，已给予基础分10分。', 'deductions': []}}
                yield f"data: {sse_json_dumps(error_result)}\n\n"
                logger.info("已发送错误结果（基础分10分）")
            except Exception as e:
                logger.error(f"❌ 批改过程异常: {e}", exc_info=True)
                logger.error(f"❌ 原始返回内容: {result_text[:500] if len(result_text) > 500 else result_text}")
                print(f"❌ 批改过程异常: {e}")
                print(f"❌ 原始返回内容: {result_text[:500] if len(result_text) > 500 else result_text}")
                import traceback
                traceback.print_exc()
                error_result = {'type': 'result', 'data': {'overall_score': 10, 'summary': '批改过程中出现错误，已给予基础分10分。', 'deductions': []}}
                yield f"data: {sse_json_dumps(error_result)}\n\n"
                logger.info("已发送错误结果（基础分10分）")
            
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            error_data = {'type': 'error', 'content': str(e)}
            yield f"data: {sse_json_dumps(error_data)}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/tutor", response_model=TutorResponse)
async def tutor_chat(request: TutorRequest):
    try:
        answer = coordinator.tutoring_workflow(
            request.question,
            request.chat_history,
            request.student_code,
            request.report_json
        )
        return TutorResponse(answer=answer, ai_generated=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tutor/stream")
async def tutor_chat_stream(request: TutorRequest):
    async def generate():
        try:
            messages = [{"role": "system", "content": "你是码途智伴，一位耐心的编程导师。回答要简洁、鼓励性。"}]
            
            for msg in request.chat_history:
                messages.append({"role": msg["role"], "content": msg["content"]})
            
            if request.report_json and request.report_json != "{}":
                messages.append({"role": "system", "content": f"批改报告: {request.report_json}"})
            
            if request.student_code:
                messages.append({"role": "system", "content": f"学生当前代码:\n```\n{request.student_code}\n```"})
            
            messages.append({"role": "user", "content": request.question})
            
            if USE_LOCAL_MODEL:
                prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
                answer = await call_local_model(prompt)
                for char in answer:
                    yield f"data: {sse_json_dumps({'content': char})}\n\n"
            else:
                response = client.chat.completions.create(
                    model="glm-4-flash",
                    messages=messages,
                    stream=True,
                    temperature=0.7
                )
                for chunk in response:
                    content = chunk.choices[0].delta.content
                    if content is not None:
                        yield f"data: {sse_json_dumps({'content': content})}\n\n"
            
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            yield f"data: {sse_json_dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


class PracticeRequest(BaseModel):
    weak_points: list = []
    language: str = "python"


@router.post("/generate/practice")
async def generate_practice(request: PracticeRequest):
    weak_points = request.weak_points
    language = request.language
    
    if not weak_points:
        return {"practices": []}
    
    # 尝试从缓存获取
    cache = get_cache()
    cache_key = f"practice:{hash_code_content(str(weak_points))}:{language}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    
    practices = []
    for i, wp in enumerate(weak_points[:2]):
        if language == "java":
            practices.append({
                "description": f"针对「{wp}」的Java专项练习",
                "difficulty": 1,
                "template": f"// 练习：{wp}\npublic class Main {{\n    // TODO: 解决{wp}问题\n}}"
            })
        else:
            practices.append({
                "description": f"针对「{wp}」的Python专项练习",
                "difficulty": 1,
                "template": f"# 练习：{wp}\ndef solution():\n    # TODO: 解决{wp}问题\n    pass"
            })
    
    result = {"practices": practices}
    cache.set(cache_key, result, ttl=CACHE_TTL)
    return result


class SandboxRequest(BaseModel):
    code: str
    language: str = "python"
    timeout: int = 5


# 简化的代码执行接口（供学生端使用）
@router.post("/execute")
async def execute_code(request: SandboxRequest):
    """简化的代码执行接口"""
    return await execute_sandbox(request)


# ================= Ollama 离线模式支持 =================

@router.get("/ollama/status")
async def check_ollama_status():
    """检查Ollama服务状态和模型可用性"""
    import httpx
    
    status = {
        "connected": False,
        "model_available": False,
        "model_name": LOCAL_MODEL_NAME,
        "error": None,
        "suggestion": ""
    }
    
    try:
        # 检查Ollama服务是否运行
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:11434/api/tags")
            
            if response.status_code == 200:
                status["connected"] = True
                data = response.json()
                models = data.get('models', [])
                
                # 检查指定模型是否可用
                model_prefix = LOCAL_MODEL_NAME.split(':')[0]
                status["model_available"] = any(
                    model.get('name', '').startswith(model_prefix) 
                    for model in models
                )
                
                if not status["model_available"]:
                    status["suggestion"] = f"请运行命令下载模型: `ollama pull {LOCAL_MODEL_NAME}`"
            else:
                status["error"] = f"Ollama服务返回错误: {response.status_code}"
                
    except httpx.ConnectError:
        status["error"] = "无法连接到Ollama服务，请确保Ollama已启动"
        status["suggestion"] = "请先安装Ollama并启动服务，然后运行: `ollama pull qwen2.5:7b`"
    except Exception as e:
        status["error"] = str(e)
    
    return status


@router.post("/ollama/pull")
async def pull_ollama_model():
    """拉取Ollama模型"""
    import httpx
    
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                "http://localhost:11434/api/pull",
                json={"name": LOCAL_MODEL_NAME, "stream": False}
            )
            
            if response.status_code == 200:
                return {"success": True, "message": f"模型 {LOCAL_MODEL_NAME} 拉取成功"}
            else:
                return {"success": False, "message": f"拉取失败: {response.text}"}
                
    except Exception as e:
        return {"success": False, "message": f"拉取失败: {str(e)}"}


@router.post("/sandbox/execute")
async def execute_sandbox(request: SandboxRequest):
    try:
        import subprocess
        from app.core.sandbox.secure_executor import SecureExecutor
        from app.core.sandbox.docker_java_executor import DockerJavaExecutor

        if request.language == "java":
            if settings.docker_java_enabled:
                executor = DockerJavaExecutor(
                    image=settings.docker_java_image,
                    timeout=request.timeout,
                )
                return executor.execute(request.code)

            import subprocess
            import tempfile
            import shutil

            tmpdir = tempfile.mkdtemp()
            filepath = os.path.join(tmpdir, "Main.java")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(request.code)

            result = subprocess.run(
                ["javac", filepath], capture_output=True, text=True, timeout=request.timeout
            )
            if result.returncode != 0:
                shutil.rmtree(tmpdir, ignore_errors=True)
                return {"success": False, "error": result.stderr, "output": ""}

            result = subprocess.run(
                ["java", "-cp", tmpdir, "Main"],
                capture_output=True,
                text=True,
                timeout=request.timeout,
            )
            shutil.rmtree(tmpdir, ignore_errors=True)
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
            }

        executor = SecureExecutor()
        return executor.execute_python(request.code)
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"执行超时（{request.timeout}秒）", "output": ""}
    except FileNotFoundError:
        return {"success": False, "error": "未找到对应的运行环境（Python/Java/Docker）", "output": ""}
    except ImportError as e:
        return {"success": False, "error": f"导入模块失败: {str(e)}", "output": ""}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e), "output": ""}


# ================= Coze 集成 =================
class CozeRequest(BaseModel):
    description: str


@router.post("/coze/rubrics")
async def coze_generate_rubrics(request: CozeRequest):
    try:
        from src.coze.coze_client import CozeClient
        coze = CozeClient()
        result = coze.generate_rubrics(request.description)
        return result
    except Exception as e:
        return {"success": False, "error": str(e), "rubrics": ""}


# ================= LTI 平台对接 =================
from datetime import datetime

class LTIRequest(BaseModel):
    user_id: str
    assignment_id: str
    code: str
    language: str = "python"

class LTIResponse(BaseModel):
    user_id: str
    assignment_id: str
    score: int
    feedback: str
    submitted_at: str

questionBank = {
    "q1": {"description": "找最大值", "rubrics": "1. 逻辑正确(60分)；2. 代码规范(20分)；3. 边界处理(20分)"},
    "q2": {"description": "列表去重", "rubrics": "1. 逻辑正确(60分)；2. 代码规范(20分)；3. 效率(20分)"},
}

@router.post("/lti/submit", response_model=LTIResponse)
async def lti_submit(request: LTIRequest):
    question = questionBank.get(request.assignment_id, {
        "description": "编写函数解决问题",
        "rubrics": "1. 逻辑正确(60分)；2. 代码规范(20分)；3. 边界处理(20分)"
    })
    
    result = coordinator.grade_workflow(
        request.code,
        question.get("description", ""),
        question.get("rubrics", "")
    )
    
    return LTIResponse(
        user_id=request.user_id,
        assignment_id=request.assignment_id,
        score=result["evaluation"]["overall_score"],
        feedback=result["final_report"],
        submitted_at=datetime.now().isoformat()
    )

class LearningPathRequest(BaseModel):
    weak_points: list = []
    language: str = "python"

@router.post("/learning-path")
async def generate_learning_path(request: LearningPathRequest):
    """根据薄弱知识点生成个性化学习路径（已缓存）"""
    weak_points = request.weak_points
    language = request.language
    
    # 尝试从缓存获取
    cache = get_cache()
    cache_key = f"learning_path:{hash_code_content(str(weak_points))}:{language}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    
    # 知识图谱中的学习路径映射
    knowledge_map = {
        "语法错误": {
            "python": [
                {"step": 1, "name": "Python基础语法", "desc": "学习函数定义、缩进、冒号等基本语法", "resource": "Python官方文档-语法篇"},
                {"step": 2, "name": "常见语法错误", "desc": "了解SyntaxError的产生原因和修复方法", "resource": "语法错误排查练习"},
            ],
            "java": [
                {"step": 1, "name": "Java基础语法", "desc": "学习类定义、方法声明、分号等基本语法", "resource": "Java入门-语法篇"},
                {"step": 2, "name": "编译错误排查", "desc": "学习使用javac编译错误信息定位问题", "resource": "Java编译错误指南"},
            ]
        },
        "初始化错误": {
            "python": [
                {"step": 1, "name": "变量初始化", "desc": "理解变量在使用前必须赋值，学习选择合适的初始值", "resource": "变量初始化最佳实践"},
                {"step": 2, "name": "边界条件处理", "desc": "学习如何处理空列表、全负数等特殊输入", "resource": "边界条件练习"},
            ],
            "java": [
                {"step": 1, "name": "变量初始化", "desc": "理解Java变量初始化规则和默认值", "resource": "Java变量初始化"},
                {"step": 2, "name": "边界条件处理", "desc": "学习处理空数组和特殊输入", "resource": "边界条件练习"},
            ]
        },
        "索引越界": {
            "python": [
                {"step": 1, "name": "列表索引基础", "desc": "理解0-based索引和len()函数", "resource": "列表操作基础"},
                {"step": 2, "name": "安全遍历技巧", "desc": "学习使用for...in和range(len-1)避免越界", "resource": "安全遍历练习"},
            ],
            "java": [
                {"step": 1, "name": "数组索引基础", "desc": "理解数组长度和索引范围", "resource": "Java数组操作"},
                {"step": 2, "name": "安全遍历技巧", "desc": "学习使用for-each和边界检查", "resource": "Java数组遍历练习"},
            ]
        },
        "忘记返回值": {
            "python": [
                {"step": 1, "name": "函数定义", "desc": "理解函数的输入输出，return语句的作用", "resource": "Python函数教程"},
                {"step": 2, "name": "返回值最佳实践", "desc": "学习确保函数在所有路径都有返回值", "resource": "函数返回值练习"},
            ],
            "java": [
                {"step": 1, "name": "方法定义", "desc": "理解方法的返回类型和return语句", "resource": "Java方法教程"},
                {"step": 2, "name": "返回值最佳实践", "desc": "学习确保方法在所有路径都有返回值", "resource": "方法返回值练习"},
            ]
        },
    }
    
    # 默认路径
    default_path = [
        {"step": 1, "name": "基础知识巩固", "desc": "回顾编程基础概念", "resource": "编程基础教程"},
        {"step": 2, "name": "专项练习", "desc": "针对薄弱环节进行练习", "resource": "专项练习集"},
        {"step": 3, "name": "综合实践", "desc": "完成综合项目巩固所学", "resource": "综合项目练习"},
    ]
    
    # 匹配路径
    all_steps = []
    seen = set()
    for wp in weak_points[:3]:  # 取前3个薄弱点
        path = knowledge_map.get(wp, {}).get(language, [])
        for step in path:
            if step["name"] not in seen:
                all_steps.append(step)
                seen.add(step["name"])
    
    if not all_steps:
        all_steps = default_path
    
    result = {
        "weak_points": weak_points,
        "path": all_steps,
        "total_steps": len(all_steps)
    }
    
    # 缓存结果
    cache.set(cache_key, result, ttl=CACHE_TTL)
    return result

# ================= 题库管理 API =================

# 题库存储文件路径
# ================= 题库管理 API（数据库版补充） =================

class QuestionUpdateRequest(BaseModel):
    """题目更新请求体"""
    title: str = None
    description: str = None
    languages: list = None
    python: dict = None
    java: dict = None
    rubrics: str = None
    difficulty: str = None

@router.put("/questions/update/{question_id}")
async def update_question_full(question_id: str, request: QuestionUpdateRequest, db: Session = Depends(get_db)):
    """通过JSON body更新题目"""
    question = db.query(Question).filter(Question.question_id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")
    
    if request.title is not None:
        question.title = request.title
    if request.description is not None:
        question.description = request.description
    if request.rubrics is not None:
        question.rubrics = request.rubrics
    if request.difficulty is not None:
        question.difficulty = request.difficulty
    if request.python is not None:
        question.python_template = request.python.get("template", question.python_template)
        question.python_description = request.python.get("description", question.python_description)
        question.python_rubrics = request.python.get("rubrics", question.python_rubrics)
    if request.java is not None:
        question.java_template = request.java.get("template", question.java_template)
        question.java_description = request.java.get("description", question.java_description)
        question.java_rubrics = request.java.get("rubrics", question.java_rubrics)
    
    question.updated_at = datetime.now()
    db.commit()
    db.refresh(question)
    
    return {"success": True, "message": "题目更新成功"}