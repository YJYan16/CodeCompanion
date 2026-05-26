"""
编程知识图谱 - 节点与关系定义
"""

# ================= 知识点节点 =================
KNOWLEDGE_NODES = [
    {
        "id": "K001",
        "name": "列表基本概念",
        "type": "知识点",
        "difficulty": 1,
        "description": "理解列表的创建、元素访问、长度len()",
        "resources": ["列表入门练习", "Python官方文档-列表"]
    },
    {
        "id": "K002",
        "name": "列表索引访问",
        "type": "知识点",
        "difficulty": 2,
        "prerequisites": ["K001"],
        "description": "使用索引访问列表元素，理解0-based索引",
        "resources": ["索引练习", "负索引教程"]
    },
    {
        "id": "K003",
        "name": "循环遍历",
        "type": "知识点",
        "difficulty": 2,
        "prerequisites": ["K001"],
        "description": "使用for/while遍历列表，理解迭代过程",
        "resources": ["for循环基础", "range()用法"]
    },
    {
        "id": "K004",
        "name": "变量初始化",
        "type": "知识点",
        "difficulty": 1,
        "description": "变量使用前赋初始值，理解None与数值初始化的区别",
        "resources": ["变量作用域练习", "初始值选择指南"]
    },
    {
        "id": "K005",
        "name": "函数定义与返回值",
        "type": "知识点",
        "difficulty": 2,
        "prerequisites": ["K001", "K004"],
        "description": "定义函数、return语句、None返回值",
        "resources": ["函数定义练习", "return详解"]
    },
    {
        "id": "K006",
        "name": "代码缩进规范",
        "type": "知识点",
        "difficulty": 1,
        "description": "Python缩进规则，Tab与空格统一",
        "resources": ["PEP8缩进规范"]
    },
    {
        "id": "K007",
        "name": "边界条件处理",
        "type": "知识点",
        "difficulty": 3,
        "prerequisites": ["K002", "K003"],
        "description": "处理空列表、单元素列表、索引越界等特殊情况",
        "resources": ["边界条件练习", "防御性编程"]
    },
    {
        "id": "K008",
        "name": "算法思维",
        "type": "知识点",
        "difficulty": 3,
        "prerequisites": ["K003", "K004"],
        "description": "设计正确算法，如找最大值、排序等",
        "resources": ["算法入门", "找最大值多种实现"]
    }
]

# ================= 错误模式节点 =================
ERROR_NODES = [
    {
        "id": "E001",
        "name": "索引越界 (IndexError)",
        "type": "错误模式",
        "caused_by": ["K002", "K007"],
        "pattern": "访问超出列表长度的索引",
        "fix_hint": "检查索引范围，使用len()-1或改用for...in遍历"
    },
    {
        "id": "E002",
        "name": "初始化错误",
        "type": "错误模式",
        "caused_by": ["K004"],
        "pattern": "最大值初始化为0或None导致逻辑错误",
        "fix_hint": "应初始化为第一个元素或负无穷float('-inf')"
    },
    {
        "id": "E003",
        "name": "忘记返回值",
        "type": "错误模式",
        "caused_by": ["K005"],
        "pattern": "函数末尾缺少return语句",
        "fix_hint": "在函数末尾添加return语句返回计算结果"
    },
    {
        "id": "E004",
        "name": "缩进错误 (IndentationError)",
        "type": "错误模式",
        "caused_by": ["K006"],
        "pattern": "代码块缩进不一致或缺失",
        "fix_hint": "统一使用4个空格缩进，检查if/for/def后的缩进"
    },
    {
        "id": "E005",
        "name": "逻辑错误-比较相邻元素",
        "type": "错误模式",
        "caused_by": ["K003", "K008"],
        "pattern": "比较相邻元素而非逐个比较",
        "fix_hint": "应维护当前最大值，与每个元素比较，而不是比较相邻元素"
    },
    {
        "id": "E006",
        "name": "空列表未处理",
        "type": "错误模式",
        "caused_by": ["K007"],
        "pattern": "访问空列表元素导致错误",
        "fix_hint": "在函数开头判断 if not numbers: return None"
    }
]
# 追加 Java 知识点
JAVA_KNOWLEDGE_NODES = [
    {
        "id": "K_J01",
        "name": "Java类定义",
        "type": "知识点",
        "difficulty": 1,
        "description": "理解 class 关键字、类名规范、main 方法",
        "resources": ["Java入门-类与对象", "main方法详解"]
    },
    {
        "id": "K_J02",
        "name": "Java方法定义",
        "type": "知识点",
        "difficulty": 2,
        "prerequisites": ["K_J01"],
        "description": "方法的声明、返回类型、参数列表",
        "resources": ["Java方法教程"]
    },
    {
        "id": "K_J03",
        "name": "Java数组与集合",
        "type": "知识点",
        "difficulty": 2,
        "prerequisites": ["K_J01"],
        "description": "数组声明、遍历、ArrayList使用",
        "resources": ["Java数组练习"]
    }
]

# 追加 Java 错误模式
JAVA_ERROR_NODES = [
    {
        "id": "E_J01",
        "name": "缺少分号 (;)",
        "type": "错误模式",
        "caused_by": ["K_J01"],
        "pattern": "语句末尾缺少分号",
        "fix_hint": "在语句末尾添加分号 ;"
    },
    {
        "id": "E_J02",
        "name": "类型不匹配",
        "type": "错误模式",
        "caused_by": ["K_J02"],
        "pattern": "返回类型与声明不一致",
        "fix_hint": "确保 return 语句的类型与函数声明一致"
    },
    {
        "id": "E_J03",
        "name": "数组越界 (ArrayIndexOutOfBoundsException)",
        "type": "错误模式",
        "caused_by": ["K_J03"],
        "pattern": "访问超出数组长度的索引",
        "fix_hint": "使用 .length 检查数组边界，或使用 for-each 循环"
    }
]

# 合并到原有数据
KNOWLEDGE_NODES.extend(JAVA_KNOWLEDGE_NODES)
ERROR_NODES.extend(JAVA_ERROR_NODES)