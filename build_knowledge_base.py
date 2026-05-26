import chromadb
from sentence_transformers import SentenceTransformer
import os

KB_PATH = os.path.join(os.path.dirname(__file__), "kb_data")

print("⏳ 正在加载嵌入模型...")
embedding_model = SentenceTransformer('BAAI/bge-large-zh-v1.5')
print("✅ 模型加载完成")

client = chromadb.PersistentClient(path=KB_PATH)

try:
    client.delete_collection("python_errors")
    client.delete_collection("python_examples")
except:
    pass

error_collection = client.create_collection("python_errors")
example_collection = client.create_collection("python_examples")

errors = [
    {"id": "err_001", "type": "初始化错误", "pattern": "max_num=0 全负数返回0", "explanation": "初始化为0导致全负数列表返回错误", "fix_example": "max_val = numbers[0]"},
    {"id": "err_002", "type": "索引越界", "pattern": "numbers[i+1] 导致 IndexError", "explanation": "循环到最后一个元素时访问 i+1 越界", "fix_example": "使用 range(len(numbers)-1) 或 for...in"},
    {"id": "err_003", "type": "忘记返回值", "pattern": "函数末尾缺少 return", "explanation": "没有 return 语句，函数返回 None", "fix_example": "在函数末尾添加 return max_val"},
    {"id": "err_004", "type": "缩进错误", "pattern": "if/for/def 后未缩进", "explanation": "代码块必须缩进", "fix_example": "使用4个空格缩进"},
    {"id": "err_005", "type": "空列表未处理", "pattern": "空列表访问索引", "explanation": "未检查空列表导致 IndexError", "fix_example": "if not numbers: return None"}
]

for err in errors:
    error_collection.add(
        documents=[f"{err['type']}: {err['explanation']}"],
        metadatas=[err],
        ids=[err["id"]]
    )

examples = [
    {"id": "ex_001", "topic": "找最大值（遍历法）", "code": "def find_max(numbers):\n    if not numbers: return None\n    max_val = numbers[0]\n    for num in numbers[1:]:\n        if num > max_val: max_val = num\n    return max_val", "explanation": "正确解法"}
]
for ex in examples:
    example_collection.add(
        documents=[f"{ex['topic']}: {ex['explanation']}"],
        metadatas=[ex],
        ids=[ex["id"]]
    )

print(f"✅ 知识库构建完成！\n📁 保存路径: {KB_PATH}")