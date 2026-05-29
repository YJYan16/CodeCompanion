import { reactive } from 'vue'

// 从后端API获取题目数据
const fetchQuestions = async () => {
  try {
    const response = await fetch('http://localhost:8001/api/questions')
    const result = await response.json()
    if (result.questions) {
      const questionMap = {}
      result.questions.forEach(q => {
        questionMap[q.id] = {
          ...q,
          languages: ['python', 'java'],
          python: {
            description: q.description,
            rubrics: q.rubrics,
            template: q.python
          },
          java: {
            description: q.description,
            rubrics: q.rubrics,
            template: q.java
          }
        }
      })
      return questionMap
    }
  } catch (error) {
    console.error('获取题目数据失败:', error)
  }
  return null
}

// 默认题目数据（首次初始化时使用）
const defaultQuestions = [
  {
    id: 'q1',
    title: '找最大值',
    description: '编写函数，接收整数列表/数组，返回最大值。不能使用内置排序/max函数。',
    languages: ['python', 'java'],
    python: {
      description: '编写函数 find_max(numbers)，接收整数列表，返回最大值。',
      rubrics: '1. 逻辑正确(60分)\n2. 代码规范(20分)\n3. 边界处理(20分)',
      template: `# 题目：找最大值
def find_max(numbers):
    pass`,
      practices: [
        { 
          description: "基础练习：遍历列表找最大值", 
          difficulty: 1, 
          questionId: "q1", 
          template: `def find_max(numbers):
    max_val = numbers[0]
    for num in numbers:
        if num > max_val:
            max_val = num
    return max_val` 
        }
      ]
    },
    java: {
      description: '编写 findMax 方法，接收整数数组，返回最大值。',
      rubrics: '1. 逻辑正确(60分)\n2. 代码规范(20分)\n3. 边界处理(20分)',
      template: `// 找最大值 (Java)
public class Main {
    public static int findMax(int[] numbers) {
        return 0;
    }
}`,
      practices: [
        { 
          description: "基础练习：遍历数组找最大值", 
          difficulty: 1, 
          questionId: "q1", 
          template: `public class Main {
    public static int findMax(int[] numbers) {
        int maxVal = numbers[0];
        for (int num : numbers) {
            if (num > maxVal) {
                maxVal = num;
            }
        }
        return maxVal;
    }
}` 
        }
      ]
    }
  },
  {
    id: 'q2',
    title: '列表去重',
    description: '编写函数，接收一个列表/数组，返回去重后的新列表/数组。',
    languages: ['python', 'java'],
    python: {
      description: '编写函数 remove_duplicates(lst)，接收列表，返回去重后的新列表。',
      rubrics: '1. 逻辑正确(60分)\n2. 代码规范(20分)\n3. 效率(20分)',
      template: `# 列表去重
def remove_duplicates(lst):
    pass`,
      practices: [
        { 
          description: "基础练习：保持顺序的去重", 
          difficulty: 1, 
          questionId: "q2", 
          template: `def remove_duplicates(lst):
    result = []
    seen = set()
    for item in lst:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result` 
        }
      ]
    },
    java: {
      description: '编写 removeDuplicates 方法，接收数组，返回去重后的新数组。',
      rubrics: '1. 逻辑正确(60分)\n2. 代码规范(20分)\n3. 效率(20分)',
      template: `// 数组去重 (Java)
public class Main {
    public static int[] removeDuplicates(int[] arr) {
        return new int[0];
    }
}`,
      practices: [
        { 
          description: "基础练习：保持顺序的去重", 
          difficulty: 1, 
          questionId: "q2", 
          template: `import java.util.ArrayList;
import java.util.HashSet;

public class Main {
    public static int[] removeDuplicates(int[] arr) {
        ArrayList<Integer> result = new ArrayList<>();
        HashSet<Integer> seen = new HashSet<>();
        for (int num : arr) {
            if (!seen.contains(num)) {
                seen.add(num);
                result.add(num);
            }
        }
        return result.stream().mapToInt(Integer::intValue).toArray();
    }
}` 
        }
      ]
    }
  },
  {
    id: 'q3',
    title: '斐波那契数列',
    description: '编写函数，输出斐波那契数列的第n项。',
    languages: ['python', 'java'],
    python: {
      description: '编写函数 fibonacci(n)，返回斐波那契数列第n项。',
      rubrics: '1. 逻辑正确(60分)\n2. 代码规范(20分)\n3. 效率优化(20分)',
      template: `# 斐波那契数列
def fibonacci(n):
    pass`,
      practices: []
    },
    java: {
      description: '编写 fibonacci 方法，返回斐波那契数列第n项。',
      rubrics: '1. 逻辑正确(60分)\n2. 代码规范(20分)\n3. 效率优化(20分)',
      template: `// 斐波那契数列 (Java)
public class Main {
    public static int fibonacci(int n) {
        return 0;
    }
}`,
      practices: []
    }
  },
  {
    id: 'q4',
    title: '字符串反转',
    description: '编写函数，接收一个字符串，返回反转后的字符串。',
    languages: ['python', 'java'],
    python: {
      description: '编写函数 reverse_string(s)，接收字符串，返回反转后的字符串。',
      rubrics: '1. 逻辑正确(60分)\n2. 代码规范(20分)\n3. 边界处理(20分)',
      template: `# 字符串反转
def reverse_string(s):
    pass`,
      practices: [
        { 
          description: "基础练习：使用切片反转字符串", 
          difficulty: 1, 
          questionId: "q4", 
          template: `def reverse_string(s):
    return s[::-1]` 
        }
      ]
    },
    java: {
      description: '编写 reverseString 方法，接收字符串，返回反转后的字符串。',
      rubrics: '1. 逻辑正确(60分)\n2. 代码规范(20分)\n3. 边界处理(20分)',
      template: `// 字符串反转 (Java)
public class Main {
    public static String reverseString(String s) {
        return "";
    }
}`,
      practices: [
        { 
          description: "基础练习：使用StringBuilder反转字符串", 
          difficulty: 1, 
          questionId: "q4", 
          template: `public class Main {
    public static String reverseString(String s) {
        return new StringBuilder(s).reverse().toString();
    }
}` 
        }
      ]
    }
  },
  {
    id: 'q5',
    title: '质数判断',
    description: '编写函数，判断一个数是否为质数。',
    languages: ['python', 'java'],
    python: {
      description: '编写函数 is_prime(n)，判断n是否为质数，返回布尔值。',
      rubrics: '1. 逻辑正确(60分)\n2. 代码规范(20分)\n3. 效率优化(20分)',
      template: `# 质数判断
def is_prime(n):
    pass`,
      practices: [
        { 
          description: "基础练习：判断质数", 
          difficulty: 2, 
          questionId: "q5", 
          template: `def is_prime(n):
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True` 
        }
      ]
    },
    java: {
      description: '编写 isPrime 方法，判断n是否为质数，返回布尔值。',
      rubrics: '1. 逻辑正确(60分)\n2. 代码规范(20分)\n3. 效率优化(20分)',
      template: `// 质数判断 (Java)
public class Main {
    public static boolean isPrime(int n) {
        return false;
    }
}`,
      practices: [
        { 
          description: "基础练习：判断质数", 
          difficulty: 2, 
          questionId: "q5", 
          template: `public class Main {
    public static boolean isPrime(int n) {
        if (n <= 1) return false;
        if (n <= 3) return true;
        if (n % 2 == 0 || n % 3 == 0) return false;
        for (int i = 5; i * i <= n; i += 6) {
            if (n % i == 0 || n % (i + 2) == 0) return false;
        }
        return true;
    }
}` 
        }
      ]
    }
  },
  {
    id: 'q6',
    title: '冒泡排序',
    description: '编写函数，使用冒泡排序算法对列表/数组进行升序排序。',
    languages: ['python', 'java'],
    python: {
      description: '编写函数 bubble_sort(arr)，接收列表，返回排序后的新列表。',
      rubrics: '1. 逻辑正确(60分)\n2. 代码规范(20分)\n3. 效率优化(20分)',
      template: `# ============================================
# 题目：冒泡排序
# ============================================
# 题目描述：使用冒泡排序算法对列表进行升序排序。
# ============================================

def bubble_sort(arr):
    """
    冒泡排序
    
    参数：
        arr: 待排序的列表
        
    返回值：
        排序后的新列表
    """
    # ============ 请在此处编写代码 ============
    result = arr.copy()
    n = len(result)
    # ...
    return result`,
      practices: [
        { 
          description: "基础练习：实现冒泡排序", 
          difficulty: 2, 
          questionId: "q6", 
          template: `def bubble_sort(arr):
    result = arr.copy()
    n = len(result)
    for i in range(n):
        swapped = False
        for j in range(0, n-i-1):
            if result[j] > result[j+1]:
                result[j], result[j+1] = result[j+1], result[j]
                swapped = True
        if not swapped:
            break
    return result` 
        }
      ]
    },
    java: {
      description: '编写 bubbleSort 方法，接收数组，返回排序后的新数组。',
      rubrics: '1. 逻辑正确(60分)\n2. 代码规范(20分)\n3. 效率优化(20分)',
      template: `// ============================================
// 题目：冒泡排序
// ============================================
// 题目描述：使用冒泡排序算法对数组进行升序排序。
// ============================================

public class Main {
    public static void main(String[] args) {
        // 测试代码
    }
    
    public static int[] bubbleSort(int[] arr) {
        // ============ 请在此处编写代码 ============
        int[] result = arr.clone();
        int n = result.length;
        // ...
        return result;
    }
}`,
      practices: [
        { 
          description: "基础练习：实现冒泡排序", 
          difficulty: 2, 
          questionId: "q6", 
          template: `public class Main {
    public static int[] bubbleSort(int[] arr) {
        int[] result = arr.clone();
        int n = result.length;
        for (int i = 0; i < n-1; i++) {
            boolean swapped = false;
            for (int j = 0; j < n-i-1; j++) {
                if (result[j] > result[j+1]) {
                    int temp = result[j];
                    result[j] = result[j+1];
                    result[j+1] = temp;
                    swapped = true;
                }
            }
            if (!swapped) break;
        }
        return result;
    }
}` 
        }
      ]
    }
  },
  {
    id: 'q7',
    title: '二分查找',
    description: '编写函数，使用二分查找算法在有序列表/数组中查找目标值。',
    languages: ['python', 'java'],
    python: {
      description: '编写函数 binary_search(arr, target)，在有序列表中查找目标值，返回索引。',
      rubrics: '1. 逻辑正确(60分)\n2. 代码规范(20分)\n3. 边界处理(20分)',
      template: `# ============================================
# 题目：二分查找
# ============================================
# 题目描述：使用二分查找算法在有序列表中查找目标值。
# ============================================

def binary_search(arr, target):
    """
    二分查找
    
    参数：
        arr: 有序列表（升序）
        target: 要查找的目标值
        
    返回值：
        目标值的索引，如果未找到返回-1
    """
    # ============ 请在此处编写代码 ============
    # ...
    return -1`,
      practices: [
        { 
          description: "基础练习：实现二分查找", 
          difficulty: 2, 
          questionId: "q7", 
          template: `def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1` 
        }
      ]
    },
    java: {
      description: '编写 binarySearch 方法，在有序数组中查找目标值，返回索引。',
      rubrics: '1. 逻辑正确(60分)\n2. 代码规范(20分)\n3. 边界处理(20分)',
      template: `// ============================================
// 题目：二分查找
// ============================================
// 题目描述：使用二分查找算法在有序数组中查找目标值。
// ============================================

public class Main {
    public static void main(String[] args) {
        // 测试代码
    }
    
    public static int binarySearch(int[] arr, int target) {
        // ============ 请在此处编写代码 ============
        // ...
        return -1;
    }
}`,
      practices: [
        { 
          description: "基础练习：实现二分查找", 
          difficulty: 2, 
          questionId: "q7", 
          template: `public class Main {
    public static int binarySearch(int[] arr, int target) {
        int left = 0, right = arr.length - 1;
        while (left <= right) {
            int mid = left + (right - left) / 2;
            if (arr[mid] == target) {
                return mid;
            } else if (arr[mid] < target) {
                left = mid + 1;
            } else {
                right = mid - 1;
            }
        }
        return -1;
    }
}` 
        }
      ]
    }
  }
]

export const adminStore = reactive({
  classes: ['默认班级'],
  currentClass: '默认班级',
  allReports: {},
  questions: [],
  students: [
    { userId: '2024001', name: '张三', class: '默认班级' },
    { userId: '2024002', name: '李四', class: '默认班级' },
    { userId: '2024003', name: '王五', class: '默认班级' },
  ],

  init() {
    const saved = localStorage.getItem('admin_classes')
    if (saved) {
      const data = JSON.parse(saved)
      this.classes = data.classes || ['默认班级']
      this.currentClass = data.currentClass || '默认班级'
      this.allReports = data.allReports || {}
      this.students = data.students || this.students
    } else {
      this.allReports = { '默认班级': [] }
    }
    this.loadStudentReports()
    this.loadQuestions()
  },

  loadStudentReports() {
    const savedReports = localStorage.getItem('admin_reports')
    if (savedReports) {
      const reports = JSON.parse(savedReports)
      reports.forEach(r => {
        const className = r.class || '默认班级'
        if (!this.allReports[className]) this.allReports[className] = []
        if (!this.allReports[className].find(report => report.id === r.id)) {
          this.allReports[className].push(r)
        }
      })
    }
    this.saveToStorage()
  },

  async loadQuestions() {
    try {
      const apiQuestions = await fetchQuestions()
      if (apiQuestions) {
        this.questions = Object.values(apiQuestions)
        this.saveQuestions()
        return
      }
    } catch (error) {
      console.error('从API加载题目失败，使用本地存储:', error)
    }
    
    const saved = localStorage.getItem('admin_questions')
    if (saved) {
      this.questions = JSON.parse(saved)
    } else {
      this.questions = JSON.parse(JSON.stringify(defaultQuestions))
      this.saveQuestions()
    }
  },

  // 获取题目数据（供学生端使用）
  getQuestionsForStudent() {
    const result = {}
    this.questions.forEach(q => {
      result[q.id] = q
    })
    return result
  },
  
  // 从API同步题目数据
  async syncQuestionsFromAPI() {
    try {
      const apiQuestions = await fetchQuestions()
      if (apiQuestions) {
        this.questions = Object.values(apiQuestions)
        this.saveQuestions()
        return { success: true, message: '题目同步成功' }
      }
    } catch (error) {
      console.error('同步题目失败:', error)
      return { success: false, message: '同步失败: ' + error.message }
    }
  },

  // 获取单个题目
  getQuestionById(id) {
    return this.questions.find(q => q.id === id)
  },

  updateStudentClass(userId, newClass) {
    const student = this.students.find(s => s.userId === userId)
    if (student) {
      student.class = newClass
      this.saveToStorage()
    }
  },

  saveQuestions() {
    try { localStorage.setItem('admin_questions', JSON.stringify(this.questions)) } catch (e) {}
  },

  addQuestion(question) {
    // 确保题目有完整的结构
    const defaultPython = { description: '', rubrics: '', template: '', practices: [] }
    const defaultJava = { description: '', rubrics: '', template: '', practices: [] }
    
    if (!question.python) question.python = { ...defaultPython }
    if (!question.java) question.java = { ...defaultJava }
    if (!question.python.practices) question.python.practices = []
    if (!question.java.practices) question.java.practices = []
    if (!question.description) question.description = question.python.description || ''
    
    const idx = this.questions.findIndex(q => q.id === question.id)
    if (idx >= 0) this.questions[idx] = question
    else this.questions.push(question)
    this.saveQuestions()
  },

  deleteQuestion(id) {
    this.questions = this.questions.filter(q => q.id !== id)
    this.saveQuestions()
  },

  get reports() {
    if (!this.allReports[this.currentClass]) this.allReports[this.currentClass] = []
    return this.allReports[this.currentClass]
  },

  addReport(report) {
    if (!this.allReports[this.currentClass]) this.allReports[this.currentClass] = []
    this.allReports[this.currentClass].push(report)
    this.saveToStorage()
  },

  addClass(name) {
    if (!this.classes.includes(name)) {
      this.classes.push(name)
      this.allReports[name] = []
      this.saveToStorage()
    }
  },

  switchClass(name) {
    this.currentClass = name
    this.saveToStorage()
  },

  saveToStorage() {
    try {
      localStorage.setItem('admin_classes', JSON.stringify({
        classes: this.classes,
        currentClass: this.currentClass,
        allReports: this.allReports,
        students: this.students
      }))
    } catch (e) {}
  },

  // 统计方法
  getStats() {
    const reports = this.reports
    const stats = {
      total: reports.length,
      averageScore: 0,
      passed: 0,
      failed: 0,
      questionStats: {},
      studentStats: {}
    }

    if (reports.length === 0) return stats

    let totalScore = 0
    reports.forEach(r => {
      const score = r.overall_score || 0
      totalScore += score
      
      if (score >= 60) stats.passed++
      else stats.failed++

      // 按题目统计
      const q = r.question || '未知'
      if (!stats.questionStats[q]) {
        stats.questionStats[q] = { total: 0, sum: 0, count: 0 }
      }
      stats.questionStats[q].total += score
      stats.questionStats[q].count++

      // 按学生统计
      const student = r.student_name || r.userId || '未知'
      if (!stats.studentStats[student]) {
        stats.studentStats[student] = { total: 0, count: 0, best: 0 }
      }
      stats.studentStats[student].total += score
      stats.studentStats[student].count++
      if (score > stats.studentStats[student].best) {
        stats.studentStats[student].best = score
      }
    })

    stats.averageScore = Math.round(totalScore / reports.length * 10) / 10

    // 计算题目平均分
    Object.keys(stats.questionStats).forEach(q => {
      stats.questionStats[q].avg = Math.round(stats.questionStats[q].total / stats.questionStats[q].count * 10) / 10
    })

    // 计算学生平均分
    Object.keys(stats.studentStats).forEach(s => {
      stats.studentStats[s].avg = Math.round(stats.studentStats[s].total / stats.studentStats[s].count * 10) / 10
    })

    return stats
  }
})

adminStore.init()