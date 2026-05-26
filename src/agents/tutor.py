"""
导师智能体：苏格拉底式追问 + 自适应难度
"""
from zhipuai import ZhipuAI

class Tutor:
    def __init__(self, api_key: str):
        print("🎓 导师智能体初始化...")
        self.client = ZhipuAI(api_key=api_key)
        self.base_prompt = """你是"码途智伴"，一位耐心的Python编程导师。
当前处于辅导模式，学生针对批改中的某个问题向你追问。

你必须遵守以下原则：
1. 先肯定学生提问，表达鼓励
2. 结合知识库从原理层解释问题根源
3. 给出一个简单的代码示例帮助理解
4. 最后提出一个引导性问题，启发学生自己解决（苏格拉底式提问）
5. 严禁直接给出完整答案

可参考知识：
{knowledge}"""
        print("✅ 导师智能体就绪")

    def generate_response(self, question: str, chat_history: list, 
                         diagnosis: dict, grading_report: str) -> str:
        """生成辅导回答，根据学生水平调整提示强度"""
        
        # 自适应：根据分数调整引导程度
        score = 0
        try:
            import json
            report_json = json.loads(grading_report)
            score = report_json.get('overall_score', 0)
        except:
            pass
        
        if score < 40:
            style = "请多给一些直接提示，但依然不要直接给出完整答案。"
        elif score < 70:
            style = "请适度引导，指出问题的方向。"
        else:
            style = "请用挑战性提问，鼓励探索最优解。"
        
        knowledge_text = ""
        for err in diagnosis['knowledge']['errors']:
            knowledge_text += f"【错误】{err['type']}: {err['explanation']}\n"
        for ex in diagnosis['knowledge']['examples']:
            knowledge_text += f"【范例】{ex['topic']}: {ex['explanation']}\n"
        
        system_prompt = self.base_prompt.format(knowledge=knowledge_text) + "\n" + style
        
        messages = [{"role": "system", "content": system_prompt}]
        # 加入批改报告上下文
        if grading_report and grading_report != "{}":
            messages.append({"role": "system", "content": f"批改报告: {grading_report}"})
        
        for msg in chat_history:
            messages.append({"role": msg["role"], "content": msg["content"]})
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