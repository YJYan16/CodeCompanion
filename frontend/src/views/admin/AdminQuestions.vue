<template>
  <div class="admin-page">
    <el-card>
      <template #header>
        <span>📝 题库管理</span>
        <el-button type="primary" size="small" @click="showAddDialog = true" style="float:right">添加题目</el-button>
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
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button size="small" @click="editQuestion(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="adminStore.deleteQuestion(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showAddDialog" title="添加/编辑题目" width="700px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="题目ID">
          <el-input v-model="form.id" placeholder="q1" />
        </el-form-item>
        <el-form-item label="题目名称">
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="支持语言">
          <el-checkbox-group v-model="form.languages">
            <el-checkbox label="python">Python</el-checkbox>
            <el-checkbox label="java">Java</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        
        <el-divider />
        <h4>Python 配置</h4>
        <el-form-item label="题目描述">
          <el-input v-model="form.python.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="评分标准">
          <el-input v-model="form.python.rubrics" type="textarea" :rows="2" />
        </el-form-item>

        <el-divider />
        <h4>Java 配置</h4>
        <el-form-item label="题目描述">
          <el-input v-model="form.java.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="评分标准">
          <el-input v-model="form.java.rubrics" type="textarea" :rows="2" />
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
import { adminStore } from '@/store/index.js'

const showAddDialog = ref(false)
const defaultForm = {
  id: '', title: '', languages: ['python'],
  python: { description: '', rubrics: '' },
  java: { description: '', rubrics: '' }
}
const form = reactive(JSON.parse(JSON.stringify(defaultForm)))

const editQuestion = (row) => {
  Object.assign(form, JSON.parse(JSON.stringify(row)))
  showAddDialog.value = true
}

const saveQuestion = () => {
  if (!form.id || !form.title) return alert('请填写题目ID和名称')
  adminStore.addQuestion(JSON.parse(JSON.stringify(form)))
  showAddDialog.value = false
  Object.assign(form, JSON.parse(JSON.stringify(defaultForm)))
}
</script>