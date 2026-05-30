"""
辅导智能体 - 提供个性化的编程指导
"""
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(os.path.dirname(current_dir))

if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from config.settings import get_settings
from zhipuai import ZhipuAI

settings = get_settings()


class Tutor:
    def __init__(self, api_key=None):
        self.client = ZhipuAI(api_key=api_key or settings.zhipu_api_key)
    
    def evaluate(self, code: str, question: str, rubrics: str, diagnosis: dict = None, language: str = "python") -> dict:
        """评估代码并生成扣分详情"""
        
        lang_hint = ""
        if language == "java":
            lang_hint = "请注意这是 Java 代码。"

        prompt = f"""{lang_hint}
你是一位严谨的编程导师。请根据以下信息批改学生代码。

题目：{question}
评分标准：{rubrics}
学生代码：
{code}

请直接输出JSON（不要用markdown代码块包裹）：
{{
    "overall_score": 整数(0-100),
    "summary": "总体评价（包括代码优点、存在的问题、改进建议）",
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

        try:
            response = self.client.chat.completions.create(
                model="glm-4-flash",
                messages=[
                    {"role": "system", "content": "你是编程评分助手，请根据评分标准输出JSON。只输出JSON，不要其他内容。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            result_text = response.choices[0].message.content
            
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            elif result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            result_text = result_text.strip()
            
            import json
            return json.loads(result_text)
        except Exception as e:
            print(f"评分失败: {e}")
            return {
                "overall_score": 50,
                "summary": f"评分出错: {str(e)}",
                "deductions": []
            }
    
    def generate_report(self, code: str, evaluation: dict, diagnosis: dict) -> str:
        """生成最终报告"""
        score = evaluation.get("overall_score", 0)
        summary = evaluation.get("summary", "")
        deductions = evaluation.get("deductions", [])
        
        report = f"## 📋 批改报告\n\n**总分: {score}/100（由AI生成）**\n\n"
        report += f"### 总体评价\n{summary}\n\n"
        
        if deductions:
            report += "### 扣分明细\n"
            for i, d in enumerate(deductions, 1):
                report += f"**{i}. 第{d.get('line', '?')}行 — {d.get('type', '未知')} (扣{d.get('points_deducted', 0)}分)**\n"
                report += f"- 原因: {d.get('reason', '')}\n"
                report += f"- 建议: {d.get('suggestion', '')}\n\n"
        
        return report
    
    def tutor(self, question: str, chat_history: list, student_code: str = "", report_json: str = "") -> str:
        """提供辅导回答"""
        messages = [{"role": "system", "content": "你是码途智伴，一位耐心的编程导师。回答要简洁、鼓励性。"}]
        
        for msg in chat_history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        if report_json and report_json != "{}":
            messages.append({"role": "system", "content": f"批改报告: {report_json}"})
        
        if student_code:
            messages.append({"role": "system", "content": f"学生当前代码:\n```\n{student_code}\n```"})
        
        messages.append({"role": "user", "content": question})
        
        try:
            response = self.client.chat.completions.create(
                model="glm-4-flash",
                messages=messages,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"抱歉，暂时无法回答。错误: {str(e)}"