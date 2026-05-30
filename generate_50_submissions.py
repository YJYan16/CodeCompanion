"""
生成50份Python/Java混合测试作业包
题目：找最大值
包含5种类型代码，每种10份
"""
import zipfile
import os

# 5种代码模板（Python和Java混合）
TEMPLATES = [
    # 类型0：正确代码（Python）
    {
        "code": '''def find_max(numbers):
    if not numbers:
        return None
    max_val = numbers[0]
    for num in numbers[1:]:
        if num > max_val:
            max_val = num
    return max_val

# 测试
print(find_max([1, 5, 3, 9, 2]))
print(find_max([-5, -2, -9]))
print(find_max([]))
''',
        "lang": "py"
    },
    # 类型1：初始化错误（Python）
    {
        "code": '''def find_max(numbers):
    max_num = 0
    for i in range(1, len(numbers)):
        if numbers[i] > max_num:
            max_num = numbers[i]
    return max_num

# 测试
print(find_max([1, 5, 3, 9, 2]))
print(find_max([-5, -2, -9]))
''',
        "lang": "py"
    },
    # 类型2：索引越界（Python）
    {
        "code": '''def find_max(numbers):
    if not numbers:
        return None
    max_val = numbers[0]
    for i in range(len(numbers)):
        if numbers[i] > numbers[i+1]:
            max_val = numbers[i]
    return max_val

# 测试
print(find_max([3, 1, 4, 1, 5]))
''',
        "lang": "py"
    },
    # 类型3：忘记返回值（Python）
    {
        "code": '''def find_max(numbers):
    if not numbers:
        return None
    max_val = numbers[0]
    for num in numbers[1:]:
        if num > max_val:
            max_val = num
    # 忘记写return了

# 测试
result = find_max([3, 7, 2, 9, 1])
print(result)
''',
        "lang": "py"
    },
    # 类型4：正确代码（Java）
    {
        "code": '''public class Main {
    public static int findMax(int[] numbers) {
        if (numbers.length == 0) {
            return -1;
        }
        int maxVal = numbers[0];
        for (int i = 1; i < numbers.length; i++) {
            if (numbers[i] > maxVal) {
                maxVal = numbers[i];
            }
        }
        return maxVal;
    }

    public static void main(String[] args) {
        int[] test = {1, 5, 3, 9, 2};
        System.out.println(findMax(test));
    }
}
''',
        "lang": "java"
    },
]

# 学生名单（50个不重复姓名）
STUDENTS = [
    "张三", "李四", "王五", "赵六", "孙七",
    "周八", "吴九", "郑十", "钱一", "陈二",
    "刘三", "黄四", "林五", "杨六", "许七",
    "沈八", "韩九", "冯十", "邓一", "曹二",
    "彭三", "肖四", "田五", "董六", "袁七",
    "潘八", "于九", "蒋十", "蔡一", "余二",
    "杜三", "叶四", "程五", "苏六", "魏七",
    "吕八", "丁九", "任十", "卢一", "钟二",
    "廖三", "邱四", "夏五", "谭六", "严七",
    "陆八", "汪九", "范十", "方一", "石二"
][:50]

def main():
    output_path = os.path.join(os.path.dirname(__file__), "test50_max_value.zip")
    
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for i in range(50):
            code_type = i % len(TEMPLATES)
            template = TEMPLATES[code_type]
            filename = f"{STUDENTS[i]}.{template['lang']}"
            zf.writestr(filename, template['code'].strip())
    
    print(f"✅ 生成完成：{output_path}")
    print(f"   包含50个文件：")
    print(f"   - Python(.py)：40份（类型0-3各10份）")
    print(f"   - Java(.java)：10份（类型4，10份）")
    print(f"   5种错误类型：正确代码、初始化错误、索引越界、忘记返回值、Java正确代码")
    print(f"\n📦 可直接上传到教师端「批量批改」进行测试")

if __name__ == "__main__":
    main()