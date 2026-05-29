<template>
  <div class="skeleton-container">
    <el-card class="skeleton-card">
      <div class="skeleton-header">
        <div class="skeleton-title skeleton-animated"></div>
        <div class="skeleton-subtitle skeleton-animated"></div>
      </div>
      
      <div class="skeleton-form">
        <div class="skeleton-form-item">
          <div class="skeleton-label skeleton-animated"></div>
          <div class="skeleton-select skeleton-animated"></div>
        </div>
        <div class="skeleton-form-item">
          <div class="skeleton-label skeleton-animated"></div>
          <div class="skeleton-select skeleton-animated"></div>
        </div>
        <div class="skeleton-form-item">
          <div class="skeleton-label skeleton-animated"></div>
          <div class="skeleton-editor skeleton-animated"></div>
        </div>
        <div class="skeleton-form-item">
          <div class="skeleton-button skeleton-animated"></div>
        </div>
      </div>
    </el-card>
    
    <el-card class="skeleton-card">
      <div class="skeleton-header">
        <div class="skeleton-title skeleton-animated"></div>
      </div>
      <div class="skeleton-content">
        <div class="skeleton-line skeleton-animated"></div>
        <div class="skeleton-line skeleton-animated"></div>
        <div class="skeleton-line skeleton-animated"></div>
        <div class="skeleton-line skeleton-animated"></div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
// 骨架屏组件
</script>

<style scoped>
.skeleton-container {
  display: flex;
  gap: 20px;
  padding: 20px;
}

.skeleton-card {
  flex: 1;
  min-height: 400px;
}

.skeleton-header {
  margin-bottom: 20px;
}

.skeleton-title {
  width: 200px;
  height: 24px;
  background: #f2f2f2;
  border-radius: 4px;
  margin-bottom: 8px;
}

.skeleton-subtitle {
  width: 150px;
  height: 18px;
  background: #f2f2f2;
  border-radius: 4px;
}

.skeleton-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.skeleton-form-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.skeleton-label {
  width: 60px;
  height: 16px;
  background: #f2f2f2;
  border-radius: 4px;
}

.skeleton-select {
  width: 100%;
  height: 40px;
  background: #f2f2f2;
  border-radius: 4px;
}

.skeleton-editor {
  width: 100%;
  height: 300px;
  background: #f2f2f2;
  border-radius: 4px;
}

.skeleton-button {
  width: 120px;
  height: 40px;
  background: #f2f2f2;
  border-radius: 4px;
}

.skeleton-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.skeleton-line {
  width: 100%;
  height: 16px;
  background: #f2f2f2;
  border-radius: 4px;
}

.skeleton-line:nth-child(2) {
  width: 80%;
}

.skeleton-line:nth-child(3) {
  width: 60%;
}

.skeleton-line:nth-child(4) {
  width: 90%;
}

.skeleton-animated {
  animation: skeleton-loading 1.5s ease-in-out infinite;
}

@keyframes skeleton-loading {
  0% {
    opacity: 0.6;
  }
  50% {
    opacity: 1;
  }
  100% {
    opacity: 0.6;
  }
}

@media (max-width: 768px) {
  .skeleton-container {
    flex-direction: column;
  }
}
</style>