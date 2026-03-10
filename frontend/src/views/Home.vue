<template>
  <div class="home">
    <el-row :gutter="20">
      <!-- 左侧：帖子列表 -->
      <el-col :span="16">
        <div class="post-list">
          <el-tabs v-model="activeTab" @tab-change="handleTabChange">
            <el-tab-pane label="最新" name="latest" />
            <el-tab-pane label="热门" name="hot" />
            <el-tab-pane label="精华" name="essence" />
            <el-tab-pane label="公告" name="announcement" />
          </el-tabs>

          <div v-loading="loading" class="posts">
            <div v-for="post in posts" :key="post.id" class="post-item">
              <div class="post-info" @click="router.push(`/post/${post.id}`)">
                <div class="post-title">
                  <el-tag v-if="post.post_type === 'top'" type="danger" size="small">
                    置顶
                  </el-tag>
                  <el-tag v-if="post.post_type === 'essence'" type="success" size="small">
                    精华
                  </el-tag>
                  <el-tag v-if="post.post_type === 'announcement'" type="warning" size="small">
                    公告
                  </el-tag>
                  <el-tag v-if="post.is_hidden" type="info" size="small">
                    已隐藏
                  </el-tag>
                  <span class="title">{{ post.title }}</span>
                </div>
                <div class="post-meta">
                  <span class="author" @click.stop="goToUser(post.author?.id)">
                    {{ post.author?.username }}
                  </span>
                  <span class="category">{{ post.category?.name }}</span>
                  <span class="time">{{ formatTime(post.created_at) }}</span>
                </div>
                <div class="post-stats">
                  <el-icon><View /></el-icon>
                  <span>{{ post.view_count }}</span>
                  <el-icon><ChatDotRound /></el-icon>
                  <span>{{ post.comment_count }}</span>
                  <el-icon><Star /></el-icon>
                  <span>{{ post.like_count }}</span>
                </div>
              </div>
            </div>

            <el-empty v-if="!loading && posts.length === 0" description="暂无帖子" />

            <div v-if="total > 0" class="pagination">
              <el-pagination
                v-model:current-page="currentPage"
                v-model:page-size="pageSize"
                :total="total"
                :page-sizes="[10, 20, 30, 50]"
                layout="total, sizes, prev, pager, next, jumper"
                @size-change="loadPosts"
                @current-change="loadPosts"
              />
            </div>
          </div>
        </div>
      </el-col>

      <!-- 右侧：侧边栏 -->
      <el-col :span="8">
        <div class="sidebar">
          <!-- 版块列表 -->
          <div class="sidebar-section">
            <h3>版块</h3>
            <div v-loading="categoriesLoading" class="category-list">
              <div
                v-for="category in categories"
                :key="category.id"
                class="category-item"
                @click="router.push(`/category/${category.id}`)"
              >
                <el-icon><Folder /></el-icon>
                <span>{{ category.name }}</span>
                <span class="count">{{ category.post_count }}</span>
              </div>
            </div>
          </div>

          <!-- 热门用户 -->
          <div class="sidebar-section">
            <h3>热门用户</h3>
            <div v-loading="usersLoading" class="user-list">
              <div
                v-for="user in hotUsers"
                :key="user.id"
                class="user-item"
                @click="router.push(`/user/${user.id}`)"
              >
                <el-avatar :size="40" :src="user.avatar" />
                <div class="user-info">
                  <div class="username">{{ user.username }}</div>
                  <div class="level">Lv.{{ user.level }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { View, ChatDotRound, Star, Folder } from '@element-plus/icons-vue'
import { formatRelativeTime as formatTime } from '@/utils/time'
import api from '@/api'

const router = useRouter()

const activeTab = ref('latest')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const posts = ref([])
const categories = ref([])
const hotUsers = ref([])

const loading = ref(false)
const categoriesLoading = ref(false)
const usersLoading = ref(false)

onMounted(() => {
  loadPosts()
  loadCategories()
  loadHotUsers()
})

async function loadPosts() {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value
    }

    if (activeTab.value === 'hot') {
      const data = await api.posts.getHot(params)
      posts.value = data
      total.value = data.length
    } else {
      if (activeTab.value === 'essence') {
        params.post_type = 'essence'
      } else if (activeTab.value === 'announcement') {
        params.post_type = 'announcement'
      }
      const data = await api.posts.getList(params)
      posts.value = data.items
      total.value = data.total
    }
  } catch (error) {
    console.error('加载帖子失败:', error)
  } finally {
    loading.value = false
  }
}

async function loadCategories() {
  categoriesLoading.value = true
  try {
    categories.value = await api.categories.getList()
  } catch (error) {
    console.error('加载版块失败:', error)
  } finally {
    categoriesLoading.value = false
  }
}

async function loadHotUsers() {
  usersLoading.value = true
  try {
    const data = await api.users.getHotUsers({ limit: 10 })
    hotUsers.value = data
  } catch (error) {
    console.error('加载热门用户失败:', error)
    // 静默处理错误，不显示错误提示
    hotUsers.value = []
  } finally {
    usersLoading.value = false
  }
}

function handleTabChange() {
  currentPage.value = 1
  loadPosts()
}

function goToUser(userId) {
  router.push(`/user/${userId}`)
}
</script>

<style lang="scss" scoped>
.home {
  .post-list {
    background: #fff;
    border-radius: 4px;
    padding: 20px;

    .posts {
      .post-item {
        padding: 16px 0;
        border-bottom: 1px solid #eee;

        &:last-child {
          border-bottom: none;
        }

        .post-info {
          cursor: pointer;

          &:hover {
            .post-title {
              .title {
                color: #409eff;
              }
            }
          }

          .post-title {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 8px;

            .title {
              font-size: 16px;
              font-weight: 500;
              color: #333;
            }
          }

          .post-meta {
            display: flex;
            align-items: center;
            gap: 16px;
            color: #999;
            font-size: 13px;
            margin-bottom: 8px;
          }

          .post-stats {
            display: flex;
            align-items: center;
            gap: 16px;
            color: #999;
            font-size: 13px;

            .el-icon {
              vertical-align: middle;
            }
          }
        }
      }

      .pagination {
        margin-top: 20px;
        text-align: center;
      }
    }
  }

  .sidebar {
    .sidebar-section {
      background: #fff;
      border-radius: 4px;
      padding: 20px;
      margin-bottom: 20px;

      h3 {
        font-size: 16px;
        margin-bottom: 16px;
        padding-bottom: 8px;
        border-bottom: 1px solid #eee;
      }

      .category-list {
        .category-item {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 0;
          cursor: pointer;

          &:hover {
            color: #409eff;
          }

          .count {
            margin-left: auto;
            color: #999;
            font-size: 13px;
          }
        }
      }

      .user-list {
        .user-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 10px 0;
          cursor: pointer;

          &:hover {
            background: #f5f5f5;
          }

          .user-info {
            .username {
              font-size: 14px;
              color: #333;
            }

            .level {
              font-size: 12px;
              color: #999;
              margin-top: 4px;
            }
          }
        }
      }
    }
  }
}
</style>
