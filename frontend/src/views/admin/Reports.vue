<template>
  <div class="admin-reports">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>举报管理</span>
          <el-select v-model="statusFilter" placeholder="状态筛选" clearable @change="loadReports" style="width: 150px">
            <el-option label="待处理" value="pending" />
            <el-option label="已通过" value="approved" />
            <el-option label="已驳回" value="rejected" />
          </el-select>
        </div>
      </template>

      <el-table :data="reports" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column label="举报类型" width="100">
          <template #default="{ row }">
            <el-tag>{{ row.post_id ? '帖子' : row.comment_id ? '评论' : '其他' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="post_id" label="帖子ID" width="80">
          <template #default="{ row }">{{ row.post_id || '-' }}</template>
        </el-table-column>
        <el-table-column prop="comment_id" label="评论ID" width="80">
          <template #default="{ row }">{{ row.comment_id || '-' }}</template>
        </el-table-column>
        <el-table-column prop="reporter" label="举报人" width="120">
          <template #default="{ row }">{{ row.reporter?.username || '-' }}</template>
        </el-table-column>
        <el-table-column prop="reason" label="举报原因" min-width="200" show-overflow-tooltip />
        <el-table-column prop="description" label="详细说明" min-width="200" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTag(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="handler" label="处理人" width="120">
          <template #default="{ row }">{{ row.handler?.username || '-' }}</template>
        </el-table-column>
        <el-table-column prop="handler_note" label="处理备注" min-width="150" show-overflow-tooltip />
        <el-table-column prop="created_at" label="举报时间" width="180">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="120">
          <template #default="{ row }">
            <template v-if="row.status === 'pending'">
              <el-button type="primary" size="small" @click="handleReport(row)">处理</el-button>
            </template>
            <span v-else class="text-muted">已处理</span>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="loadReports"
        @current-change="loadReports"
        style="margin-top: 20px; justify-content: flex-end;"
      />
    </el-card>

    <!-- 处理对话框 -->
    <el-dialog v-model="handleDialogVisible" title="处理举报" width="500px">
      <el-form :model="handleForm" label-width="100px">
        <el-form-item label="操作类型">
          <el-radio-group v-model="handleForm.action">
            <el-radio label="hide" border>隐藏内容</el-radio>
            <el-radio label="delete" border type="danger">删除内容</el-radio>
            <el-radio label="reject" border>驳回举报</el-radio>
            <el-radio label="ignore" border>忽略举报</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-alert
          v-if="handleForm.action === 'hide'"
          type="warning"
          title="隐藏内容"
          description="内容将仅对管理员可见，普通用户无法查看。"
          :closable="false"
          show-icon
          style="margin-bottom: 16px;"
        />
        <el-alert
          v-if="handleForm.action === 'delete'"
          type="error"
          title="删除内容"
          description="内容将被永久删除（软删除），无法恢复。"
          :closable="false"
          show-icon
          style="margin-bottom: 16px;"
        />
        <el-alert
          v-if="handleForm.action === 'reject'"
          type="info"
          title="驳回举报"
          description="该举报将被驳回，内容保持原状。"
          :closable="false"
          show-icon
          style="margin-bottom: 16px;"
        />
        <el-alert
          v-if="handleForm.action === 'ignore'"
          type="info"
          title="忽略举报"
          description="暂时搁置该举报，不处理内容，后续可重新处理。"
          :closable="false"
          show-icon
          style="margin-bottom: 16px;"
        />
        <el-form-item label="处理备注">
          <el-input v-model="handleForm.note" type="textarea" :rows="3" placeholder="请输入处理备注（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="handleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmHandle">确认处理</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const loading = ref(false)
const reports = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const statusFilter = ref('')

const handleDialogVisible = ref(false)
const handleForm = ref({ id: null, approved: false, note: '' })

onMounted(() => {
  loadReports()
})

async function loadReports() {
  loading.value = true
  try {
    const data = await api.reports.getList({
      page: page.value,
      page_size: pageSize.value,
      status: statusFilter.value || undefined
    })
    reports.value = data.items
    total.value = data.total
  } catch (error) {
    console.error('加载举报列表失败:', error)
  } finally {
    loading.value = false
  }
}

function handleReport(row) {
  handleForm.value = {
    id: row.id,
    action: 'hide',
    note: ''
  }
  handleDialogVisible.value = true
}

async function confirmHandle() {
  try {
    await api.reports.handle(handleForm.value.id, {
      action: handleForm.value.action,
      handler_note: handleForm.value.note
    })
    ElMessage.success('处理成功')
    handleDialogVisible.value = false
    loadReports()
  } catch (error) {
    console.error('处理举报失败:', error)
    ElMessage.error(error.response?.data?.detail || '处理失败')
  }
}

function getStatusTag(status) {
  const map = {
    pending: 'warning',
    approved: 'success',
    rejected: 'info',
    ignored: ''
  }
  return map[status] || ''
}

function getStatusLabel(status) {
  const map = {
    pending: '待处理',
    approved: '已通过',
    rejected: '已驳回',
    ignored: '已忽略'
  }
  return map[status] || status
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}
</script>

<style scoped>
.admin-reports {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.text-muted {
  color: #999;
  font-size: 12px;
}
</style>