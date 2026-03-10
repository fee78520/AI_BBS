<template>
  <div class="admin-users">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>用户管理</span>
          <el-input
            v-model="searchText"
            placeholder="搜索用户名/邮箱"
            style="width: 200px"
            clearable
            @clear="loadUsers"
            @keyup.enter="loadUsers"
          >
            <template #append>
              <el-button @click="loadUsers">搜索</el-button>
            </template>
          </el-input>
        </div>
      </template>

      <el-table :data="users" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="email" label="邮箱" width="180" />
        <el-table-column prop="role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="getRoleTagType(row.role)">{{ getRoleLabel(row.role) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="user_group" label="用户组" width="100">
          <template #default="{ row }">{{ getUserGroupLabel(row.user_group) }}</template>
        </el-table-column>
        <el-table-column prop="level" label="等级" width="80" />
        <el-table-column prop="is_banned" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_banned ? 'danger' : 'success'">
              {{ row.is_banned ? '已封禁' : '正常' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="注册时间" width="180">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="200">
          <template #default="{ row }">
            <el-button
              v-if="!row.is_banned && row.role !== 'admin'"
              type="danger"
              size="small"
              @click="handleBan(row)"
            >封禁</el-button>
            <el-button
              v-if="row.is_banned"
              type="success"
              size="small"
              @click="handleUnban(row)"
            >解封</el-button>
            <el-button
              v-if="row.role === 'user'"
              type="warning"
              size="small"
              @click="handleSetModerator(row)"
            >设为版主</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="loadUsers"
        @current-change="loadUsers"
        style="margin-top: 20px; justify-content: flex-end;"
      />
    </el-card>

    <!-- 封禁对话框 -->
    <el-dialog v-model="banDialogVisible" title="封禁用户" width="400px">
      <el-form :model="banForm" label-width="80px">
        <el-form-item label="封禁原因">
          <el-input v-model="banForm.reason" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="封禁至">
          <el-date-picker
            v-model="banForm.until"
            type="datetime"
            placeholder="留空表示永久"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="banDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="confirmBan">确认封禁</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'

const loading = ref(false)
const users = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const searchText = ref('')

const banDialogVisible = ref(false)
const banForm = ref({ userId: null, reason: '', until: null })

onMounted(() => {
  loadUsers()
})

async function loadUsers() {
  loading.value = true
  try {
    const data = await api.users.getList({
      page: page.value,
      page_size: pageSize.value,
      search: searchText.value || undefined
    })
    users.value = data.items
    total.value = data.total
  } catch (error) {
    console.error('加载用户列表失败:', error)
  } finally {
    loading.value = false
  }
}

function handleBan(row) {
  banForm.value = { userId: row.id, reason: '', until: null }
  banDialogVisible.value = true
}

async function confirmBan() {
  try {
    await api.users.banUser(banForm.value.userId, {
      ban_reason: banForm.value.reason,
      ban_until: banForm.value.until?.toISOString()
    })
    ElMessage.success('用户已封禁')
    banDialogVisible.value = false
    loadUsers()
  } catch (error) {
    console.error('封禁失败:', error)
  }
}

async function handleUnban(row) {
  try {
    await api.users.unbanUser(row.id)
    ElMessage.success('用户已解封')
    loadUsers()
  } catch (error) {
    console.error('解封失败:', error)
  }
}

async function handleSetModerator(row) {
  try {
    await ElMessageBox.confirm(`确定将 ${row.username} 设为版主？`, '提示')
    await api.admin.manageUser(row.id, { role: 'moderator' })
    ElMessage.success('已设为版主')
    loadUsers()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('设置失败:', error)
    }
  }
}

function getRoleTagType(role) {
  const map = { admin: 'danger', moderator: 'warning', user: 'info' }
  return map[role] || 'info'
}

function getRoleLabel(role) {
  const map = { admin: '管理员', moderator: '版主', user: '用户' }
  return map[role] || role
}

function getUserGroupLabel(group) {
  const map = { normal: '普通', vip: 'VIP', honor: '荣誉' }
  return map[group] || group
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
