<template>
  <div class="category-page">
    <div v-loading="loading">
      <el-card>
        <template #header>
          <h2>{{ category?.name }}</h2>
          <p>{{ category?.description }}</p>
        </template>

        <div class="posts">
          <div v-for="post in posts" :key="post.id" class="post-item">
            <router-link :to="`/post/${post.id}`" class="post-link">
              <div class="post-title">{{ post.title }}</div>
              <div class="post-meta">
                <span>{{ post.author?.username }}</span>
                <span>{{ post.comment_count }} 回复</span>
                <span>{{ formatTime(post.created_at) }}</span>
              </div>
            </router-link>
          </div>
        </div>

        <el-pagination
          v-if="total > 0"
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="loadPosts"
        />
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'
import api from '@/api'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const route = useRoute()

const category = ref(null)
const posts = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const loading = ref(false)

onMounted(() => {
  loadCategory()
  loadPosts()
})

async function loadCategory() {
  try {
    category.value = await api.categories.getById(route.params.id)
  } catch (error) {
    console.error('加载版块失败:', error)
  }
}

async function loadPosts() {
  loading.value = true
  try {
    const data = await api.posts.getList({
      category_id: route.params.id,
      page: currentPage.value,
      page_size: pageSize.value
    })
    posts.value = data.items
    total.value = data.total
  } catch (error) {
    console.error('加载帖子失败:', error)
  } finally {
    loading.value = false
  }
}

function formatTime(time) {
  return dayjs(time).fromNow()
}
</script>

<style lang="scss" scoped>
.category-page {
  .post-item {
    padding: 16px 0;
    border-bottom: 1px solid #eee;

    &:last-child {
      border-bottom: none;
    }

    .post-link {
      text-decoration: none;

      .post-title {
        font-size: 16px;
        color: #333;
        margin-bottom: 8px;

        &:hover {
          color: #409eff;
        }
      }

      .post-meta {
        display: flex;
        gap: 16px;
        color: #999;
        font-size: 13px;
      }
    }
  }
}
</style>
