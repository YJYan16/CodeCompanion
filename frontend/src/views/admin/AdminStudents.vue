<template>
  <div class="admin-page">
    <el-card>
      <template #header><span>👥 学生管理</span></template>
      <el-table :data="adminStore.students" stripe>
        <el-table-column prop="userId" label="学号" width="120" />
        <el-table-column prop="name" label="姓名" width="120" />
        <el-table-column prop="class" label="班级" width="150" />
        <el-table-column label="操作">
          <template #default="{ row }">
            <el-select v-model="row.class" @change="adminStore.updateStudentClass(row.userId, row.class)" size="small" style="width:150px">
              <el-option v-for="c in adminStore.classes" :key="c" :label="c" :value="c" />
            </el-select>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { adminStore } from '@/store/index.js'
</script>