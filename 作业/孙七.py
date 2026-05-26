def find_max(numbers)    # 这里缺少冒号！
    max_num = 0
    for num in numbers:   # 这一行也缺少冒号
        if num > max_num  # 也缺少冒号
            max_num = num
    return max_num

# 测试
print(find_max([1, 5, 3]))