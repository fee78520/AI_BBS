/**
 * BBS论坛系统 - 前端应用入口
 * 本文件负责：
 * 1. 创建Vue应用实例
 * 2. 配置Pinia状态管理
 * 3. 配置Vue Router路由
 * 4. 注册Element Plus UI组件库
 * 5. 注册Element Plus图标组件
 * 6. 挂载应用到DOM
 */
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'  // Element Plus样式文件
import * as ElementPlusIconsVue from '@element-plus/icons-vue'  // Element Plus图标库
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'  // Element Plus中文语言包

import App from './App.vue'  // 根组件
import router from './router'  // 路由配置
import './assets/styles/main.scss'  // 全局样式

// ========== 创建Vue应用 ==========
const app = createApp(App)

// ========== 创建Pinia状态管理 ==========
const pinia = createPinia()

// ========== 注册所有Element Plus图标 ==========
// 遍历ElementPlusIconsVue中的所有图标组件并注册到Vue应用
// 这样可以在任何Vue组件中直接使用图标组件
// 例如：<el-icon><User /></el-icon>
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// ========== 安装插件 ==========
app.use(pinia)  // 安装Pinia状态管理
app.use(router)  // 安装Vue Router路由
app.use(ElementPlus, { locale: zhCn })  // 安装Element Plus并设置中文语言

// ========== 挂载应用到DOM ==========
// 将Vue应用挂载到HTML中id为"app"的元素上
app.mount('#app')

