<template>
  <div class="admin-posts">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>帖子管理</span>
          <el-input
            v-model="searchText"
            placeholder="搜索帖子标题/内容"
            style="width: 200px"
            clearable
            @clear="loadPosts"
            @keyup.enter="loadPosts"
          >
            <template #append>
              <el-button @click="loadPosts">搜索</el-button>
            </template>
          </el-input>
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
        <el-table-column prop="post_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getPostTypeTag(row.post_type)">{{ getPostTypeLabel(row.post_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTag(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="view_count" label="浏览" width="80" />
        <el-table-column prop="like_count" label="点赞" width="80" />
        <el-table-column prop="comment_count" label="评论" width="80" />
        <el-table-column prop="is_pinned" label="置顶" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.is_pinned" type="warning">是</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="is_hidden" label="隐藏" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.is_hidden" type="info">是</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="发布时间" width="180">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="350">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="viewPost(row)">查看</el-button>
            <el-button
              :type="row.is_pinned ? 'warning' : 'success'"
              size="small"
              @click="togglePin(row)"
            >{{ row.is_pinned ? '取消置顶' : '置顶' }}</el-button>
            <el-button
              :type="row.post_type === 'essence' ? 'warning' : 'success'"
              size="small"
              @click="toggleEssence(row)"
            >{{ row.post_type === 'essence' ? '取消精华' : '精华' }}</el-button>
            <el-button
              :type="row.is_hidden ? 'success' : 'info'"
              size="small"
              @click="toggleHide(row)"
            >{{ row.is_hidden ? '取消隐藏' : '隐藏' }}</el-button>
            <el-button
              :type="row.is_locked ? 'success' : 'danger'"
              size="small"
              @click="toggleLock(row)"
            >{{ row.is_locked ? '解锁' : '锁定' }}</el-button>
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
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import api from '@/api'

const router = useRouter()
const loading = ref(false)
const posts = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const searchText = ref('')

onMounted(() => {
  loadPosts()
})

async function loadPosts() {
  loading.value = true
  try {
    const data = await api.posts.getList({
      page: page.value,
      page_size: pageSize.value,
      search: searchText.value || undefined,
      include_hidden: true  // 管理员查看所有帖子（包含隐藏的）
    })
    posts.value = data.items
    total.value = data.total
  } catch (error) {
    console.error('加载帖子列表失败:', error)
  } finally {
    loading.value = false
  }
}

function viewPost(row) {
  router.push(`/post/${row.id}`)
}

async function togglePin(row) {
  try {
    await api.posts.pin(row.id)
    ElMessage.success(row.is_pinned ? '已取消置顶' : '已置顶')
    loadPosts()
  } catch (error) {
    console.error('操作失败:', error)
  }
}

async function toggleLock(row) {
  try {
    await api.posts.lock(row.id)
    ElMessage.success(row.is_locked ? '已解锁' : '已锁定')
    loadPosts()
  } catch (error) {
    console.error('操作失败:', error)
  }
}

async function toggleHide(row) {
  try {
    await api.posts.hide(row.id)
    ElMessage.success(row.is_hidden ? '已取消隐藏' : '已隐藏')
    loadPosts()
  } catch (error) {
    console.error('操作失败:', error)
  }
}

async function toggleEssence(row) {
  try {
    const res = await api.posts.setEssence(row.id)
    ElMessage.success(res.message || (row.post_type === 'essence' ? '已取消精华' : '已设为精华'))
    loadPosts()
  } catch (error) {
    console.error('操作失败:', error)
  }
}

function getPostTypeTag(type) {
  const map = { normal: 'info', top: 'danger', essence: 'warning', announcement: 'success' }
  return map[type] || 'info'
}

function getPostTypeLabel(type) {
  const map = { normal: '普通', top: '置顶', essence: '精华', announcement: '公告' }
  return map[type] || type
}

function getStatusTag(status) {
  const map = { published: 'success', draft: 'info', deleted: 'danger' }
  return map[status] || 'info'
}

function getStatusLabel(status) {
  const map = { published: '已发布', draft: '草稿', deleted: '已删除' }
  return map[status] || status
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
