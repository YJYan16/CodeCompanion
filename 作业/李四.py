def find_max(numbers):
    if not numbers:
        return None
    max_val = numbers[0]
    for i in range(len(numbers)):
        if numbers[i] > numbers[i+1]:  # 当i=len(numbers)-1时，i+1越界
            max_val = numbers[i]
    return max_val

# 测试
print(find_max([3, 1, 4, 1, 5]))  # 运行时报错：IndexError