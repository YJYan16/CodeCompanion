def find_max(numbers):
    if not numbers:
        return None
    max_val = numbers[0]
    for num in numbers[1:]:
        if num > max_val:
            max_val = num
    # 忘记写 return max_val 了！

# 测试
result = find_max([3, 7, 2, 9, 1])
print(result)  # 输出 None，因为函数没有return