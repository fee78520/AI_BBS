<template>
  <div class="user-profile">
    <el-card v-loading="loading">
      <template v-if="user">
        <div class="user-header">
          <el-avatar :size="100" :src="user.avatar" />
          <div class="user-info">
            <h2>{{ user.username }}</h2>
            <p v-if="user.nickname" class="nickname">{{ user.nickname }}</p>
            <div class="stats">
              <span>帖子: {{ user.post_count || 0 }}</span>
              <span>粉丝: {{ user.follower_count || 0 }}</span>
              <span>关注: {{ user.following_count || 0 }}</span>
            </div>
            <div v-if="isCurrentUser" class="actions">
              <el-button @click="router.push('/profile')">编辑资料</el-button>
            </div>
            <div v-else class="actions">
              <el-button
                v-if="isFollowing"
                type="primary"
                @click="handleUnfollow"
              >
                已关注
              </el-button>
              <el-button v-else type="primary" @click="handleFollow">
                关注
              </el-button>
              <el-button @click="showSendMessageDialog">
                <el-icon><ChatDotRound /></el-icon>
                发私信
              </el-button>
            </div>
          </div>
        </div>

        <el-tabs v-model="activeTab" @tab-change="handleTabChange">
          <el-tab-pane label="帖子" name="posts">
            <el-empty v-if="posts.length === 0" description="暂无帖子" />
            <div v-else class="post-list">
              <div v-for="post in posts" :key="post.id" class="post-item">
                <router-link :to="`/post/${post.id}`" class="post-title">
                  {{ post.title }}
                </router-link>
                <div class="post-meta">
                  <span>{{ formatDate(post.created_at) }}</span>
                  <span>浏览 {{ post.view_count }}</span>
                  <span>点赞 {{ post.like_count }}</span>
                  <span>评论 {{ post.comment_count }}</span>
                </div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </template>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import { ChatDotRound } from '@element-plus/icons-vue'
import api from '@/api'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const user = ref(null)
const loading = ref(false)
const posts = ref([])
const isFollowing = ref(false)
const activeTab = ref('posts')

const userId = computed(() => parseInt(route.params.id))
const isCurrentUser = computed(() => userStore.user?.id === userId.value)

onMounted(async () => {
  await loadUser()
  await loadPosts()
  await checkFollowStatus()
})

async function loadUser() {
  loading.value = true
  try {
    user.value = await api.users.getById(userId.value)
  } catch (error) {
    console.error('加载用户信息失败:', error)
    ElMessage.error('加载用户信息失败')
  } finally {
    loading.value = false
  }
}

async function loadPosts() {
  try {
    const response = await api.users.getUserPosts(userId.value, {
      page: 1,
      page_size: 20
    })
    posts.value = response.items || []
  } catch (error) {
    console.error('加载用户帖子失败:', error)
  }
}

async function checkFollowStatus() {
  if (isCurrentUser.value) return

  try {
    const response = await api.follows.getFollowing({ page: 1, page_size: 100 })
    isFollowing.value = response.items?.some(item => item.id === userId.value) || false
  } catch (error) {
    // 未登录或错误时忽略
  }
}

async function handleFollow() {
  try {
    await api.follows.follow({ followed_id: userId.value })
    isFollowing.value = true
    ElMessage.success('关注成功')
    // 更新粉丝数
    if (user.value) {
      user.value.follower_count = (user.value.follower_count || 0) + 1
    }
  } catch (error) {
    console.error('关注失败:', error)
    ElMessage.error('关注失败')
  }
}

async function handleUnfollow() {
  try {
    await api.follows.unfollow(userId.value)
    isFollowing.value = false
    ElMessage.success('已取消关注')
    // 更新粉丝数
    if (user.value) {
      user.value.follower_count = Math.max((user.value.follower_count || 0) - 1, 0)
    }
  } catch (error) {
    console.error('取消关注失败:', error)
    ElMessage.error('取消关注失败')
  }
}

function handleTabChange() {
  // 可以在这里切换不同类型的内容
}

function showSendMessageDialog() {
  // 跳转到私信页面，并传递接收人信息
  router.push({
    path: '/messages',
    query: {
      to_user_id: userId.value,
      to_username: user.value?.username
    }
  })
}

function formatDate(dateStr) {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}
</script>

<style lang="scss" scoped>
.user-profile {
  max-width: 800px;
  margin: 0 auto;

  .user-header {
    display: flex;
    align-items: flex-start;
    gap: 24px;
    margin-bottom: 30px;

    .user-info {
      flex: 1;

      h2 {
        margin: 0 0 8px 0;
        font-size: 24px;
      }

      .nickname {
        color: #666;
        margin: 0 0 16px 0;
      }

      .stats {
        display: flex;
        gap: 24px;
        color: #666;
        margin-bottom: 16px;
      }

      .actions {
        display: flex;
        gap: 12px;
      }
    }
  }

  .post-list {
    .post-item {
      padding: 16px 0;
      border-bottom: 1px solid #eee;

      &:last-child {
        border-bottom: none;
      }

      .post-title {
        display: block;
        font-size: 16px;
        font-weight: 500;
        color: #333;
        margin-bottom: 8px;
        text-decoration: none;

        &:hover {
          color: #409eff;
        }
      }

      .post-meta {
        font-size: 12px;
        color: #999;

        span {
          margin-right: 16px;
        }
      }
    }
  }
}
</style>
