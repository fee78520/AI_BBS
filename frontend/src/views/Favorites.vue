<template>
  <div class="favorites">
    <el-card>
      <h2>我的收藏</h2>
      <el-empty v-if="!loading && items.length === 0" description="暂无收藏" />
      <div v-else>
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
          <el-table-column prop="created_at" label="收藏时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-button type="danger" size="small" @click="handleRemoveFavorite(row)">
                取消收藏
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination
          v-if="total > 0"
          :current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          @current-change="handlePageChange"
          layout="prev, pager, next, jumper"
          style="margin-top: 20px; text-align: center"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const items = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

onMounted(() => {
  loadFavorites()
})

async function loadFavorites() {
  loading.value = true
  try {
    const response = await api.favorites.getList({
      page: currentPage.value,
      page_size: pageSize.value
    })
    items.value = response.items || []
    total.value = response.total || 0
  } catch (error) {
    console.error('加载收藏失败:', error)
    ElMessage.error('加载收藏失败')
  } finally {
    loading.value = false
  }
}

async function handleRemoveFavorite(post) {
  try {
    await api.favorites.remove(post.id)
    ElMessage.success('已取消收藏')
    loadFavorites()
  } catch (error) {
    console.error('取消收藏失败:', error)
    ElMessage.error('取消收藏失败')
  }
}

function handlePageChange(page) {
  currentPage.value = page
  loadFavorites()
}

function formatDate(dateStr) {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}
</script>

<style lang="scss" scoped>
.favorites {
  max-width: 1200px;
  margin: 0 auto;

  .post-link {
    color: #409eff;
    text-decoration: none;

    &:hover {
      text-decoration: underline;
    }
  }
}
</style>
