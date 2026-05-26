import json
import os
from zhipuai import ZhipuAI
from sentence_transformers import SentenceTransformer
import chromadb

# ================= 配置区域 =================
client = ZhipuAI(api_key="f7b6d5fa6d2c4664b4bb00cf0b90a98b.3E214QD3EwjM9f8y")

# 知识库路径（和构建脚本保持一致）
KB_PATH = os.path.join(os.path.dirname(__file__), "kb_data")

# ================= 初始化知识库连接 =================
print("⏳ 正在连接知识库...")
embedding_model = SentenceTransformer('BAAI/bge-large-zh-v1.5')
chroma_client = chromadb.PersistentClient(path=KB_PATH)
error_collection = chroma_client.get_collection("python_errors")
example_collection = chroma_client.get_collection("python_examples")
print("✅ 知识库连接成功")

# ================= 提示词模板 =================
SYSTEM_PROMPT = """你是一位严谨又耐心的Python编程导师"码途智伴"。
你的任务是根据【题目要求】和【评分标准】批改学生的Python代码。

批改时，你会收到一份【相关知识库资料】，包含类似错误的案例和修复方案。请认真参考这些资料，使你的批注更加精准和专业。

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
            "suggestion": "改进建议(string)",
            "reference": "参考了知识库中的哪条知识(string)"
        }
    ]
}"""

# ================= 知识库检索函数 =================
def search_knowledge(query_text, n_results=3):
    """
    在知识库中搜索与查询最相关的错误知识和范例
    """
    # 搜索错误库
    error_results = error_collection.query(
        query_texts=[query_text],
        n_results=n_results
    )
    
    # 搜索范例库
    example_results = example_collection.query(
        query_texts=[query_text],
        n_results=2
    )
    
    # 整理检索结果
    knowledge_texts = []
    
    for i in range(len(error_results['ids'][0])):
        meta = error_results['metadatas'][0][i]
        knowledge_texts.append(
            f"【相关知识{i+1}】错误类型: {meta['error_type']}\n"
            f"解释: {meta['explanation']}\n"
            f"修复示例:\n{meta['fix_example']}"
        )
    
    for i in range(len(example_results['ids'][0])):
        meta = example_results['metadatas'][0][i]
        knowledge_texts.append(
            f"【优秀范例{i+1}】{meta['topic']}\n"
            f"代码:\n{meta['code']}\n"
            f"说明: {meta['explanation']}"
        )
    
    return "\n\n".join(knowledge_texts) if knowledge_texts else "未找到相关知识"

# ================= 题目和评分标准 =================
QUESTION = "编写一个函数 `find_max(numbers)`，接收一个整数列表，返回其中的最大值。要求不使用内置的 `max()` 函数。"
RUBRICS = """
1. 逻辑正确 (60分): 能正确找到最大值，包括处理全负数列表。
2. 代码规范 (20分): 变量名有意义，有适当注释，函数有文档字符串。
3. 边界处理 (20分): 能处理空列表（返回None）和只有一个元素的列表。
"""

# 模拟多份学生作业
STUDENT_WORKS = [
    {
        "name": "学生A（初始化错误）",
        "code": """
def find_max(numbers):
    max_num = 0
    for i in range(1, len(numbers)):
        if numbers[i] > max_num:
            max_num = numbers[i]
    return max_num
"""
    },
    {
        "name": "学生B（优秀代码）",
        "code": """
def find_max(numbers):
    '''返回列表中的最大值'''
    if not numbers:
        return None
    max_val = numbers[0]
    for num in numbers[1:]:
        if num > max_val:
            max_val = num
    return max_val
"""
    },
]

# ================= 核心批改函数（带知识库增强） =================
def grade_code_with_rag(question, rubrics, student_code, student_name=""):
    print(f"\n⏳ 正在批改 {student_name} 的作业...")
    
    # 第一步：先用代码本身去知识库搜索相关知识
    print("  📚 正在检索知识库...")
    knowledge = search_knowledge(student_code)
    
    # 第二步：组装完整提示词
    user_message = f"""题目：
{question}

评分标准：
{rubrics}

【知识库参考资料】（请认真参考这些资料来增强你的批注）：
{knowledge}

学生代码如下：
{student_code}

请开始批改。记住，只输出一个完整的JSON对象。"""
    
    try:
        # 第三步：调用大模型
        response = client.chat.completions.create(
            model="glm-4-flash",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=0.1
        )
        
        result_text = response.choices[0].message.content
        
        # 处理可能的Markdown代码块包裹
        if result_text.startswith("```json"):
            result_text = result_text[7:-3]
        elif result_text.startswith("```"):
            result_text = result_text[3:-3]
        
        report = json.loads(result_text.strip())
        return report, knowledge
        
    except json.JSONDecodeError:
        print("  ❌ 解析JSON失败，大模型返回的内容为：")
        print(result_text)
        return None, knowledge
    except Exception as e:
        print(f"  ❌ 调用失败: {e}")
        return None, knowledge

# ================= 主程序 =================
if __name__ == "__main__":
    print("="*60)
    print("🚀 码途智伴 - 知识库增强批改系统")
    print("="*60)
    
    for work in STUDENT_WORKS:
        report, knowledge = grade_code_with_rag(QUESTION, RUBRICS, work["code"], work["name"])
        
        if report:
            print("\n" + "="*50)
            print(f"📋 {work['name']} - 批改报告")
            print("="*50)
            print(f"总分: {report['overall_score']}/100")
            print(f"总评: {report['summary']}")
            print("\n📌 扣分明细:")
            for item in report['deductions']:
                print(f"  • 第{item['line']}行: 【{item['type']}】(扣{item['points_deducted']}分)")
                print(f"    原因: {item['reason']}")
                print(f"    建议: {item['suggestion']}")
                if item.get('reference') and item['reference'] != "无":
                    print(f"    📖 参考知识: {item['reference'][:80]}...")
            print("="*50)
        else:
            print(f"\n❌ {work['name']} 的作业批改失败")
    
    print("\n" + "="*60)
    print("✅ 所有作业批改完成！")
    print("📝 你可以修改 STUDENT_WORKS 中的代码来测试不同情况")
    print("="*60)