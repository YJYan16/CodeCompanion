# backend/app/api/endpoints.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from ..models.schemas import GradeRequest, GradeResponse, TutorRequest, TutorResponse, HealthResponse, Deduction
import sys
import os
import json
import httpx
from pydantic import BaseModel

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from src.agents.coordinator import Coordinator
from zhipuai import ZhipuAI

API_KEY = os.environ.get("ZHIPU_API_KEY", "")
coordinator = Coordinator(API_KEY)
client = ZhipuAI(api_key=API_KEY)

# 本地模型配置
LOCAL_MODEL_URL = "http://localhost:11434/api/generate"
USE_LOCAL_MODEL = os.environ.get("USE_LOCAL_MODEL", "false").lower() == "true"
LOCAL_MODEL_NAME = os.environ.get("LOCAL_MODEL_NAME", "qwen2.5:0.5b")

router = APIRouter()


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
    return HealthResponse(status="ok", version="2.0.0")


@router.get("/model/status")
async def model_status():
    return {
        "use_local": USE_LOCAL_MODEL,
        "local_model": LOCAL_MODEL_NAME,
        "cloud_model": "glm-4-flash",
        "mode": "本地模型" if USE_LOCAL_MODEL else "云端模型"
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
        result = coordinator.grade_workflow(
            request.code, 
            request.question, 
            request.rubrics
        )
        evaluation = result["evaluation"]
        diagnosis = result.get("diagnosis", {})
        return GradeResponse(
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/grade/stream")
async def grade_code_stream(request: GradeRequest):
    """流式批改代码"""
    async def generate():
        try:
            diagnosis = coordinator.diagnostician.diagnose(
                code=request.code, 
                question=request.question
            )
            
            diag_msg = f"🔍 诊断完成：{diagnosis.get('summary', '')}"
            yield f"data: {json.dumps({'type': 'diagnosis', 'content': diag_msg}, ensure_ascii=False)}\n\n"
            
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
                    yield f"data: {json.dumps({'type': 'review', 'content': char}, ensure_ascii=False)}\n\n"
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
                        yield f"data: {json.dumps({'type': 'review', 'content': content}, ensure_ascii=False)}\n\n"

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
                score_data = json.loads(result_text)
                score_data["summary"] = review_text
                yield f"data: {json.dumps({'type': 'result', 'data': score_data}, ensure_ascii=False)}\n\n"
            except Exception as e:
                print(f"❌ JSON解析失败: {e}")
                yield f"data: {json.dumps({'type': 'result', 'data': {'overall_score': 0, 'summary': review_text, 'deductions': []}}, ensure_ascii=False)}\n\n"
            
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n"
    
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
                    yield f"data: {json.dumps({'content': char}, ensure_ascii=False)}\n\n"
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
                        yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"
            
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
    
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
    
    return {"practices": practices}


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
            result = subprocess.run(["python", "-c", request.code], capture_output=True, text=True, timeout=request.timeout)
            return {"success": result.returncode == 0, "output": result.stdout, "error": result.stderr}
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
    """根据薄弱知识点生成个性化学习路径"""
    weak_points = request.weak_points
    language = request.language
    
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
    
    return {
        "weak_points": weak_points,
        "path": all_steps,
        "total_steps": len(all_steps)
    }