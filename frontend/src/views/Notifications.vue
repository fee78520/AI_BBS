<template>
  <div class="notifications">
    <el-card>
      <template #header>
        <div class="card-header">
          <span class="title">通知</span>
          <div class="actions">
            <el-button
              v-if="unreadCount > 0"
              type="primary"
              size="small"
              @click="markAllAsRead"
            >
              全部已读
            </el-button>
            <el-tag v-if="unreadCount > 0" type="danger" size="small">
              {{ unreadCount }} 条未读
            </el-tag>
          </div>
        </div>
      </template>

      <!-- 通知列表 -->
      <div v-loading="loading" class="notification-list">
        <el-empty v-if="!loading && notifications.length === 0" description="暂无通知" />

        <div
          v-for="notification in notifications"
          :key="notification.id"
          :class="['notification-item', { unread: !notification.is_read }]"
          @click="handleNotificationClick(notification)"
        >
          <div class="notification-header">
            <el-tag
              :type="getNotificationTypeColor(notification.notification_type)"
              size="small"
              class="type-tag"
            >
              {{ getNotificationTypeText(notification.notification_type) }}
            </el-tag>
            <span class="time">{{ formatTime(notification.created_at) }}</span>
          </div>

          <div class="notification-content">
            <h4 class="title">{{ notification.title }}</h4>
            <p class="content">{{ notification.content }}</p>
          </div>

          <div class="notification-actions">
            <el-button
              v-if="!notification.is_read"
              type="primary"
              link
              size="small"
              @click.stop="markAsRead(notification.id)"
            >
              标记已读
            </el-button>
            <el-button
              type="danger"
              link
              size="small"
              @click.stop="deleteNotification(notification.id)"
            >
              删除
            </el-button>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <div v-if="total > 0" class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="loadNotifications"
          @current-change="loadNotifications"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'

const router = useRouter()

// 数据
const loading = ref(false)
const notifications = ref([])
const unreadCount = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 加载通知列表
const loadNotifications = async () => {
  loading.value = true
  try {
    const res = await api.notifications.getList({
      page: currentPage.value,
      page_size: pageSize.value
    })
    notifications.value = res.items || []
    total.value = res.total || 0
  } catch (error) {
    console.error('加载通知失败:', error)
    ElMessage.error('加载通知失败')
  } finally {
    loading.value = false
  }
}

// 加载未读数量
const loadUnreadCount = async () => {
  try {
    const res = await api.notifications.getUnreadCount()
    unreadCount.value = res.count || 0
  } catch (error) {
    console.error('加载未读数量失败:', error)
  }
}

// 标记单个通知为已读
const markAsRead = async (id) => {
  try {
    await api.notifications.markAsRead(id)
    const notification = notifications.value.find(n => n.id === id)
    if (notification) {
      notification.is_read = true
    }
    loadUnreadCount()
  } catch (error) {
    console.error('标记已读失败:', error)
    ElMessage.error('操作失败')
  }
}

// 标记所有通知为已读
const markAllAsRead = async () => {
  try {
    await api.notifications.markAllAsRead()
    notifications.value.forEach(n => {
      n.is_read = true
    })
    unreadCount.value = 0
    ElMessage.success('已全部标记为已读')
  } catch (error) {
    console.error('标记已读失败:', error)
    ElMessage.error('操作失败')
  }
}

// 删除通知
const deleteNotification = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这条通知吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await api.notifications.delete(id)
    notifications.value = notifications.value.filter(n => n.id !== id)
    const notification = notifications.value.find(n => n.id === id)
    if (notification && !notification.is_read) {
      loadUnreadCount()
    }
    ElMessage.success('删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除通知失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 点击通知
const handleNotificationClick = (notification) => {
  // 标记为已读
  if (!notification.is_read) {
    markAsRead(notification.id)
  }

  // 根据通知类型跳转
  if (notification.related_id) {
    const type = notification.notification_type
    if (type === 'comment' || type === 'reply') {
      // 评论相关，跳转到帖子详情
      router.push(`/posts/${notification.related_id}`)
    } else if (type === 'like') {
      // 点赞相关，跳转到被点赞内容
      router.push(`/posts/${notification.related_id}`)
    }
    // 其他类型暂不处理
  }
}

// 获取通知类型颜色
const getNotificationTypeColor = (type) => {
  const colorMap = {
    comment: 'primary',
    reply: 'success',
    like: 'danger',
    mention: 'warning',
    system: 'info',
    follow: 'success'
  }
  return colorMap[type] || 'info'
}

// 获取通知类型文本
const getNotificationTypeText = (type) => {
  const textMap = {
    comment: '评论',
    reply: '回复',
    like: '点赞',
    mention: '@提到',
    system: '系统',
    follow: '关注'
  }
  return textMap[type] || '通知'
}

// 格式化时间
const formatTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const diff = now - date

  // 小于1分钟
  if (diff < 60000) {
    return '刚刚'
  }
  // 小于1小时
  if (diff < 3600000) {
    return `${Math.floor(diff / 60000)} 分钟前`
  }
  // 小于24小时
  if (diff < 86400000) {
    return `${Math.floor(diff / 3600000)} 小时前`
  }
  // 小于7天
  if (diff < 604800000) {
    return `${Math.floor(diff / 86400000)} 天前`
  }
  // 显示具体日期
  return date.toLocaleDateString('zh-CN')
}

// 初始化
onMounted(() => {
  loadNotifications()
  loadUnreadCount()
})
</script>

<style lang="scss" scoped>
.notifications {
  max-width: 900px;
  margin: 20px auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;

  .title {
    font-size: 18px;
    font-weight: 600;
  }

  .actions {
    display: flex;
    gap: 10px;
    align-items: center;
  }
}

.notification-list {
  min-height: 200px;

  .notification-item {
    padding: 16px;
    border-bottom: 1px solid #ebeef5;
    cursor: pointer;
    transition: background-color 0.2s;

    &:hover {
      background-color: #f5f7fa;
    }

    &.unread {
      background-color: #f0f9ff;
      border-left: 3px solid #409eff;
    }

    &:last-child {
      border-bottom: none;
    }
  }

  .notification-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;

    .type-tag {
      margin-right: 8px;
    }

    .time {
      font-size: 12px;
      color: #909399;
    }
  }

  .notification-content {
    margin-bottom: 12px;

    .title {
      font-size: 14px;
      font-weight: 600;
      margin: 0 0 6px 0;
      color: #303133;
    }

    .content {
      font-size: 13px;
      color: #606266;
      margin: 0;
      line-height: 1.5;
      overflow: hidden;
      text-overflow: ellipsis;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
    }
  }

  .notification-actions {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
  }
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>
