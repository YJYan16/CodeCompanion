# backend/app/core/init_db.py
from sqlalchemy.orm import Session
from app.core.database import engine, Base
from app.models.database_models import User, Class, Question, Grade
from datetime import datetime

# 初始化数据库表
def init_db():
    Base.metadata.create_all(bind=engine)

# 添加初始数据
def add_initial_data(db: Session):
    # 检查是否已有初始数据
    if db.query(User).first():
        return
    
    # 添加管理员用户
    admin = User(
        username="admin",
        password="admin",
        name="管理员",
        role="admin",
        class_name="管理员"
    )
    db.add(admin)
    
    # 添加学生用户
    student = User(
        username="student",
        password="123456",
        name="学生小明",
        role="student",
        class_name="高一(1)班"
    )
    db.add(student)
    
    # 添加班级
    class1 = Class(name="高一(1)班")
    class2 = Class(name="高一(2)班")
    db.add(class1)
    db.add(class2)
    
    # 添加题目
    questions = [
        Question(
            question_id="q1",
            title="找最大值",
            description="编写一个函数，在不使用内置函数的情况下，找出列表中的最大值。",
            python_template="""# ============================================
# 题目：找最大值
# ============================================
# 题目描述：编写一个函数，在不使用内置函数的情况下，找出列表中的最大值。
# ============================================

def find_max(arr):
    \"\"\"
    找出列表中的最大值
    
    参数：
        arr: 一个包含数字的列表
        
    返回值：
        列表中的最大值
    \"\"\"
    # ============ 请在此处编写代码 ============
    result = None
    # ...
    return result

# 测试代码
if __name__ == "__main__":
    test_list = [3, 1, 4, 1, 5, 9, 2, 6]
    print(find_max(test_list))  # 应输出 9""",
            java_template="""// ============================================
// 题目：找最大值
// ============================================
// 题目描述：编写一个函数，在不使用内置函数的情况下，找出数组中的最大值。
// ============================================

public class Main {
    public static void main(String[] args) {
        int[] testArray = {3, 1, 4, 1, 5, 9, 2, 6};
        System.out.println(findMax(testArray));  // 应输出 9
    }
    
    public static int findMax(int[] arr) {
        // ============ 请在此处编写代码 ============
        int result = 0;
        // ...
        return result;
    }
}""",
            rubrics="1. 正确遍历列表：20分\n2. 正确比较元素：20分\n3. 返回正确结果：30分\n4. 处理边界情况：15分\n5. 代码可读性：15分",
            difficulty="简单"
        ),
        Question(
            question_id="q2",
            title="列表去重",
            description="编写一个函数，对列表进行去重，保持元素的相对顺序不变。",
            python_template="""# ============================================
# 题目：列表去重
# ============================================
# 题目描述：编写一个函数，对列表进行去重，保持元素的相对顺序不变。
# ============================================

def remove_duplicates(arr):
    \"\"\"
    列表去重，保持顺序
    
    参数：
        arr: 一个列表
        
    返回值：
        去重后的列表
    \"\"\"
    # ============ 请在此处编写代码 ============
    result = []
    # ...
    return result

# 测试代码
if __name__ == "__main__":
    test_list = [1, 2, 2, 3, 3, 3, 4]
    print(remove_duplicates(test_list))  # 应输出 [1, 2, 3, 4]""",
            java_template="""// ============================================
// 题目：数组去重
// ============================================
// 题目描述：编写一个函数，对数组进行去重，保持元素的相对顺序不变。
// ============================================

import java.util.ArrayList;
import java.util.List;

public class Main {
    public static void main(String[] args) {
        int[] testArray = {1, 2, 2, 3, 3, 3, 4};
        int[] result = removeDuplicates(testArray);
        for (int num : result) {
            System.out.print(num + " ");  // 应输出 1 2 3 4
        }
    }
    
    public static int[] removeDuplicates(int[] arr) {
        // ============ 请在此处编写代码 ============
        List<Integer> result = new ArrayList<>();
        // ...
        return result.stream().mapToInt(Integer::intValue).toArray();
    }
}""",
            rubrics="1. 正确遍历列表：20分\n2. 正确判断重复：25分\n3. 保持顺序：25分\n4. 返回正确结果：20分\n5. 代码效率：10分",
            difficulty="简单"
        ),
        Question(
            question_id="q3",
            title="斐波那契数列",
            description="编写一个函数，计算斐波那契数列的第n项。",
            python_template="""# ============================================
# 题目：斐波那契数列
# ============================================
# 题目描述：编写一个函数，计算斐波那契数列的第n项。
# ============================================

def fibonacci(n):
    \"\"\"
    计算斐波那契数列第n项
    
    参数：
        n: 正整数
        
    返回值：
        斐波那契数列第n项的值
    \"\"\"
    # ============ 请在此处编写代码 ============
    result = 0
    # ...
    return result

# 测试代码
if __name__ == "__main__":
    print(fibonacci(10))  # 应输出 55""",
            java_template="""// ============================================
// 题目：斐波那契数列
// ============================================
// 题目描述：编写一个函数，计算斐波那契数列的第n项。
// ============================================

public class Main {
    public static void main(String[] args) {
        System.out.println(fibonacci(10));  // 应输出 55
    }
    
    public static int fibonacci(int n) {
        // ============ 请在此处编写代码 ============
        int result = 0;
        // ...
        return result;
    }
}""",
            rubrics="1. 正确处理边界：20分\n2. 正确递推计算：30分\n3. 返回正确结果：30分\n4. 时间复杂度：10分\n5. 代码可读性：10分",
            difficulty="中等"
        ),
        Question(
            question_id="q4",
            title="字符串反转",
            description="编写一个函数，接收一个字符串，返回反转后的字符串。",
            python_template="""# ============================================
# 题目：字符串反转
# ============================================
# 题目描述：编写一个函数，接收一个字符串，返回反转后的字符串。
# ============================================

def reverse_string(s):
    \"\"\"
    字符串反转
    
    参数：
        s: 输入字符串
        
    返回值：
        反转后的字符串
    \"\"\"
    # ============ 请在此处编写代码 ============
    result = ""
    # ...
    return result

# 测试代码
if __name__ == "__main__":
    print(reverse_string("hello"))  # 应输出 "olleh" """,
            java_template="""// ============================================
// 题目：字符串反转
// ============================================
// 题目描述：编写一个函数，接收一个字符串，返回反转后的字符串。
// ============================================

public class Main {
    public static void main(String[] args) {
        System.out.println(reverseString("hello"));  // 应输出 "olleh"
    }
    
    public static String reverseString(String s) {
        // ============ 请在此处编写代码 ============
        String result = "";
        // ...
        return result;
    }
}""",
            rubrics="1. 正确遍历字符串：20分\n2. 正确反转字符：30分\n3. 返回正确结果：30分\n4. 处理空字符串：10分\n5. 代码简洁：10分",
            difficulty="简单"
        ),
        Question(
            question_id="q5",
            title="质数判断",
            description="编写一个函数，判断一个数是否为质数。",
            python_template="""# ============================================
# 题目：质数判断
# ============================================
# 题目描述：编写一个函数，判断一个数是否为质数。
# ============================================

def is_prime(n):
    \"\"\"
    判断一个数是否为质数
    
    参数：
        n: 正整数
        
    返回值：
        True 如果是质数，False 否则
    \"\"\"
    # ============ 请在此处编写代码 ============
    result = False
    # ...
    return result

# 测试代码
if __name__ == "__main__":
    print(is_prime(17))  # 应输出 True
    print(is_prime(15))  # 应输出 False""",
            java_template="""// ============================================
// 题目：质数判断
// ============================================
// 题目描述：编写一个函数，判断一个数是否为质数。
// ============================================

public class Main {
    public static void main(String[] args) {
        System.out.println(isPrime(17));  // 应输出 true
        System.out.println(isPrime(15));  // 应输出 false
    }
    
    public static boolean isPrime(int n) {
        // ============ 请在此处编写代码 ============
        boolean result = false;
        // ...
        return result;
    }
}""",
            rubrics="1. 正确处理边界：20分\n2. 正确判断质数：40分\n3. 返回正确结果：20分\n4. 算法效率：10分\n5. 代码可读性：10分",
            difficulty="中等"
        ),
        Question(
            question_id="q6",
            title="冒泡排序",
            description="使用冒泡排序算法对列表/数组进行升序排序。",
            python_template="""# ============================================
# 题目：冒泡排序
# ============================================
# 题目描述：使用冒泡排序算法对列表进行升序排序。
# ============================================

def bubble_sort(arr):
    \"\"\"
    冒泡排序
    
    参数：
        arr: 待排序的列表
        
    返回值：
        排序后的列表
    \"\"\"
    # ============ 请在此处编写代码 ============
    result = arr.copy()
    # ...
    return result

# 测试代码
if __name__ == "__main__":
    test_list = [64, 34, 25, 12, 22, 11, 90]
    print(bubble_sort(test_list))  # 应输出 [11, 12, 22, 25, 34, 64, 90]""",
            java_template="""// ============================================
// 题目：冒泡排序
// ============================================
// 题目描述：使用冒泡排序算法对数组进行升序排序。
// ============================================

import java.util.Arrays;

public class Main {
    public static void main(String[] args) {
        int[] testArray = {64, 34, 25, 12, 22, 11, 90};
        bubbleSort(testArray);
        System.out.println(Arrays.toString(testArray));  // 应输出 [11, 12, 22, 25, 34, 64, 90]
    }
    
    public static void bubbleSort(int[] arr) {
        // ============ 请在此处编写代码 ============
        // ...
    }
}""",
            rubrics="1. 正确实现冒泡排序：40分\n2. 正确交换元素：20分\n3. 正确排序结果：20分\n4. 优化（提前终止）：10分\n5. 代码可读性：10分",
            difficulty="中等"
        ),
        Question(
            question_id="q7",
            title="二分查找",
            description="使用二分查找算法在有序列表/数组中查找目标值。",
            python_template="""# ============================================
# 题目：二分查找
# ============================================
# 题目描述：使用二分查找算法在有序列表中查找目标值。
# ============================================

def binary_search(arr, target):
    \"\"\"
    二分查找
    
    参数：
        arr: 有序列表
        target: 目标值
        
    返回值：
        目标值的索引，如果未找到返回-1
    \"\"\"
    # ============ 请在此处编写代码 ============
    result = -1
    # ...
    return result

# 测试代码
if __name__ == "__main__":
    test_list = [1, 3, 5, 7, 9, 11, 13]
    print(binary_search(test_list, 7))   # 应输出 3
    print(binary_search(test_list, 4))   # 应输出 -1""",
            java_template="""// ============================================
// 题目：二分查找
// ============================================
// 题目描述：使用二分查找算法在有序数组中查找目标值。
// ============================================

public class Main {
    public static void main(String[] args) {
        int[] testArray = {1, 3, 5, 7, 9, 11, 13};
        System.out.println(binarySearch(testArray, 7));   // 应输出 3
        System.out.println(binarySearch(testArray, 4));   // 应输出 -1
    }
    
    public static int binarySearch(int[] arr, int target) {
        // ============ 请在此处编写代码 ============
        int result = -1;
        // ...
        return result;
    }
}""",
            rubrics="1. 正确初始化指针：20分\n2. 正确二分查找：40分\n3. 返回正确索引：20分\n4. 处理边界条件：10分\n5. 代码可读性：10分",
            difficulty="中等"
        )
    ]
    
    for q in questions:
        db.add(q)
    
    db.commit()
    print("[OK] 初始数据添加完成")

# 主函数
if __name__ == "__main__":
    init_db()
    from app.core.database import SessionLocal
    db = SessionLocal()
    add_initial_data(db)
    db.close()
    print("[OK] 数据库初始化完成")
