<template>
  <div class="main-layout">
    <el-container>
      <!-- 头部导航 -->
      <el-header class="header">
        <div class="header-content">
          <div class="logo">
            <router-link to="/">
              <h2>BBS论坛</h2>
            </router-link>
          </div>

          <div class="search-bar">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索帖子、用户..."
              @keyup.enter="handleSearch"
            >
              <template #suffix>
                <el-icon @click="handleSearch"><Search /></el-icon>
              </template>
            </el-input>
          </div>

          <div class="nav-menu">
            <router-link to="/" class="nav-item">首页</router-link>

            <template v-if="userStore.isLoggedIn">
              <el-dropdown @command="handleCommand">
                <span class="user-info">
                  <el-avatar :size="32" :src="userStore.user?.avatar" />
                  <span>{{ userStore.user?.username }}</span>
                </span>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                    <el-dropdown-item command="messages">
                      <span>私信</span>
                      <el-badge
                        v-if="messageCount > 0"
                        :value="messageCount"
                        class="message-badge"
                      />
                    </el-dropdown-item>
                    <el-dropdown-item command="notifications">
                      <span>通知</span>
                      <el-badge
                        v-if="notificationCount > 0"
                        :value="notificationCount"
                        class="message-badge"
                      />
                    </el-dropdown-item>
                    <el-dropdown-item command="favorites">收藏</el-dropdown-item>
                    <el-dropdown-item command="follows">关注</el-dropdown-item>
                    <el-dropdown-item
                      v-if="userStore.user?.role === 'admin'"
                      command="admin"
                      divided
                    >
                      管理后台
                    </el-dropdown-item>
                    <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>

              <el-button type="primary" @click="router.push('/post/create')">
                发帖
              </el-button>
            </template>

            <template v-else>
              <router-link to="/login" class="nav-item">登录</router-link>
              <el-button type="primary" @click="router.push('/register')">
                注册
              </el-button>
            </template>
          </div>
        </div>
      </el-header>

      <!-- 主体内容 -->
      <el-main class="main-content">
        <div class="container">
          <router-view />
        </div>
      </el-main>

      <!-- 页脚 -->
      <el-footer class="footer">
        <div class="footer-content">
          <p>&copy; 2024 BBS论坛. All rights reserved.</p>
        </div>
      </el-footer>
    </el-container>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { Search } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import api from '@/api'

const router = useRouter()
const userStore = useUserStore()

const searchKeyword = ref('')
const messageCount = ref(0)
const notificationCount = ref(0)
let pollingTimer = null

onMounted(async () => {
  if (userStore.isLoggedIn) {
    await loadUnreadCounts()
    startPolling()
  }
})

onUnmounted(() => {
  stopPolling()
})

async function loadUnreadCounts() {
  try {
    // 加载通知未读数
    const notificationData = await api.notifications.getUnreadCount()
    notificationCount.value = notificationData.count

    // 加载私信未读数
    const messageData = await api.messages.getUnreadCount()
    messageCount.value = messageData.count
  } catch (error) {
    console.error('加载未读数失败:', error)
  }
}

function startPolling() {
  // 每30秒刷新一次未读数
  pollingTimer = setInterval(() => {
    loadUnreadCounts()
  }, 30000)
}

function stopPolling() {
  if (pollingTimer) {
    clearInterval(pollingTimer)
    pollingTimer = null
  }
}

function handleSearch() {
  if (searchKeyword.value.trim()) {
    router.push({
      path: '/search',
      query: { keyword: searchKeyword.value }
    })
  }
}

async function handleCommand(command) {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'messages':
      router.push('/messages')
      break
    case 'notifications':
      router.push('/notifications')
      break
    case 'favorites':
      router.push('/favorites')
      break
    case 'likes':
      router.push('/likes')
      break
    case 'follows':
      router.push('/follows')
      break
    case 'admin':
      router.push('/admin')
      break
    case 'logout':
      userStore.logout()
      ElMessage.success('退出登录成功')
      router.push('/')
      break
  }
}
</script>

<style lang="scss" scoped>
.main-layout {
  min-height: 100vh;
  background: #f5f5f5;
}

.header {
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 0;

  .header-content {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 60px;
    padding: 0 20px;
    max-width: 1200px;
    margin: 0 auto;

    .logo {
      h2 {
        color: #409eff;
        margin: 0;
        cursor: pointer;
      }
    }

    .search-bar {
      flex: 1;
      max-width: 400px;
      margin: 0 40px;
    }

    .nav-menu {
      display: flex;
      align-items: center;
      gap: 20px;

      .nav-item {
        color: #333;
        font-size: 14px;
        cursor: pointer;

        &:hover {
          color: #409eff;
        }
      }

      .user-info {
        display: flex;
        align-items: center;
        gap: 8px;
        cursor: pointer;
        padding: 8px 12px;
        border-radius: 4px;

        &:hover {
          background: #f5f5f5;
        }
      }

      .message-badge {
        margin-left: 8px;
      }
    }
  }
}

.main-content {
  padding: 20px;

  .container {
    max-width: 1200px;
    margin: 0 auto;
  }
}

.footer {
  background: #fff;
  border-top: 1px solid #eee;
  text-align: center;
  padding: 20px;
  margin-top: 40px;

  .footer-content {
    max-width: 1200px;
    margin: 0 auto;
  }
}
</style>
