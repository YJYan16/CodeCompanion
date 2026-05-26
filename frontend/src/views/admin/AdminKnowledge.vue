<template>
  <div class="admin-page">
    <h2>🧠 编程知识图谱</h2>
    
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>Python 知识点体系</template>
          <div ref="pythonRef" style="height:400px"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>Java 知识点体系</template>
          <div ref="javaRef" style="height:400px"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top:20px">
      <el-col :span="24">
        <el-card>
  <template #header>诊断链路（由AI生成）</template>
  <el-select 
    v-model="selectedStudent" 
    style="width:300px"
    placeholder="输入姓名搜索或选择学生"
    filterable
    clearable
  >
    <el-option 
      v-for="r in reports" 
      :key="r.student_name" 
      :label="r.student_name" 
      :value="r.student_name" 
    />
  </el-select>
  
  <div v-if="selectedReport" style="margin-top:15px">
    <el-steps direction="vertical">
      <el-step 
        v-for="(kp, i) in (selectedReport.weak_knowledge_points || [])" 
        :key="'kp'+i" 
        :title="kp" 
        status="warning"
        description="需要加强的知识点"
      />
      <el-step 
        v-for="(d, i) in (selectedReport.deductions || [])" 
        :key="'d'+i" 
        :title="d.type" 
        status="error" 
        :description="d.suggestion"
      />
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

const reports = computed(() => adminStore.reports)
const selectedStudent = ref('')
const pythonRef = ref(null)
const javaRef = ref(null)

const selectedReport = computed(() => {
  return reports.value.find(r => r.student_name === selectedStudent.value) || null
})

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
      echarts.init(pythonRef.value).setOption({
        series: [{ type: 'tree', data: pythonNodes, layout: 'radial', symbol: 'roundRect', symbolSize: 12 }]
      })
    }
    if (javaRef.value) {
      echarts.init(javaRef.value).setOption({
        series: [{ type: 'tree', data: javaNodes, layout: 'radial', symbol: 'roundRect', symbolSize: 12 }]
      })
    }
  })
})
</script>

<style scoped>
.admin-page { max-width: 1200px; }
</style>