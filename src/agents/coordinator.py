"""
协调器智能体：任务分发与结果融合
"""
import hashlib
from functools import lru_cache
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

    @lru_cache(maxsize=128)
    def _cached_grade(self, code: str, question: str, rubrics: str):
        diagnosis = self.diagnostician.diagnose(code, question)
        evaluation = self.evaluator.evaluate(code, question, rubrics, diagnosis)
        return diagnosis, evaluation

    def grade_workflow(self, student_code: str, question: str, rubrics: str) -> dict:
        diagnosis, evaluation = self._cached_grade(student_code, question, rubrics)
        
        # 3. 融合结果
        return {
            "diagnosis": diagnosis,
            "evaluation": evaluation,
            "final_report": self._format_report(evaluation)
        }

    def tutoring_workflow(self, question: str, chat_history: list,
                         student_code: str, grading_report: str) -> str:
        """追问工作流：诊断 → 导师回答"""
        # 只用知识库检索，不做完整评价
        diagnosis = self.diagnostician.diagnose(student_code, question)
        answer = self.tutor.generate_response(question, chat_history, 
                                             diagnosis, grading_report)
        return answer

    def _format_report(self, evaluation: dict) -> str:
        """格式化为Markdown报告"""
        score = evaluation.get('overall_score', 0)
        summary = evaluation.get('summary', '')
        formatted = f"## 📋 批改报告\n\n**总分: {score}/100**\n\n### 总体评价\n{summary}（由AI生成）\n\n### 扣分明细\n"
        for i, item in enumerate(evaluation.get('deductions', []), 1):
            formatted += f"""
**{i}. 第{item['line']}行 — {item['type']} (扣{item['points_deducted']}分)**
- 原因: {item['reason']}
- 建议: {item['suggestion']}（由AI生成）
"""
        return formatted