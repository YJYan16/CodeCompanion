# backend/app/api/endpoints.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from ..models.schemas import GradeRequest, GradeResponse, TutorRequest, TutorResponse, HealthResponse, Deduction
import sys
import os
import json
import httpx
import hashlib
from pydantic import BaseModel

# 性能优化：使用 orjson
try:
    import orjson as json_lib
except ImportError:
    import json as json_lib

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
                yield f"data: {json_lib.dumps({'type': 'diagnosis', 'content': '从缓存加载数据中...'}, ensure_ascii=False)}\n\n"
                
                # 输出评语
                for char in cached_result.get("summary", ""):
                    yield f"data: {json_lib.dumps({'type': 'review', 'content': char}, ensure_ascii=False)}\n\n"
                
                # 输出结果
                yield f"data: {json_lib.dumps({'type': 'result', 'data': {
                    'overall_score': cached_result['overall_score'],
                    'summary': cached_result['summary'],
                    'deductions': cached_result['deductions']
                }}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
                return
            
            # 未命中缓存，正常执行
            diagnosis = coordinator.diagnostician.diagnose(
                code=request.code, 
                question=request.question
            )
            
            diag_msg = f"🔍 诊断完成：{diagnosis.get('summary', '')}"
            yield f"data: {json_lib.dumps({'type': 'diagnosis', 'content': diag_msg}, ensure_ascii=False)}\n\n"
            
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
                    yield f"data: {json_lib.dumps({'type': 'review', 'content': char}, ensure_ascii=False)}\n\n"
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
                        yield f"data: {json_lib.dumps({'type': 'review', 'content': content}, ensure_ascii=False)}\n\n"

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
                
                yield f"data: {json_lib.dumps({'type': 'result', 'data': score_data}, ensure_ascii=False)}\n\n"
            except Exception as e:
                print(f"❌ JSON解析失败: {e}")
                yield f"data: {json_lib.dumps({'type': 'result', 'data': {'overall_score': 0, 'summary': review_text, 'deductions': []}}, ensure_ascii=False)}\n\n"
            
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"data: {json_lib.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n"
    
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
                    yield f"data: {json_lib.dumps({'content': char}, ensure_ascii=False)}\n\n"
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
                        yield f"data: {json_lib.dumps({'content': content}, ensure_ascii=False)}\n\n"
            
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            yield f"data: {json_lib.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
    
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
