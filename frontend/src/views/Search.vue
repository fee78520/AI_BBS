<template>
  <div class="search-page">
    <!-- 搜索输入框 -->
    <el-card class="search-input-card">
      <div class="search-box">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索帖子、用户..."
          size="large"
          clearable
          @keyup.enter="handleSearch"
        >
          <template #append>
            <el-button type="primary" @click="handleSearch" :loading="loading">
              搜索
            </el-button>
          </template>
        </el-input>
      </div>
      
      <!-- 搜索类型和筛选 -->
      <div class="search-filters">
        <el-radio-group v-model="searchType" @change="handleSearch">
          <el-radio-button value="all">全部</el-radio-button>
          <el-radio-button value="posts">帖子</el-radio-button>
          <el-radio-button value="users">用户</el-radio-button>
        </el-radio-group>
        
        <el-select
          v-model="sortBy"
          placeholder="排序方式"
          @change="handleSearch"
          style="width: 150px"
        >
          <el-option label="最新" value="created_at" />
          <el-option label="最热" value="view_count" />
          <el-option label="回复最多" value="comment_count" />
        </el-select>
      </div>
    </el-card>

    <!-- 搜索结果 -->
    <el-card v-if="hasSearched" v-loading="loading" class="search-results">
      <!-- 结果统计 -->
      <div class="result-header">
        <span class="result-count">
          搜索 "{{ currentKeyword }}" 共找到 {{ total }} 条结果
        </span>
      </div>

      <!-- 帖子结果 -->
      <div v-if="searchType === 'all' || searchType === 'posts'" class="result-section">
        <div v-if="searchResults.posts.length > 0">
          <h3 class="section-title">
            <el-icon><Document /></el-icon>
            帖子 ({{ searchResults.posts.length }})
          </h3>
          <div class="post-list">
            <div
              v-for="post in searchResults.posts"
              :key="post.id"
              class="post-item"
              @click="router.push(`/post/${post.id}`)"
            >
              <div class="post-title">{{ post.title }}</div>
              <div class="post-meta">
                <span class="author">{{ post.author?.username }}</span>
                <span class="category">{{ post.category?.name }}</span>
                <span class="views">{{ post.view_count }} 浏览</span>
                <span class="comments">{{ post.comment_count }} 回复</span>
                <span class="time">{{ formatDateTime(post.created_at) }}</span>
              </div>
              <div v-if="post.content" class="post-preview">
                {{ post.content.slice(0, 150) }}...
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 用户结果 -->
      <div v-if="searchType === 'all' || searchType === 'users'" class="result-section">
        <div v-if="searchResults.users.length > 0">
          <h3 class="section-title">
            <el-icon><User /></el-icon>
            用户 ({{ searchResults.users.length }})
          </h3>
          <div class="user-list">
            <div
              v-for="user in searchResults.users"
              :key="user.id"
              class="user-item"
              @click="router.push(`/user/${user.id}`)"
            >
              <el-avatar :size="50" :src="user.avatar" />
              <div class="user-info">
                <div class="username">{{ user.username }}</div>
                <div class="user-meta">
                  <span v-if="user.bio" class="bio">{{ user.bio }}</span>
                  <span v-else class="bio">暂无简介</span>
                </div>
              </div>
              <el-button
                type="primary"
                size="small"
                plain
                @click.stop="handleFollow(user.id)"
              >
                关注
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 无结果 -->
      <el-empty
        v-if="
          searchResults.posts.length === 0 &&
          searchResults.users.length === 0 &&
          !loading
        "
        description="未找到相关结果"
      />

      <!-- 分页 -->
      <div
        v-if="total > 0"
        class="pagination"
      >
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="handleSearch"
          @size-change="handleSearch"
        />
      </div>
    </el-card>

    <!-- 首次访问提示 -->
    <el-card v-else class="welcome-card">
      <el-empty description="输入关键词开始搜索" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Document, User } from '@element-plus/icons-vue'
import { formatDateTime } from '@/utils/time'
import api from '@/api'

const router = useRouter()
const route = useRoute()

const searchKeyword = ref('')
const currentKeyword = ref('')
const searchType = ref('all')
const sortBy = ref('created_at')
const searchResults = ref({ posts: [], users: [] })
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const hasSearched = ref(false)

// 执行搜索
async function handleSearch() {
  const keyword = searchKeyword.value.trim()
  if (!keyword) {
    ElMessage.warning('请输入搜索关键词')
    return
  }

  loading.value = true
  currentKeyword.value = keyword
  hasSearched.value = true

  try {
    const res = await api.search.search({
      keyword,
      search_type: searchType.value,
      sort_by: sortBy.value,
      sort_order: 'desc',
      page: currentPage.value,
      page_size: pageSize.value
    })

    searchResults.value = res
    total.value = res.total
  } catch (error) {
    console.error('搜索失败:', error)
    ElMessage.error(error.response?.data?.detail || '搜索失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 关注用户
async function handleFollow(userId) {
  try {
    await api.follows.toggle(userId)
    ElMessage.success('关注成功')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  }
}

// 监听路由参数变化
watch(
  () => route.query.keyword,
  (keyword) => {
    if (keyword) {
      searchKeyword.value = keyword
      handleSearch()
    }
  },
  { immediate: true }
)

onMounted(() => {
  // 初始化时检查路由参数
  if (route.query.keyword) {
    searchKeyword.value = route.query.keyword
    handleSearch()
  }
})
</script>

<style lang="scss" scoped>
.search-page {
  max-width: 1000px;
  margin: 20px auto;
  padding: 0 20px;

  .search-input-card {
    margin-bottom: 20px;

    .search-box {
      margin-bottom: 15px;
    }

    .search-filters {
      display: flex;
      gap: 15px;
      align-items: center;
    }
  }

  .search-results {
    min-height: 400px;

    .result-header {
      padding: 10px 0;
      border-bottom: 1px solid #eee;
      margin-bottom: 20px;

      .result-count {
        color: #666;
        font-size: 14px;
      }
    }

    .result-section {
      margin-bottom: 30px;

      .section-title {
        font-size: 16px;
        font-weight: 600;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        gap: 8px;

        .el-icon {
          color: #409eff;
        }
      }
    }

    .post-list {
      .post-item {
        padding: 15px;
        border-bottom: 1px solid #f0f0f0;
        cursor: pointer;
        transition: background-color 0.2s;

        &:hover {
          background-color: #f9f9f9;
        }

        .post-title {
          font-size: 16px;
          font-weight: 500;
          color: #303133;
          margin-bottom: 8px;
        }

        .post-meta {
          display: flex;
          gap: 15px;
          color: #909399;
          font-size: 12px;
          margin-bottom: 8px;

          .author {
            color: #409eff;
          }
        }

        .post-preview {
          color: #606266;
          font-size: 14px;
          line-height: 1.6;
        }
      }
    }

    .user-list {
      display: flex;
      flex-direction: column;
      gap: 10px;

      .user-item {
        display: flex;
        align-items: center;
        padding: 15px;
        border: 1px solid #f0f0f0;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s;

        &:hover {
          border-color: #409eff;
          background-color: #f0f9ff;
        }

        .user-info {
          flex: 1;
          margin-left: 15px;
          margin-right: 15px;

          .username {
            font-size: 15px;
            font-weight: 500;
            color: #303133;
            margin-bottom: 5px;
          }

          .user-meta {
            .bio {
              font-size: 13px;
              color: #909399;
            }
          }
        }
      }
    }

    .pagination {
      display: flex;
      justify-content: center;
      margin-top: 30px;
      padding-top: 20px;
      border-top: 1px solid #eee;
    }
  }

  .welcome-card {
    text-align: center;
    padding: 50px 20px;
  }
}
</style>
