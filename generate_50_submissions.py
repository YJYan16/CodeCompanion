"""
生成50份测试作业包 test50.zip
包含5种类型代码，每种10份
"""
import zipfile
import os

# 5种代码模板
TEMPLATES = [
    # 类型0：正确代码
    '''
def find_max(numbers):
    if not numbers:
        return None
    max_val = numbers[0]
    for num in numbers[1:]:
        if num > max_val:
            max_val = num
    return max_val
''',
    # 类型1：初始化错误（max_num=0 导致全负数返回0）
    '''
def find_max(numbers):
    max_num = 0
    for i in range(1, len(numbers)):
        if numbers[i] > max_num:
            max_num = numbers[i]
    return max_num
''',
    # 类型2：索引越界（numbers[i+1]）
    '''
def find_max(numbers):
    if not numbers:
        return None
    max_val = numbers[0]
    for i in range(len(numbers)):
        if numbers[i] > numbers[i+1]:
            max_val = numbers[i]
    return max_val
''',
    # 类型3：忘记return
    '''
def find_max(numbers):
    if not numbers:
        return None
    max_val = numbers[0]
    for num in numbers[1:]:
        if num > max_val:
            max_val = num
    # 没有return
''',
    # 类型4：语法错误（缺少冒号）
    '''
def find_max(numbers)
    max_num = 0
    for num in numbers:
        if num > max_num:
            max_num = num
    return max_num
'''
]

# 生成50个不重复的学生姓名
names = [
    "张三", "李四", "王五", "赵六", "孙七", "周八", "吴九", "郑十",
    "钱一", "陈二", "刘三", "黄四", "林五", "杨六", "许七", "沈八",
    "韩九", "冯十", "邓一", "曹二", "彭三", "肖四", "田五", "董六",
    "袁七", "潘八", "于九", "蒋十", "蔡一", "余二",
    "学生A", "学生B", "学生C", "学生D", "学生E", "学生F",
    "学生G", "学生H", "学生I", "学生J", "学生K", "学生L",
    "学生M", "学生N", "学生O", "学生P", "学生Q", "学生R",
    "学生S", "学生T"
][:50]  # 确保恰好50个

# 生成zip
output_path = os.path.join(os.path.dirname(__file__), "test50.zip")
with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for i in range(50):
        code_type = i % 5  # 5种类型循环
        filename = f"{names[i]}.py"
        zf.writestr(filename, TEMPLATES[code_type].strip())

print(f"✅ 生成完成：{output_path}")
print(f"   包含50个.py文件，5种错误类型各10份")