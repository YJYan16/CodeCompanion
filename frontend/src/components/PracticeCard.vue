<template>
  <div>
    <h3>🎯 推荐练习</h3>
    <div v-for="(p, i) in practices" :key="i" style="padding:10px;margin:5px;background:#fff;border:1px solid #ddd;border-radius:6px;cursor:pointer" @click="$emit('start-practice', p)">
      <strong>练习{{ i+1 }}:</strong> {{ p.description }}
      <button style="margin-left:10px;padding:5px 15px;background:#409eff;color:#fff;border:none;border-radius:4px;cursor:pointer">开始</button>
    </div>
  </div>
</template>

<script setup>
defineProps({ practices: Array })
defineEmits(['start-practice'])
</script>