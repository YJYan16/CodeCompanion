<template>
  <div class="weak-section" v-if="knowledgePoints && knowledgePoints.length > 0">
    <el-divider />
    <h3>📚 薄弱知识点讲解 <el-tag size="small" type="info" effect="plain">由AI生成</el-tag></h3>
    <el-collapse accordion>
      <el-collapse-item v-for="(kp, index) in knowledgePoints" :key="index" :title="`${index + 1}. ${kp.name}`">
        <div class="kp-detail">
          <p><strong>📖 讲解：</strong></p>
          <p v-html="formatText(kp.explanation)"></p>
          <p v-if="kp.common_mistake"><strong>⚠️ 常见错误：</strong>{{ kp.common_mistake }}</p>
        </div>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script setup>
defineProps({
  knowledgePoints: { type: Array, default: () => [] }
})
const formatText = (text) => (text || '').replace(/\n/g, '<br>')
</script>

<style scoped>
.weak-section {
  margin-top: 20px;
}
.kp-detail {
  padding: 10px 20px;
  line-height: 1.8;
}
</style>