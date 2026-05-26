<template>
  <el-container class="admin-layout">
    <!-- 左侧导航 -->
    <el-aside :width="isCollapse ? '64px' : '220px'" class="admin-aside">
      <div class="logo" v-show="!isCollapse">
        <div class="logo-icon">📚</div>
        <h2>码途智伴</h2>
        <p>教师管理平台</p>
      </div>
      <div class="header-right">
        <!-- 第一行：班级管理 -->
        <div class="header-row">
          <el-select v-model="selectedClass" @change="switchClass" size="small" style="width:160px" placeholder="选择班级">
            <el-option v-for="c in adminStore.classes" :key="c" :label="c" :value="c" />
          </el-select>
          <el-button size="small" @click="showAddClass = true" link>+ 新建</el-button>
        </div>
        <!-- 第二行：用户信息 -->
        <div class="header-row">
          <el-tag type="success" effect="dark" round size="small">v2.0</el-tag>
          <span class="header-user">{{ authStore.user }}</span>
          <el-button @click="handleLogout" type="danger" link size="small">退出</el-button>
        </div>
      </div>
      <!-- 新建班级对话框 -->
      <el-dialog v-model="showAddClass" title="新建班级" width="300px">
        <el-input v-model="newClassName" placeholder="班级名称" />
        <template #footer>
          <el-button @click="showAddClass = false">取消</el-button>
          <el-button type="primary" @click="addClass">确定</el-button>
        </template>
      </el-dialog>
      <div class="logo-mini" v-show="isCollapse">
        <span style="font-size:24px">📚</span>
      </div>
      <el-menu
        :collapse="isCollapse"
        :default-active="activeMenu"
        router
        background-color="transparent"
        text-color="#b8c7e0"
        active-text-color="#fff"
        class="side-menu"
      >
        <el-menu-item index="/admin/questions">
          <el-icon><Edit /></el-icon>
          <span>题库管理</span>
        </el-menu-item>
        <el-menu-item index="/admin/batch">
          <el-icon><Upload /></el-icon>
          <span>批量批改</span>
        </el-menu-item>
        <el-menu-item index="/admin/reports">
          <el-icon><DataAnalysis /></el-icon>
          <span>成绩查看</span>
        </el-menu-item>
        <el-menu-item index="/admin/dashboard">
          <el-icon><TrendCharts /></el-icon>
          <span>数据驾驶舱</span>
        </el-menu-item>
        <el-menu-item index="/admin/plagiarism">
          <el-icon><Search /></el-icon>
          <span>抄袭检测</span>
        </el-menu-item>
        <el-menu-item index="/admin/knowledge">
          <el-icon><Share /></el-icon>
          <span>知识图谱</span>
        </el-menu-item>
        <el-menu-item index="/admin/sandbox">
          <el-icon><Box /></el-icon>
          <span>沙箱测试</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 右侧内容 -->
    <el-container>
      <el-header class="admin-header">
        <div class="header-left">
          <el-button @click="isCollapse = !isCollapse" class="collapse-btn" link>
            <el-icon v-if="isCollapse"><Expand /></el-icon>
            <el-icon v-else><Fold /></el-icon>
          </el-button>
          <el-button @click="goStudent" class="back-btn">
            <el-icon><ArrowLeft /></el-icon>
            <span v-show="!isMobile">返回学生端</span>
          </el-button>
        </div>
        <div class="header-right">
          <el-tag type="success" effect="dark" round>v2.0</el-tag>
          <span class="header-title">教师管理平台</span>
        </div>
      </el-header>
      <el-main class="admin-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Expand, Fold } from '@element-plus/icons-vue'
import { adminStore } from '@/store/index.js'
import { authStore } from '@/store/auth.js'

const route = useRoute()
const router = useRouter()
const activeMenu = computed(() => route.path)

const selectedClass = ref(adminStore.currentClass)
const showAddClass = ref(false)
const newClassName = ref('')
const isCollapse = ref(false)
const isMobile = ref(window.innerWidth < 768)

window.addEventListener('resize', () => {
  isMobile.value = window.innerWidth < 768
  if (isMobile.value) isCollapse.value = true
})

const goStudent = () => {
  router.push('/')
}

const switchClass = (name) => {
  adminStore.switchClass(name)
  selectedClass.value = name
}

const addClass = () => {
  if (newClassName.value.trim()) {
    adminStore.addClass(newClassName.value.trim())
    selectedClass.value = newClassName.value.trim()
    adminStore.switchClass(newClassName.value.trim())
    newClassName.value = ''
    showAddClass.value = false
  }
}

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.admin-layout {
  height: 100vh;
  background: #f0f2f5;
}

.admin-aside {
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  overflow-y: auto;
  box-shadow: 4px 0 20px rgba(0, 0, 0, 0.15);
}

.logo {
  padding: 28px 20px 20px;
  text-align: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  margin-bottom: 8px;
}
.logo-icon {
  font-size: 36px;
  margin-bottom: 8px;
}
.logo h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 1px;
}
.logo p {
  margin: 4px 0 0;
  font-size: 11px;
  color: #7a8fb8;
  letter-spacing: 2px;
  text-transform: uppercase;
}

.side-menu {
  border-right: none;
}
.side-menu :deep(.el-menu-item) {
  margin: 4px 12px;
  border-radius: 10px;
  transition: all 0.3s ease;
}
.side-menu :deep(.el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.08) !important;
}
.side-menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.admin-header {
  background: #fff;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 56px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.back-btn {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  transition: all 0.3s ease;
}
.back-btn:hover {
  border-color: #667eea;
  color: #667eea;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.header-title {
  font-size: 14px;
  color: #888;
}

.admin-main {
  background: #f0f2f5;
  padding: 24px;
  overflow-y: auto;
}
.logo-mini {
  text-align: center;
  padding: 16px 0;
  border-bottom: 1px solid rgba(255,255,255,0.08);
  margin-bottom: 8px;
}

@media screen and (max-width: 768px) {
  .admin-aside {
    position: fixed;
    z-index: 100;
    height: 100vh;
  }
  .admin-main {
    padding: 12px !important;
  }
  .back-btn span {
    display: none;
  }
}
.header-right {
  display: flex;
  flex-direction: column;
  gap: 6px;
  align-items: flex-end;
}

.header-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-user {
  font-size: 13px;
  color: #666;
  font-weight: 500;
}
</style>