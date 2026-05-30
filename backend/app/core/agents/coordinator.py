"""
协调智能体 - 编排各个智能体的工作流程
"""
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(os.path.dirname(current_dir))

if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
if os.path.dirname(backend_dir) not in sys.path:
    sys.path.insert(0, os.path.dirname(backend_dir))

from config.settings import get_settings
from app.core.agents.diagnostician import Diagnostician
from app.core.agents.tutor import Tutor

settings = get_settings()


class Coordinator:
    def __init__(self, api_key=None):
        self.diagnostician = Diagnostician()
        self.tutor = Tutor(api_key or settings.zhipu_api_key)
    
    def grade_workflow(self, code: str, question: str, rubrics: str, language: str = "python") -> dict:
        """执行完整的批改工作流"""
        diagnosis = self.diagnostician.diagnose(code, question)
        
        evaluation = self.tutor.evaluate(
            code=code,
            question=question,
            rubrics=rubrics,
            diagnosis=diagnosis,
            language=language
        )
        
        final_report = self.tutor.generate_report(
            code=code,
            evaluation=evaluation,
            diagnosis=diagnosis
        )
        
        return {
            "evaluation": evaluation,
            "diagnosis": diagnosis,
            "final_report": final_report
        }
    
    def tutoring_workflow(self, question: str, chat_history: list, student_code: str = "", report_json: str = "") -> str:
        """执行辅导工作流"""
        return self.tutor.tutor(question, chat_history, student_code, report_json)