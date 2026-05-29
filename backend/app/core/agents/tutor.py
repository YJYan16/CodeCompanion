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
    
    def evaluate(self, code: str, question: str, rubrics: str, diagnosis: dict = None) -> dict:
        """评估代码并生成扣分详情"""
        return {
            "overall_score": 0,
            "deductions": [],
            "summary": ""
        }
    
    def generate_report(self, code: str, evaluation: dict, diagnosis: dict) -> str:
        """生成最终报告"""
        return "报告生成中..."
    
    def tutor(self, question: str, chat_history: list, student_code: str = "", report_json: str = "") -> str:
        """提供辅导回答"""
        return "这是一个辅导回答"