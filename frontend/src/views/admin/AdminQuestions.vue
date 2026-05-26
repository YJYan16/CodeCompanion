<template>
  <div class="admin-page">
    <el-card>
      <template #header>
        <span>📝 题库管理</span>
        <el-button type="primary" size="small" @click="showAddDialog = true" style="float:right">
          添加题目
        </el-button>
      </template>

      <el-table :data="questions" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="title" label="题目名称" />
        <el-table-column prop="language" label="语言" width="80" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button size="small" @click="editQuestion(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteQuestion(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="questions.length === 0" description="暂无题目" />
    </el-card>

    <!-- 添加/编辑对话框 -->
    <el-dialog v-model="showAddDialog" title="添加题目" width="600px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="题目ID">
          <el-input v-model="form.id" placeholder="q1" />
        </el-form-item>
        <el-form-item label="语言">
          <el-select v-model="form.language">
            <el-option label="Python" value="python" />
            <el-option label="Java" value="java" />
          </el-select>
        </el-form-item>
        <el-form-item label="题目名称">
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="题目描述">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="评分标准">
          <el-input v-model="form.rubrics" type="textarea" :rows="3" />
            <el-button 
              size="small" 
              type="success" 
              @click="generateRubrics" 
              :loading="rubricsLoading"
              style="margin-top:5px"
            >
            🤖 AI 生成评分标准
          </el-button>
        </el-form-item>
        <el-form-item label="代码模板">
          <el-input v-model="form.template" type="textarea" :rows="4" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="saveQuestion">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'

const questions = ref([
  {
    id: 'q1', title: '找最大值', language: 'python',
    description: '编写函数 find_max(numbers)，接收整数列表，返回最大值。',
    rubrics: '1. 逻辑正确(60分)\n2. 代码规范(20分)\n3. 边界处理(20分)',
    template: '# 找最大值\ndef find_max(numbers):\n    pass'
  },
  {
    id: 'q2', title: '列表去重', language: 'python',
    description: '编写函数 remove_duplicates(lst)，去重后返回新列表。',
    rubrics: '1. 逻辑正确(60分)\n2. 代码规范(20分)\n3. 效率考虑(20分)',
    template: '# 列表去重\ndef remove_duplicates(lst):\n    pass'
  },
  {
    id: 'j1', title: '找最大值 (Java)', language: 'java',
    description: '编写 findMax 方法，返回数组最大值。',
    rubrics: '1. 逻辑正确(60分)\n2. 代码规范(20分)\n3. 边界处理(20分)',
    template: 'public class Main {\n    public static int findMax(int[] nums) {\n        return 0;\n    }\n}'
  }
])

const showAddDialog = ref(false)
const form = reactive({
  id: '', title: '', language: 'python', description: '', rubrics: '', template: ''
})

const editQuestion = (row) => {
  Object.assign(form, row)
  showAddDialog.value = true
}

const saveQuestion = () => {
  const idx = questions.value.findIndex(q => q.id === form.id)
  if (idx >= 0) {
    questions.value[idx] = { ...form }
  } else {
    questions.value.push({ ...form })
  }
  showAddDialog.value = false
  // 重置表单
  Object.keys(form).forEach(k => form[k] = k === 'language' ? 'python' : '')
}

const deleteQuestion = (id) => {
  questions.value = questions.value.filter(q => q.id !== id)
}
const rubricsLoading = ref(false)

const generateRubrics = async () => {
  if (!form.description.trim()) {
    alert('请先填写题目描述')
    return
  }
  rubricsLoading.value = true
  try {
    const res = await api.post('/coze/rubrics', { description: form.description })
    if (res.data.success) {
      form.rubrics = res.data.rubrics
    } else {
      // 降级：本地生成
      form.rubrics = `1. 逻辑正确(60分)\n2. 代码规范(20分)\n3. 边界处理(20分)`
    }
  } catch (e) {
    // 降级
    form.rubrics = `1. 逻辑正确(60分)\n2. 代码规范(20分)\n3. 边界处理(20分)`
  } finally {
    rubricsLoading.value = false
  }
}
</script>

<style scoped>
.admin-page {
  max-width: 1000px;
}
.admin-page {
  max-width: 1100px;
}
.admin-page :deep(.el-card) {
  border-radius: 16px;
  border: none;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}
.admin-page :deep(.el-card__header) {
  font-weight: 600;
  font-size: 16px;
  padding: 16px 20px;
  border-bottom: 1px solid #f5f5f5;
}
.admin-page :deep(.el-button--primary) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 10px;
  transition: all 0.3s ease;
}
.admin-page :deep(.el-button--primary:hover) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
}
.admin-page :deep(.el-table) {
  border-radius: 12px;
  overflow: hidden;
}
.admin-page :deep(.el-table th) {
  background: #f8f9fc;
  color: #555;
  font-weight: 600;
}
</style>