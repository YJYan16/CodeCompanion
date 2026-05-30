<template>
  <div class="admin-page">
    <el-card>
      <template #header>
        <span>📝 题库管理</span>
        <el-button type="primary" size="small" @click="openAddDialog" style="float:right">添加题目</el-button>
      </template>

      <el-table :data="adminStore.questions" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="title" label="题目名称" />
        <el-table-column label="支持语言" width="180">
          <template #default="{ row }">
            <template v-if="row.languages && row.languages.length > 0">
              <el-tag v-for="lang in row.languages" :key="lang" size="small" style="margin-right:4px">
                {{ lang }}
              </el-tag>
            </template>
            <span v-else style="color:#999">未设置</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="editQuestion(row)">编辑</el-button>
            <el-button size="small" type="success" @click="generateTemplate(row)">生成模板</el-button>
            <el-button size="small" type="danger" @click="confirmDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showAddDialog" title="添加/编辑题目" width="800px">
      <el-form :model="form" label-width="100px">
        <el-form-item v-if="isEditing" label="题目ID">
          <el-input v-model="form.id" placeholder="自动生成" disabled />
        </el-form-item>
        <el-form-item v-if="!isEditing" label="题目ID">
          <el-input value="自动分配" disabled />
        </el-form-item>
        <el-form-item label="题目名称">
          <el-input v-model="form.title" />
          <el-button v-if="form.title" type="info" size="small" @click="generateRequirements" :loading="generating">
            ✨ 自动生成要求
          </el-button>
        </el-form-item>
        <el-form-item label="题目描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="题目整体描述" />
        </el-form-item>
        <el-form-item label="支持语言">
          <el-checkbox-group v-model="form.languages">
            <el-checkbox value="python">Python</el-checkbox>
            <el-checkbox value="java">Java</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        
        <el-divider />
        <div style="display:flex;justify-content:space-between;align-items:center">
          <h4>🐍 Python 配置</h4>
          <el-button v-if="form.languages.includes('python')" type="info" size="small" @click="generatePythonTemplate">
            📋 生成模板
          </el-button>
        </div>
        <el-form-item label="题目描述">
          <el-input v-model="form.python.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="评分标准">
          <el-input v-model="form.python.rubrics" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="代码模板">
          <el-input v-model="form.python.template" type="textarea" :rows="6" placeholder="自动生成的代码模板" />
        </el-form-item>

        <el-divider />
        <div style="display:flex;justify-content:space-between;align-items:center">
          <h4>☕ Java 配置</h4>
          <el-button v-if="form.languages.includes('java')" type="info" size="small" @click="generateJavaTemplate">
            📋 生成模板
          </el-button>
        </div>
        <el-form-item label="题目描述">
          <el-input v-model="form.java.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="评分标准">
          <el-input v-model="form.java.rubrics" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="代码模板">
          <el-input v-model="form.java.template" type="textarea" :rows="6" placeholder="自动生成的代码模板" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="success" @click="saveAndPublish">发布题目</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { adminStore } from '@/store/index.js'

const showAddDialog = ref(false)
const generating = ref(false)
const isEditing = ref(false) // ★ 是否为编辑模式

const defaultForm = {
  id: '', title: '', description: '', languages: ['python'],
  python: { description: '', rubrics: '', template: '' },
  java: { description: '', rubrics: '', template: '' }
}
const form = reactive(JSON.parse(JSON.stringify(defaultForm)))

const editQuestion = (row) => {
  Object.assign(form, JSON.parse(JSON.stringify(row)))
  if (!form.python) form.python = { description: '', rubrics: '', template: '' }
  if (!form.java) form.java = { description: '', rubrics: '', template: '' }
  isEditing.value = true
  showAddDialog.value = true
}

const openAddDialog = () => {
  // 重置表单为默认状态
  Object.assign(form, JSON.parse(JSON.stringify(defaultForm)))
  isEditing.value = false
  showAddDialog.value = true
}

// ★ 根据题目名称自动生成题目要求
const generateRequirements = () => {
  if (!form.title) return
  
  generating.value = true
  
  // 根据题目名称生成描述和评分标准
  const title = form.title
  
  // 生成整体描述
  form.description = `编写程序实现${title}功能。`
  
  // 生成 Python 描述和评分标准
  form.python.description = generateLangDescription(title, 'Python')
  form.python.rubrics = generateRubrics()
  
  // 生成 Java 描述和评分标准
  form.java.description = generateLangDescription(title, 'Java')
  form.java.rubrics = generateRubrics()
  
  generating.value = false
  alert('✨ 题目要求已自动生成，可以根据需要进行编辑')
}

// 生成语言特定的描述
const generateLangDescription = (title, lang) => {
  const funcName = title.replace(/[^\w]/g, '_').toLowerCase()
  if (lang === 'Python') {
    return `编写函数 ${funcName}(...)，实现${title}功能。`
  } else {
    return `编写 ${funcName} 方法，实现${title}功能。`
  }
}

// 生成标准评分标准
const generateRubrics = () => {
  return `1. 逻辑正确(60分)
2. 代码规范(20分)
3. 边界处理(20分)`
}

// ★ 生成 Python 代码模板（详细版）
const generatePythonTemplate = () => {
  if (!form.title) return
  
  const funcName = form.title.replace(/[^\w]/g, '_').toLowerCase()
  form.python.template = `# ============================================
# 题目：${form.title}
# ============================================
# 题目描述：${form.python.description || form.description || '请实现题目要求的功能'}
# 评分标准：${form.python.rubrics || '请参考评分标准'}
# ============================================

def ${funcName}(*args, **kwargs):
    """
    ${form.title}
    
    参数：
        根据题目要求添加参数
        
    返回值：
        根据题目要求返回相应结果
        
    示例：
        # 请根据题目要求添加示例
        # result = ${funcName}(输入参数)
        # print(result)
    """
    # ============ 请在此处编写代码 ============
    # 1. 分析题目要求
    # 2. 设计算法逻辑
    # 3. 编写代码实现
    # 4. 测试边界情况
    
    # 初始化结果
    result = None
    
    # 编写你的代码逻辑
    # ...
    
    return result

# ============================================
# 测试代码（可选）
# ============================================
if __name__ == '__main__':
    # 测试示例
    # test_input = ...
    # test_output = ${funcName}(test_input)
    # print(f"测试结果: {test_output}")
    pass`
  
  alert('📋 Python 代码模板已生成（详细版）')
}

// ★ 生成 Java 代码模板（详细版）
const generateJavaTemplate = () => {
  if (!form.title) return
  
  const funcName = form.title.replace(/[^\w]/g, '_').toLowerCase()
  form.java.template = `// ============================================
// 题目：${form.title}
// ============================================
// 题目描述：${form.java.description || form.description || '请实现题目要求的功能'}
// 评分标准：${form.java.rubrics || '请参考评分标准'}
// ============================================

public class Main {
    
    /**
     * ${form.title}
     * 
     * @param args 命令行参数
     */
    public static void main(String[] args) {
        // 测试示例
        // int result = ${funcName}(输入参数);
        // System.out.println("测试结果: " + result);
    }
    
    /**
     * ${form.title}
     * 
     * @param 请根据题目要求添加参数
     * @return 请根据题目要求返回相应结果
     */
    public static int ${funcName}() {
        // ============ 请在此处编写代码 ============
        // 1. 分析题目要求
        // 2. 设计算法逻辑
        // 3. 编写代码实现
        // 4. 测试边界情况
        
        // 初始化结果
        int result = 0;
        
        // 编写你的代码逻辑
        // ...
        
        return result;
    }
}`
  
  alert('📋 Java 代码模板已生成（详细版）')
}

// ★ 为已有题目批量生成模板（详细版）
const generateTemplate = (row) => {
  console.log('generateTemplate called with row:', row)
  console.log('row.id:', row.id, 'type:', typeof row.id)
  console.log('Boolean(row.id):', Boolean(row.id))
  console.log('row.id === "":', row.id === '')
  console.log('!row.id:', !row.id)
  
  if (!row.id || row.id === '') {
    alert('题目ID不能为空，请刷新页面重试')
    console.error('generateTemplate: row.id is undefined or empty', row)
    return
  }

  const funcName = row.title.replace(/[^\w]/g, '_').toLowerCase()

  // 生成 Python 模板（详细版）
  const pythonTemplate = `# ============================================
# 题目：${row.title}
# ============================================
# 题目描述：${row.python?.description || row.description || '请实现题目要求的功能'}
# ============================================

def ${funcName}(*args, **kwargs):
    """
    ${row.title}

    参数：
        根据题目要求添加参数

    返回值：
        根据题目要求返回相应结果
    """
    # ============ 请在此处编写代码 ============
    result = None
    # ...
    return result`

  // 生成 Java 模板（详细版）
  const javaTemplate = `// ============================================
// 题目：${row.title}
// ============================================
// 题目描述：${row.java?.description || row.description || '请实现题目要求的功能'}
// ============================================

public class Main {
    public static void main(String[] args) {
        // 测试代码
    }

    public static int ${funcName}() {
        // ============ 请在此处编写代码 ============
        int result = 0;
        // ...
        return result;
    }
}`

  // 直接更新 row 的属性
  if (!row.python) row.python = {}
  if (!row.java) row.java = {}
  row.python.template = pythonTemplate
  row.java.template = javaTemplate

  // 保存到服务器
  adminStore.updateQuestion(row)
  alert('📋 代码模板已生成并保存（详细版）')
}

// ★ 保存并发布题目（支持新增和编辑）
const saveAndPublish = () => {
  if (!form.title) return alert('请填写题目名称')
  if (isEditing.value && !form.id) return alert('题目ID不能为空')

  // 确保模板存在（使用详细版模板）
  if (form.languages.includes('python') && !form.python.template) {
    const funcName = form.title.replace(/[^\w]/g, '_').toLowerCase()
    form.python.template = `# ============================================
# 题目：${form.title}
# ============================================
# 题目描述：${form.python.description || form.description || '请实现题目要求的功能'}
# ============================================

def ${funcName}(*args, **kwargs):
    """
    ${form.title}

    参数：
        根据题目要求添加参数

    返回值：
        根据题目要求返回相应结果
    """
    # ============ 请在此处编写代码 ============
    result = None
    # ...
    return result`
  }

  if (form.languages.includes('java') && !form.java.template) {
    const funcName = form.title.replace(/[^\w]/g, '_').toLowerCase()
    form.java.template = `// ============================================
// 题目：${form.title}
// ============================================
// 题目描述：${form.java.description || form.description || '请实现题目要求的功能'}
// ============================================

public class Main {
    public static void main(String[] args) {
        // 测试代码
    }

    public static int ${funcName}() {
        // ============ 请在此处编写代码 ============
        int result = 0;
        // ...
        return result;
    }
}`
  }

  const questionData = JSON.parse(JSON.stringify(form))
  if (isEditing.value) {
    adminStore.updateQuestion(questionData)
    alert('✅ 题目已更新')
  } else {
    adminStore.addQuestion(questionData)
    alert('✅ 题目已发布，学生端可以看到并使用')
  }
  showAddDialog.value = false
  isEditing.value = false
  Object.assign(form, JSON.parse(JSON.stringify(defaultForm)))
}

// ★ 确认删除题目
const confirmDelete = (row) => {
  if (confirm(`确定要删除题目【${row.title}】吗？此操作不可恢复！`)) {
    adminStore.deleteQuestion(row.id)
    alert('✅ 题目已删除')
  }
}
</script>