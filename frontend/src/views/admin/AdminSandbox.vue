<template>
  <div class="admin-page">
    <el-card>
      <template #header>🧪 代码沙箱测试</template>

      <el-form label-width="80px">
        <el-form-item label="语言">
          <el-select v-model="language" @change="changeLanguage">
            <el-option label="Python" value="python" />
            <el-option label="Java" value="java" />
          </el-select>
        </el-form-item>

        <el-form-item label="代码">
          <el-input v-model="code" type="textarea" :rows="10" />
        </el-form-item>

        <el-form-item label="超时">
          <el-slider v-model="timeout" :min="1" :max="30" show-input style="width:300px" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="execute" :loading="running">
            🧪 在沙箱中执行
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 执行结果 -->
      <el-card v-if="output !== null" class="output-card">
        <template #header>
          <span :style="{ color: success ? '#67c23a' : '#f56c6c', fontWeight: 'bold' }">
            {{ success ? '✅ 执行成功' : '❌ 执行失败' }}
          </span>
          <span style="float:right;color:#999;font-size:12px">
            耗时: {{ elapsed }}ms
          </span>
        </template>
        <div v-if="output" class="output-section">
          <h4>标准输出</h4>
          <pre class="output-block"><code>{{ output }}</code></pre>
        </div>
        <div v-if="error" class="output-section">
          <h4>错误输出</h4>
          <pre class="output-block error-block"><code>{{ error }}</code></pre>
        </div>
      </el-card>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { executeCode } from '@/api/index.js'

const language = ref('python')
const code = ref(`# 输入你的代码
print('Hello from 沙箱!')
for i in range(3):
    print(f'第{i+1}次执行')`)
const timeout = ref(5)
const running = ref(false)
const output = ref(null)
const error = ref(null)
const success = ref(false)
const elapsed = ref(0)

const pythonDefault = `# 输入你的代码
print('Hello from 沙箱!')
for i in range(3):
    print(f'第{i+1}次执行')`

const javaDefault = `public class Main {
    public static void main(String[] args) {
        System.out.println("Hello from 沙箱!");
        for (int i = 0; i < 3; i++) {
            System.out.println("第" + (i+1) + "次执行");
        }
    }
}`

const changeLanguage = (lang) => {
  if (lang === 'java') {
    code.value = javaDefault
  } else {
    code.value = pythonDefault
  }
}

const execute = async () => {
  running.value = true
  output.value = null
  error.value = null
  success.value = false
  elapsed.value = 0

  const startTime = Date.now()
  try {
    const res = await executeCode(code.value, language.value, timeout.value)
    elapsed.value = Date.now() - startTime
    success.value = res.data.success
    output.value = res.data.output || ''
    error.value = res.data.error || ''
  } catch (e) {
    elapsed.value = Date.now() - startTime
    success.value = false
    error.value = '请求失败: ' + (e.response?.data?.detail || e.message)
  } finally {
    running.value = false
  }
}
</script>

<style scoped>
.admin-page { max-width: 900px; }
.output-card { margin-top: 20px; }
.output-section { margin-bottom: 10px; }
.output-section h4 { margin: 5px 0; color: #666; }
.output-block {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 15px;
  border-radius: 4px;
  max-height: 300px;
  overflow: auto;
  font-size: 14px;
  white-space: pre-wrap;
}
.error-block {
  color: #f56c6c;
}
</style>