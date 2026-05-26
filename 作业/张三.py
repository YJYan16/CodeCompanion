def find_max(numbers):
    max_num = 0
    for i in range(1, len(numbers)):
        if numbers[i] > max_num:
            max_num = numbers[i]
    return max_num

# 测试
print(find_max([1, 5, 3, 9, 2]))    # 正常，输出9
print(find_max([-5, -2, -9, -1]))   # 错误！全负数时返回0，而不是-1
print(find_max([]))                  # 错误！空列表会崩溃