<template>
  <div class="admin-layout">
    <el-container>
      <el-aside width="200px">
        <div class="logo">
          <h2>管理后台</h2>
        </div>
        <el-menu
          :default-active="activeMenu"
          router
          class="admin-menu"
        >
          <el-menu-item index="/admin">
            <el-icon><DataAnalysis /></el-icon>
            <span>数据统计</span>
          </el-menu-item>
          <el-menu-item index="/admin/users">
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </el-menu-item>
          <el-menu-item index="/admin/posts">
            <el-icon><Document /></el-icon>
            <span>帖子管理</span>
          </el-menu-item>
          <el-menu-item index="/admin/categories">
            <el-icon><Folder /></el-icon>
            <span>版块管理</span>
          </el-menu-item>
          <el-menu-item index="/admin/reports">
            <el-icon><Warning /></el-icon>
            <span>举报管理</span>
          </el-menu-item>
          <el-menu-item index="/admin/trash">
            <el-icon><Delete /></el-icon>
            <span>回收站</span>
          </el-menu-item>
          <el-menu-item index="/admin/settings">
            <el-icon><Setting /></el-icon>
            <span>系统设置</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <el-container>
        <el-header>
          <div class="header-content">
            <h3>{{ currentTitle }}</h3>
            <el-button @click="router.push('/')">返回前台</el-button>
          </div>
        </el-header>

        <el-main>
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { DataAnalysis, User, Document, Folder, Bell, Warning, Setting, Delete } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

const activeMenu = computed(() => route.path)
const currentTitle = computed(() => route.meta?.title || '管理后台')
</script>

<style lang="scss" scoped>
.admin-layout {
  height: 100vh;

  .el-container {
    height: 100%;
  }

  .el-aside {
    background: #304156;
    color: #fff;

    .logo {
      height: 60px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);

      h2 {
        color: #fff;
        font-size: 18px;
        margin: 0;
      }
    }

    .admin-menu {
      border: none;
      background: #304156;
    }
  }

  .el-header {
    background: #fff;
    border-bottom: 1px solid #eee;
    padding: 0 20px;

    .header-content {
      display: flex;
      align-items: center;
      justify-content: space-between;
      height: 60px;

      h3 {
        margin: 0;
      }
    }
  }

  .el-main {
    background: #f0f2f5;
  }
}
</style>
