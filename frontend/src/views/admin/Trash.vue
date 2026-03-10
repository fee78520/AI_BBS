<template>
  <div class="admin-trash">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>回收站</span>
          <el-radio-group v-model="filterType" @change="loadPosts">
            <el-radio-button label="all">全部</el-radio-button>
            <el-radio-button label="hidden">已隐藏</el-radio-button>
            <el-radio-button label="deleted">已删除</el-radio-button>
          </el-radio-group>
        </div>
      </template>

      <el-table :data="posts" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
        <el-table-column prop="author" label="作者" width="120">
          <template #default="{ row }">{{ row.author?.username || '-' }}</template>
        </el-table-column>
        <el-table-column prop="category" label="版块" width="120">
          <template #default="{ row }">{{ row.category?.name || '-' }}</template>
        </el-table-column>
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.is_deleted" type="danger">已删除</el-tag>
            <el-tag v-else-if="row.is_hidden" type="info">已隐藏</el-tag>
            <el-tag v-else type="success">正常</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="view_count" label="浏览" width="80" />
        <el-table-column prop="like_count" label="点赞" width="80" />
        <el-table-column prop="comment_count" label="评论" width="80" />
        <el-table-column prop="updated_at" label="更新时间" width="180">
          <template #default="{ row }">{{ formatDate(row.updated_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="200">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="viewPost(row)">查看</el-button>
            <el-button v-if="row.is_hidden" type="success" size="small" @click="toggleHide(row)">取消隐藏</el-button>
            <el-button v-if="row.is_deleted" type="warning" size="small" @click="restorePost(row)">恢复</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="loadPosts"
        @current-change="loadPosts"
        style="margin-top: 20px; justify-content: flex-end;"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import api from '@/api'

const router = useRouter()
const loading = ref(false)
const posts = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const filterType = ref('all')

onMounted(() => {
  loadPosts()
})

async function loadPosts() {
  loading.value = true
  try {
    const data = await api.posts.getTrash({
      page: page.value,
      page_size: pageSize.value,
      filter_type: filterType.value
    })
    posts.value = data.items
    total.value = data.total
  } catch (error) {
    console.error('加载回收站失败:', error)
    ElMessage.error('加载回收站失败')
  } finally {
    loading.value = false
  }
}

function viewPost(row) {
  router.push(`/post/${row.id}`)
}

async function toggleHide(row) {
  try {
    await api.posts.hide(row.id)
    ElMessage.success('已取消隐藏')
    loadPosts()
  } catch (error) {
    console.error('操作失败:', error)
    ElMessage.error('操作失败')
  }
}

async function restorePost(row) {
  try {
    await ElMessageBox.confirm('确定要恢复此帖子吗？', '确认恢复', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await api.posts.restore(row.id)
    ElMessage.success('帖子已恢复')
    loadPosts()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('恢复失败:', error)
      ElMessage.error('恢复失败')
    }
  }
}

function formatDate(date) {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN')
}
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
