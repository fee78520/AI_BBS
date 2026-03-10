<template>
  <div class="likes">
    <el-card>
      <template #header>
        <el-tabs v-model="activeTab" @tab-change="handleTabChange">
          <el-tab-pane label="点赞的帖子" name="posts" />
          <el-tab-pane label="点赞的评论" name="comments" />
        </el-tabs>
      </template>

      <el-empty v-if="!loading && items.length === 0" :description="activeTab === 'posts' ? '暂无点赞的帖子' : '暂无点赞的评论'" />

      <!-- 帖子列表 -->
      <div v-else-if="activeTab === 'posts'">
        <el-table :data="items" v-loading="loading" style="width: 100%">
          <el-table-column prop="title" label="帖子标题" min-width="300">
            <template #default="{ row }">
              <router-link :to="`/post/${row.id}`" class="post-link">
                {{ row.title }}
              </router-link>
            </template>
          </el-table-column>
          <el-table-column prop="author.username" label="作者" width="120" />
          <el-table-column prop="category.name" label="版块" width="120" />
          <el-table-column prop="view_count" label="浏览" width="80" />
          <el-table-column prop="like_count" label="点赞" width="80" />
          <el-table-column prop="comment_count" label="评论" width="80" />
          <el-table-column label="点赞时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.liked_at || row.created_at) }}
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 评论列表 -->
      <div v-else-if="activeTab === 'comments'">
        <div v-for="item in items" :key="item.id" class="comment-item">
          <div class="comment-header">
            <el-avatar :size="32" :src="item.author?.avatar" />
            <div class="comment-author-info">
              <span class="comment-author">{{ item.author?.username }}</span>
              <span class="comment-time">{{ formatDate(item.liked_at || item.created_at) }}</span>
            </div>
          </div>
          <div class="comment-content">{{ item.content }}</div>
          <div class="comment-post">
            <span>所属帖子：</span>
            <router-link v-if="item.post" :to="`/post/${item.post.id}`" class="post-link">
              {{ item.post.title }}
            </router-link>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <el-pagination
        v-if="total > 0"
        :current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        @current-change="handlePageChange"
        layout="prev, pager, next, jumper"
        style="margin-top: 20px; text-align: center"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const activeTab = ref('posts')
const items = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

onMounted(() => {
  loadLikes()
})

async function loadLikes() {
  loading.value = true
  try {
    let response
    if (activeTab.value === 'posts') {
      response = await api.likes.getLikedPosts({
        page: currentPage.value,
        page_size: pageSize.value
      })
    } else {
      response = await api.likes.getLikedComments({
        page: currentPage.value,
        page_size: pageSize.value
      })
    }
    items.value = response.items || []
    total.value = response.total || 0
  } catch (error) {
    console.error('加载点赞列表失败:', error)
    ElMessage.error('加载点赞列表失败')
  } finally {
    loading.value = false
  }
}

function handleTabChange() {
  currentPage.value = 1
  loadLikes()
}

function handlePageChange(page) {
  currentPage.value = page
  loadLikes()
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}
</script>

<style lang="scss" scoped>
.likes {
  max-width: 1200px;
  margin: 20px auto;

  .post-link {
    color: #409eff;
    text-decoration: none;

    &:hover {
      text-decoration: underline;
    }
  }

  .comment-item {
    padding: 16px;
    border-bottom: 1px solid #ebeef5;

    &:last-child {
      border-bottom: none;
    }

    .comment-header {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 12px;

      .comment-author-info {
        display: flex;
        flex-direction: column;
        gap: 4px;

        .comment-author {
          font-weight: 500;
          color: #303133;
        }

        .comment-time {
          font-size: 12px;
          color: #909399;
        }
      }
    }

    .comment-content {
      color: #606266;
      line-height: 1.6;
      margin-bottom: 12px;
      padding-left: 44px;
    }

    .comment-post {
      font-size: 13px;
      color: #909399;
      padding-left: 44px;

      span {
        margin-right: 4px;
      }
    }
  }
}
</style>
