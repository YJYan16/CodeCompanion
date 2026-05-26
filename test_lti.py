"""测试 LTI 平台对接接口"""
import requests
import json

BASE_URL = "http://127.0.0.1:8001"

# 测试数据
test_data = {
    "user_id": "student_001",
    "assignment_id": "q1",
    "code": """def find_max(numbers):
    if not numbers:
        return None
    max_val = numbers[0]
    for num in numbers[1:]:
        if num > max_val:
            max_val = num
    return max_val""",
    "language": "python"
}

# 发送请求
response = requests.post(f"{BASE_URL}/lti/submit", json=test_data)
result = response.json()

print("=" * 50)
print("📋 LTI 对接测试结果")
print("=" * 50)
print(f"学生ID: {result.get('user_id')}")
print(f"作业ID: {result.get('assignment_id')}")
print(f"得分: {result.get('score')}/100")
print(f"提交时间: {result.get('submitted_at')}")
print(f"\n反馈内容:\n{result.get('feedback')[:200]}...")
print("=" * 50)