// frontend/src/main.js
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import {
  ArrowLeft,
  Box,
  DataAnalysis,
  Document,
  Edit,
  Expand,
  Fold,
  Search,
  Share,
  TrendCharts,
  Upload,
  User,
} from '@element-plus/icons-vue'
import { setupErrorReporter } from '@/utils/errorReporter.js'

const app = createApp(App)

const icons = {
  ArrowLeft,
  Box,
  DataAnalysis,
  Document,
  Edit,
  Expand,
  Fold,
  Search,
  Share,
  TrendCharts,
  Upload,
  User,
}

for (const [key, component] of Object.entries(icons)) {
  app.component(key, component)
}

app.use(router)
app.use(ElementPlus)
setupErrorReporter(app)
app.mount('#app')
