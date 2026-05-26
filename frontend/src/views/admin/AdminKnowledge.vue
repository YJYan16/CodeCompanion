<template>
  <div class="admin-page">
    <h2>🧠 编程知识图谱</h2>

    <!-- 上半部分：知识点体系（不变） -->
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card header="Python 知识点体系"><div ref="pythonRef" style="height:400px"></div></el-card>
      </el-col>
      <el-col :span="12">
        <el-card header="Java 知识点体系"><div ref="javaRef" style="height:400px"></div></el-card>
      </el-col>
    </el-row>

    <!-- 下半部分：诊断链路 -->
    <el-row :gutter="20" style="margin-top:20px">
      <el-col :span="24">
        <el-card>
          <template #header>
            <span>诊断链路（由AI生成）</span>
          </template>

          <!-- 筛选框：班级 + 语言 + 学生姓名 -->
          <div style="display:flex;gap:10px;margin-bottom:16px;align-items:center;flex-wrap:wrap">
            <span style="color:#666;font-size:14px">班级:</span>
            <el-select v-model="filterClass" size="small" style="width:150px" filterable @change="onFilterChange">
              <el-option v-for="c in adminStore.classes" :key="c" :label="c" :value="c" />
            </el-select>
            <span style="color:#666;font-size:14px;margin-left:8px">语言:</span>
            <el-select v-model="filterLang" size="small" style="width:110px" @change="onFilterChange">
              <el-option label="全部语言" value="all" />
              <el-option label="Python" value="python" />
              <el-option label="Java" value="java" />
            </el-select>
            <span style="color:#666;font-size:14px;margin-left:8px">学生:</span>
            <el-select v-model="selectedStudent" size="small" style="width:180px" filterable clearable placeholder="搜索学生姓名" @change="onStudentChange">
              <el-option v-for="r in filteredReports" :key="r.student_name" :label="r.student_name" :value="r.student_name" />
            </el-select>
          </div>

          <!-- 诊断链路内容 -->
          <div v-if="selectedReport" style="margin-top:10px">
            <el-steps direction="vertical">
              <el-step v-for="(kp, i) in (selectedReport.weak_knowledge_points || [])" :key="'kp'+i" :title="kp" status="warning" description="需加强的知识点" />
              <el-step v-for="(d, i) in (selectedReport.deductions || [])" :key="'d'+i" :title="d.type" status="error" :description="d.suggestion" />
            </el-steps>
          </div>
          <el-empty v-else description="请选择学生查看诊断链路" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { adminStore } from '@/store/index.js'

const filterClass = ref(adminStore.currentClass)
const filterLang = ref('all')
const selectedStudent = ref('')
const pythonRef = ref(null)
const javaRef = ref(null)

const filteredReports = computed(() => {
  let result = adminStore.allReports[filterClass.value] || []
  if (filterLang.value !== 'all') result = result.filter(r => (r.language || 'python') === filterLang.value)
  return result
})

const selectedReport = computed(() => {
  if (!selectedStudent.value) return null
  return filteredReports.value.find(r => r.student_name === selectedStudent.value) || null
})

const onFilterChange = () => {
  selectedStudent.value = ''
}

const onStudentChange = () => {}

const pythonNodes = [
  { name: '列表操作', children: [{ name: '索引访问' }, { name: '遍历循环' }, { name: '切片' }] },
  { name: '函数定义', children: [{ name: '参数传递' }, { name: '返回值' }] },
  { name: '变量初始化', children: [{ name: '类型选择' }, { name: '边界值处理' }] }
]

const javaNodes = [
  { name: '类定义', children: [{ name: '方法声明' }, { name: '访问修饰符' }] },
  { name: '数组操作', children: [{ name: '索引访问' }, { name: '边界检查' }] },
  { name: '语法规范', children: [{ name: '分号' }, { name: '命名规范' }] }
]

onMounted(() => {
  nextTick(() => {
    if (pythonRef.value) {
      const existing = echarts.getInstanceByDom(pythonRef.value)
      if (existing) existing.dispose()
      echarts.init(pythonRef.value).setOption({ series: [{ type: 'tree', data: pythonNodes, layout: 'radial', symbol: 'roundRect', symbolSize: 12 }] })
    }
    if (javaRef.value) {
      const existing = echarts.getInstanceByDom(javaRef.value)
      if (existing) existing.dispose()
      echarts.init(javaRef.value).setOption({ series: [{ type: 'tree', data: javaNodes, layout: 'radial', symbol: 'roundRect', symbolSize: 12 }] })
    }
  })
})
</script>

<style scoped>
.admin-page { max-width: 1200px; }
</style>