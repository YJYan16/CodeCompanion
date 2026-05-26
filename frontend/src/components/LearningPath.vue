<template>
  <div class="learning-path" v-if="steps.length > 0">
    <el-divider />
    <h3>🗺️ 个性化学习路径 <el-tag size="small" type="info" effect="plain">由AI生成</el-tag></h3>
    
    <el-steps :active="activeStep" align-center finish-status="success" class="path-steps">
      <el-step
        v-for="(step, index) in steps"
        :key="index"
        :title="`第${step.step}步`"
        :description="step.name"
      />
    </el-steps>
    
    <el-collapse class="path-detail">
      <el-collapse-item
        v-for="(step, index) in steps"
        :key="index"
        :title="`📖 ${step.step}. ${step.name}`"
        :name="index"
      >
        <p><strong>学习内容：</strong>{{ step.desc }}</p>
        <p><strong>推荐资源：</strong>{{ step.resource }}</p>
        <el-button size="small" type="primary" @click.stop="showCard(step)">
          开始学习
        </el-button>
      </el-collapse-item>
    </el-collapse>

    <!-- 知识卡片弹窗 -->
    <el-dialog v-model="dialogVisible" :title="'📚 ' + currentStep.name" width="600px">
      <div class="knowledge-card">
        <div class="card-section">
          <h4>📖 知识点讲解</h4>
          <p>{{ currentStep.desc }}</p>
        </div>
        <div class="card-section">
          <h4>💡 学习建议</h4>
          <p>{{ currentStep.resource }}</p>
        </div>
        <div class="card-section">
          <h4>✍️ 练习题</h4>
          <pre class="code-block-example">{{ getExampleCode(currentStep.name) }}</pre>
        </div>
        <div class="card-section">
          <h4>⚠️ 常见错误</h4>
          <p>{{ getCommonMistake(currentStep.name) }}</p>
        </div>
      </div>
      <template #footer>
        <el-button @click="dialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="startPractice(currentStep)">去练习</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  steps: { type: Array, default: () => [] },
  activeStep: { type: Number, default: 0 }
})
const emit = defineEmits(['start-step'])

const dialogVisible = ref(false)
const currentStep = ref({})

const getExampleCode = (name) => {
  const examples = {
    'Python基础语法': '# 函数定义\n# 注意：冒号和缩进\ndef find_max(numbers):\n    if not numbers:\n        return None\n    max_val = numbers[0]\n    for num in numbers:\n        if num > max_val:\n            max_val = num\n    return max_val',
    '变量初始化': '# 正确初始化\nmax_val = numbers[0]  # 用第一个元素\n# 不要用 max_val = 0',
    '安全遍历技巧': '# 安全遍历\nfor num in numbers:  # 直接遍历元素\n    print(num)\n\n# 需要索引时\nfor i in range(len(numbers)):\n    print(i, numbers[i])',
    '函数定义': '# 函数定义模板\ndef function_name(params):\n    """函数说明"""\n    # 处理逻辑\n    return result',
    'Java基础语法': 'public class Main {\n    public static int findMax(int[] numbers) {\n        if (numbers.length == 0) return -1;\n        int maxVal = numbers[0];\n        for (int num : numbers) {\n            if (num > maxVal) maxVal = num;\n        }\n        return maxVal;\n    }\n}',
    '基础知识巩固': '# 基础练习\ndef hello():\n    print("Hello, Python!")\n    return 0',
    '专项练习': '# 专项练习\n# 请根据前面的学习内容完成练习\ndef practice():\n    pass',
    '综合实践': '# 综合项目\n# 完成一个完整的函数\ndef complete_project(input_data):\n    # TODO: 实现完整逻辑\n    return None',
  }
  return examples[name] || '# 请根据知识点完成练习\ndef practice():\n    pass'
}

const getCommonMistake = (name) => {
  const mistakes = {
    'Python基础语法': '忘记冒号(:)、缩进不一致、混用Tab和空格',
    '变量初始化': '用0初始化最大值，导致全负数列表出错',
    '安全遍历技巧': '使用 range(len) 时访问 i+1 导致索引越界',
    '函数定义': '忘记写 return 语句，函数返回 None',
    'Java基础语法': '忘记分号(;)、类名与文件名不一致',
    '基础知识巩固': '基础语法不熟练，建议多加练习',
    '专项练习': '针对薄弱环节加强训练',
    '综合实践': '将多个知识点融会贯通',
  }
  return mistakes[name] || '请仔细阅读知识点讲解，避免类似错误'
}

const showCard = (step) => {
  currentStep.value = step
  dialogVisible.value = true
}

const startPractice = (step) => {
  dialogVisible.value = false
  emit('start-step', step)
}
</script>

<style scoped>
.learning-path {
  margin-top: 20px;
}
.path-steps {
  margin: 20px 0;
}
.path-detail {
  margin-top: 10px;
}
.knowledge-card {
  max-height: 60vh;
  overflow-y: auto;
}
.card-section {
  margin-bottom: 20px;
  padding: 12px;
  background: #f8f9fc;
  border-radius: 8px;
}
.card-section h4 {
  margin: 0 0 8px;
  color: #333;
}
.code-block-example {
  background: #1a1a2e;
  color: #e0e0e0;
  padding: 12px;
  border-radius: 8px;
  font-family: 'Consolas', monospace;
  font-size: 13px;
  overflow-x: auto;
  white-space: pre-wrap;
}
</style>