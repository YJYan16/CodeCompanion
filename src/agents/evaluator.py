"""
评价智能体：多维度评分 + 评语生成
"""
import json
from zhipuai import ZhipuAI

class Evaluator:
    def __init__(self, api_key: str):
        print("📝 评价智能体初始化...")
        self.client = ZhipuAI(api_key=api_key)
        self.system_prompt = """你是一位严谨的Python编程导师"码途智伴"。
你的任务是根据【诊断报告】【题目要求】【评分标准】批改学生代码，参考知识库资料。

严格按JSON输出：
{
    "overall_score": 整数(0-100),
    "summary": "总体评价",
    "deductions": [
        {
            "line": 行号,
            "type": "错误类型",
            "points_deducted": 扣分,
            "reason": "扣分原因",
            "suggestion": "改进建议"
        }
    ]
}"""
        print("✅ 评价智能体就绪")

    def evaluate(self, student_code: str, question: str, rubrics: str, 
                 diagnosis_report: dict) -> dict:
        """基于诊断结果进行评分"""
        # 准备知识文本
        knowledge_text = ""
        for err in diagnosis_report['knowledge']['errors']:
            knowledge_text += f"【已知错误】{err['type']}: {err['explanation']}\n修复:\n{err['fix_example']}\n\n"
        for ex in diagnosis_report['knowledge']['examples']:
            knowledge_text += f"【优秀范例】{ex['topic']}:\n{ex['code']}\n\n"
        # 在 evaluate 方法中，可以加入如下处理：
        weak_kps = diagnosis_report.get('weak_knowledge_points', [])
        if weak_kps:
            knowledge_text += f"\n【薄弱知识点】: {', '.join(weak_kps)}"

        user_message = f"""题目：{question}
评分标准：{rubrics}
诊断信息：{diagnosis_report['summary']}
知识库参考：{knowledge_text}
学生代码：
{student_code}

请批改，只输出JSON。"""
        
        try:
            response = self.client.chat.completions.create(
                model="glm-4-flash",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.1
            )
            result_text = response.choices[0].message.content
            if result_text.startswith("```json"):
                result_text = result_text[7:-3]
            elif result_text.startswith("```"):
                result_text = result_text[3:-3]
            return json.loads(result_text.strip())
        except Exception as e:
            return {"overall_score": 0, "summary": f"评分失败: {e}", "deductions": []}