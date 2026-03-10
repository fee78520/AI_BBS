<template>
  <div class="messages">
    <el-card>
      <template #header>
        <div class="messages-header">
          <h2>私信</h2>
          <div class="actions">
            <el-button type="primary" @click="showSendMessageDialog">
              <el-icon><Plus /></el-icon>
              发私信
            </el-button>
          </div>
        </div>
      </template>

      <!-- 对话列表 -->
      <div v-loading="loading" class="conversation-list">
        <div v-if="conversations.length === 0 && !loading" class="empty-tip">
          <el-empty description="暂无私信对话">
            <el-button type="primary" @click="showSendMessageDialog">发送私信</el-button>
          </el-empty>
        </div>
        
        <div 
          v-for="conv in conversations" 
          :key="conv.user_id" 
          class="conversation-item"
          @click="openConversation(conv.user_id)"
        >
          <el-badge :value="conv.unread_count" :hidden="conv.unread_count === 0" :max="99">
            <el-avatar :size="50" :src="conv.user?.avatar" />
          </el-badge>
          <div class="conversation-content">
            <div class="conversation-header">
              <span class="username">{{ conv.user?.username }}</span>
              <span class="time">{{ formatTime(conv.updated_at) }}</span>
            </div>
            <div class="last-message">
              {{ getLastMessagePreview(conv.last_message) }}
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 发送私信对话框 -->
    <el-dialog v-model="sendMessageVisible" title="发送私信" width="500px">
      <el-form :model="messageForm" label-width="80px">
        <el-form-item label="接收人">
          <el-select
            v-model="messageForm.receiver_id"
            filterable
            remote
            reserve-keyword
            placeholder="搜索用户名"
            :remote-method="searchUsers"
            :loading="searching"
            style="width: 100%"
          >
            <el-option
              v-for="user in userList"
              :key="user.id"
              :label="user.username"
              :value="user.id"
            >
              <div class="user-option">
                <el-avatar :size="24" :src="user.avatar" />
                <span>{{ user.username }}</span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="消息内容">
          <el-input
            v-model="messageForm.content"
            type="textarea"
            :rows="4"
            placeholder="写下你的消息..."
            maxlength="1000"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="图片">
          <el-upload
            v-model:file-list="imageList"
            action=""
            list-type="picture-card"
            :auto-upload="false"
            :limit="5"
            :on-change="handleImageChange"
            :on-remove="handleImageRemove"
          >
            <el-icon><Plus /></el-icon>
            <template #tip>
              <div class="upload-tip">最多上传5张图片</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="sendMessageVisible = false">取消</el-button>
        <el-button type="primary" @click="sendMessage" :loading="sending">发送</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import api from '@/api'

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const conversations = ref([])

const sendMessageVisible = ref(false)
const sending = ref(false)
const messageForm = ref({
  receiver_id: null,
  content: '',
  images: []
})
const imageList = ref([])
const userList = ref([])
const searching = ref(false)

// 加载对话列表
const loadConversations = async () => {
  loading.value = true
  try {
    conversations.value = await api.messages.getConversations()
  } catch (error) {
    console.error('加载对话列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 打开对话
const openConversation = (userId) => {
  router.push(`/messages/${userId}`)
}

// 格式化时间
const formatTime = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date
  
  // 今天内显示时:分
  if (diff < 86400000 && date.getDate() === now.getDate()) {
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
  // 昨天显示"昨天"
  const yesterday = new Date(now)
  yesterday.setDate(yesterday.getDate() - 1)
  if (date.getDate() === yesterday.getDate()) {
    return '昨天'
  }
  // 一周内显示星期
  if (diff < 604800000) {
    const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
    return weekdays[date.getDay()]
  }
  // 其他显示日期
  return date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
}

// 获取最后消息预览
const getLastMessagePreview = (msg) => {
  if (!msg) return ''
  if (msg.images && msg.images.length > 0) {
    return '[图片]'
  }
  return msg.content || ''
}

// 显示发送对话框
const showSendMessageDialog = () => {
  messageForm.value = {
    receiver_id: null,
    content: '',
    images: []
  }
  imageList.value = []
  userList.value = []
  sendMessageVisible.value = true
}

// 搜索用户
const searchUsers = async (query) => {
  if (!query) {
    userList.value = []
    return
  }
  searching.value = true
  try {
    const data = await api.users.getList({ page: 1, page_size: 10, search: query })
    userList.value = data.items
  } catch (error) {
    console.error('搜索用户失败:', error)
  } finally {
    searching.value = false
  }
}

// 图片上传处理
const handleImageChange = async (file) => {
  try {
    const res = await api.uploads.uploadImage(file.raw)
    messageForm.value.images.push(res.file_path)
  } catch (error) {
    ElMessage.error('图片上传失败')
    throw error
  }
}

const handleImageRemove = (file) => {
  const idx = messageForm.value.images.findIndex(img => img.includes(file.name))
  if (idx > -1) {
    messageForm.value.images.splice(idx, 1)
  }
}

// 发送消息
const sendMessage = async () => {
  if (!messageForm.value.receiver_id) {
    ElMessage.warning('请选择接收人')
    return
  }
  if (!messageForm.value.content && messageForm.value.images.length === 0) {
    ElMessage.warning('消息内容或图片不能为空')
    return
  }

  sending.value = true
  try {
    await api.messages.send(messageForm.value)
    ElMessage.success('发送成功')
    sendMessageVisible.value = false
    // 发送成功后跳转到对话页面
    router.push(`/messages/${messageForm.value.receiver_id}`)
  } catch (error) {
    console.error('发送失败:', error)
  } finally {
    sending.value = false
  }
}

onMounted(async () => {
  await loadConversations()
  
  // 检查是否有预设的接收人（从用户详情页跳转过来）
  const { to_user_id, to_username } = route.query
  if (to_user_id) {
    // 预填接收人信息并打开发送对话框
    messageForm.value.receiver_id = parseInt(to_user_id)
    messageForm.value.content = ''
    messageForm.value.images = []
    imageList.value = []
    userList.value = [{
      id: parseInt(to_user_id),
      username: to_username || '用户'
    }]
    sendMessageVisible.value = true
  }
})
</script>

<style lang="scss" scoped>
.messages {
  max-width: 800px;
  margin: 0 auto;

  .messages-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    h2 {
      margin: 0;
    }
  }

  .conversation-list {
    .conversation-item {
      display: flex;
      gap: 16px;
      padding: 16px;
      border-bottom: 1px solid #f0f0f0;
      cursor: pointer;
      transition: background-color 0.3s;

      &:hover {
        background-color: #f5f7fa;
      }

      &:last-child {
        border-bottom: none;
      }

      .conversation-content {
        flex: 1;
        min-width: 0;

        .conversation-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 6px;

          .username {
            font-weight: 500;
            font-size: 15px;
            color: #303133;
          }

          .time {
            font-size: 12px;
            color: #909399;
          }
        }

        .last-message {
          font-size: 13px;
          color: #909399;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
      }
    }
  }

  .empty-tip {
    padding: 40px 0;
  }

  .user-option {
    display: flex;
    align-items: center;
    gap: 8px;

    span {
      font-size: 14px;
    }
  }

  .upload-tip {
    font-size: 12px;
    color: #909399;
    margin-top: 8px;
  }
}
</style>
