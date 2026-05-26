def find_max(numbers):
    """返回整数列表中的最大值"""
    if not numbers:              # 处理空列表
        return None
    max_val = numbers[0]         # 初始化为第一个元素
    for num in numbers[1:]:      # 从第二个元素开始遍历
        if num > max_val:
            max_val = num
    return max_val

# 测试
print(find_max([1, 5, 3, 9, 2]))   # 输出 9
print(find_max([-5, -2, -9, -1]))  # 输出 -1
print(find_max([42]))               # 输出 42
print(find_max([]))                 # 输出 None