# src/agents/coordinator.py
from .diagnostician import Diagnostician
from .evaluator import Evaluator
from .tutor import Tutor


class Coordinator:
    def __init__(self, api_key: str):
        print("🎯 协调器智能体初始化...")
        self.diagnostician = Diagnostician()
        self.evaluator = Evaluator(api_key)
        self.tutor = Tutor(api_key)
        print("✅ 多智能体协作系统就绪")

    def grade_workflow(self, student_code: str, question: str, rubrics: str, language: str = "python") -> dict:
        diagnosis = self.diagnostician.diagnose(student_code, question, language)
        evaluation = self.evaluator.evaluate(student_code, question, rubrics, diagnosis, language)
        return {
            "diagnosis": diagnosis,
            "evaluation": evaluation,
            "final_report": self._format_report(evaluation)
        }

    def tutoring_workflow(self, question: str, chat_history: list, student_code: str, grading_report: str) -> str:
        diagnosis = self.diagnostician.diagnose(student_code, question)
        answer = self.tutor.generate_response(question, chat_history, diagnosis, grading_report)
        return answer

    def _format_report(self, evaluation: dict) -> str:
        score = evaluation.get('overall_score', 0)
        summary = evaluation.get('summary', '')
        formatted = f"## 📋 批改报告\n\n**总分: {score}/100（由AI生成）**\n\n### 总体评价\n{summary}（由AI生成）\n\n### 扣分明细\n"
        for i, item in enumerate(evaluation.get('deductions', []), 1):
            formatted += f"""
**{i}. 第{item['line']}行 — {item['type']} (扣{item['points_deducted']}分)**
- 原因: {item['reason']}
- 建议: {item['suggestion']}（由AI生成）
"""
        return formatted