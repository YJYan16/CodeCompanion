# backend/app/api/endpoints.py
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from ..models.schemas import GradeRequest, GradeResponse, TutorRequest, TutorResponse, HealthResponse, Deduction
from ..models.database_models import Question, Grade, User, Class
from ..core.database import get_db
from sqlalchemy.orm import Session
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
    questions = db.query(Question).all()
    result = []
    for q in questions:
        result.append({
            "id": q.question_id,
            "title": q.title,
            "description": q.description,
            "python": {"template": q.python_template},
            "java": {"template": q.java_template},
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
    question_id: str,
    title: str,
    description: str = "",
    python_template: str = "",
    java_template: str = "",
    rubrics: str = "",
    difficulty: str = "简单",
    db: Session = Depends(get_db)
):
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
    
    return {"success": True, "message": "题目添加成功"}

# 更新题目
@router.put("/questions/{question_id}")
async def update_question(
    question_id: str,
    title: str = None,
    description: str = None,
    python_template: str = None,
    java_template: str = None,
    rubrics: str = None,
    difficulty: str = None,
    db: Session = Depends(get_db)
):
    question = db.query(Question).filter(Question.question_id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")
    
    if title:
        question.title = title
    if description:
        question.description = description
    if python_template:
        question.python_template = python_template
    if java_template:
        question.java_template = java_template
    if rubrics:
        question.rubrics = rubrics
    if difficulty:
        question.difficulty = difficulty
    question.updated_at = datetime.now()
    
    db.commit()
    db.refresh(question)
    
    return {"success": True, "message": "题目更新成功"}

# 删除题目
@router.delete("/questions/{question_id}")
async def delete_question(question_id: str, db: Session = Depends(get_db)):
    question = db.query(Question).filter(Question.question_id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")
    
    db.delete(question)
    db.commit()
    
    return {"success": True, "message": "题目删除成功"}

# 保存成绩
@router.post("/grades")
async def save_grade(
    user_id: int,
    question_id: str,
    code: str,
    language: str,
    overall_score: float,
    summary: str,
    deductions: str,
    class_name: str = "",
    db: Session = Depends(get_db)
):
    # 获取题目ID
    question = db.query(Question).filter(Question.question_id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")
    
    # 获取班级
    class_obj = db.query(Class).filter(Class.name == class_name).first()
    class_id = class_obj.id if class_obj else None
    
    # 获取用户
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 解析deductions
    try:
        deductions_json = json.loads(deductions)
    except:
        deductions_json = []
    
    grade = Grade(
        user_id=user_id,
        question_id=question.id,
        class_id=class_id,
        code=code,
        language=language,
        overall_score=overall_score,
        summary=summary,
        deductions=deductions_json
    )
    
    db.add(grade)
    db.commit()
    db.refresh(grade)
    
    return {"success": True, "message": "成绩保存成功", "grade_id": grade.id}

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
            "user_name": user.name if user else "",
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
            "user_name": user.name if user else "",
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
        
        result.append({
            "id": g.id,
            "user_id": g.user_id,
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

# 用户登录
@router.post("/login")
async def login(username: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户名不存在")
    
    if user.password != password:
        raise HTTPException(status_code=401, detail="密码错误")
    
    return {
        "success": True,
        "message": "登录成功",
        "user": {
            "id": user.id,
            "username": user.username,
            "name": user.name,
            "role": user.role,
            "class_name": user.class_name
        }
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
    return HealthResponse(status="ok", version="2.1.0")


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
            request.rubrics
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
    async def generate():
        try:
            # 先检查缓存（非流式结果）
            cache = get_cache()
            cache_key = make_grade_cache_key(request.code, request.question, request.rubrics)
            cached_result = cache.get(cache_key)
            
            if cached_result is not None:
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
            diagnosis = coordinator.diagnostician.diagnose(
                code=request.code, 
                question=request.question
            )
            
            diag_msg = f"🔍 诊断完成：{diagnosis.get('summary', '')}"
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
            
            result_text = ""
            if USE_LOCAL_MODEL:
                result_text = await call_local_model(f"你是评分助手，只输出JSON。\n\n{score_prompt}")
            else:
                response2 = client.chat.completions.create(
                    model="glm-4-flash",
                    messages=[
                        {"role": "system", "content": "你是评分助手，请根据评分标准输出JSON。只输出JSON，不要其他内容。"},
                        {"role": "user", "content": score_prompt}
                    ],
                    temperature=0.1
                )
                result_text = response2.choices[0].message.content
            
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            elif result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            result_text = result_text.strip()
            
            try:
                score_data = json_lib.loads(result_text)
                score_data["summary"] = review_text
                
                # 缓存结果
                cache.set(cache_key, {
                    "overall_score": score_data["overall_score"],
                    "summary": review_text,
                    "deductions": score_data["deductions"]
                }, ttl=CACHE_TTL)
                
                result_data = {'type': 'result', 'data': score_data}
                yield f"data: {sse_json_dumps(result_data)}\n\n"
            except Exception as e:
                print(f"❌ JSON解析失败: {e}")
                error_result = {'type': 'result', 'data': {'overall_score': 0, 'summary': review_text, 'deductions': []}}
                yield f"data: {sse_json_dumps(error_result)}\n\n"
            
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
    import subprocess
    import tempfile
    
    try:
        if request.language == "java":
            tmpdir = tempfile.mkdtemp()
            filepath = os.path.join(tmpdir, "Main.java")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(request.code)
            
            result = subprocess.run(["javac", filepath], capture_output=True, text=True, timeout=request.timeout)
            if result.returncode != 0:
                return {"success": False, "error": result.stderr, "output": ""}
            
            result = subprocess.run(["java", "-cp", tmpdir, "Main"], capture_output=True, text=True, timeout=request.timeout)
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)
            return {"success": result.returncode == 0, "output": result.stdout, "error": result.stderr}
        else:
            from src.sandbox.secure_executor import SecureExecutor
            executor = SecureExecutor()
            return executor.execute_python(request.code)
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"执行超时（{request.timeout}秒）", "output": ""}
    except FileNotFoundError:
        return {"success": False, "error": "未找到对应的运行环境（Python/Java）", "output": ""}
    except Exception as e:
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
