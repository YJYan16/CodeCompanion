import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from zhipuai import ZhipuAI
from config.settings import get_settings

settings = get_settings()
client = ZhipuAI(api_key=settings.zhipu_api_key)

# ================= 提示词工程设计 =================
SYSTEM_PROMPT = """你是一位严谨又耐心的Python编程导师“码途智伴”。
你的任务是根据【题目要求】和【评分标准】批改学生的Python代码。
你必须严格按照JSON格式输出结果，不要有任何多余的文字。
JSON格式如下：
{
    "overall_score": 整数(0-100),
    "summary": "总体评价的字符串",
    "deductions": [
        {
            "line": 出问题的行号(整数),
            "type": "错误类型(string)",
            "points_deducted": 扣除分数(整数),
            "reason": "扣分原因(string)",
            "suggestion": "改进建议(string)"
        }
    ]
}"""

# 模拟的题目和要求
QUESTION = "编写一个函数 `find_max(numbers)`，接收一个整数列表，返回其中的最大值。要求不使用内置的 `max()` 函数。"
RUBRICS = "1. 逻辑正确 (60分): 能正确找到最大值。\n2. 代码规范 (20分): 变量名有意义，有适当注释。\n3. 边界处理 (20分): 能处理空列表和只有一个元素的列表。"

# 模拟的学生代码（这里故意放了一份有问题的代码）
STUDENT_CODE = """
def find_max(numbers):
    max_num = 0
    for i in range(1, len(numbers)):
        if numbers[i] > max_num:
            max_num = numbers[i]
    return max_num

print(find_max([-5, -2, -9]))
"""

# ================= 核心功能函数 =================
def grade_code(question, rubrics, student_code):
    print("⏳ 智谱AI导师正在批改中...")
    
    # 组装用户消息，将所有信息注入提示词
    user_message = f"""题目：
{question}

评分标准：
{rubrics}

学生代码如下：
{student_code}

请开始批改。记住，只输出一个完整的JSON对象。"""

    try:
        # 调用大模型
        response = client.chat.completions.create(
            model="glm-4-flash",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=0.1 # 降低随机性，让输出更稳定
        )
        
        result_text = response.choices[0].message.content
        
        # 处理可能包裹在Markdown代码块里的JSON
        if result_text.startswith("```json"):
            result_text = result_text[7:-3]
        elif result_text.startswith("```"):
            result_text = result_text[3:-3]
            
        report = json.loads(result_text.strip())
        return report

    except json.JSONDecodeError:
        print("❌ 解析JSON失败，大模型返回的内容为：")
        print(result_text)
        return None
    except Exception as e:
        print(f"❌ 调用或处理失败: {e}")
        return None

# ================= 运行和展示结果 =================
if __name__ == "__main__":
    report = grade_code(QUESTION, RUBRICS, STUDENT_CODE)
    
    if report:
        print("\n" + "="*40)
        print("📋 批改报告")
        print("="*40)
        print(f"总分: {report['overall_score']}/100")
        print(f"总结: {report['summary']}")
        print("\n扣分明细:")
        for item in report['deductions']:
            print(f"- 第{item['line']}行: {item['type']} (扣{item['points_deducted']}分)")
            print(f"  原因: {item['reason']}")
            print(f"  建议: {item['suggestion']}")
        print("="*40)
    else:
        print("批改失败，请检查代码和网络。")