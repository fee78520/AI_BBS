<template>
  <div class="conversation">
    <el-card>
      <!-- 顶部导航 -->
      <template #header>
        <div class="conversation-header">
          <el-button link @click="goBack">
            <el-icon><ArrowLeft /></el-icon>
            返回
          </el-button>
          <div class="user-info" @click="goToUserProfile">
            <el-avatar :size="36" :src="otherUser?.avatar" />
            <span class="username">{{ otherUser?.username }}</span>
          </div>
          <div style="width: 60px"></div>
        </div>
      </template>

      <!-- 消息列表 -->
      <div class="message-list" ref="messageListRef" v-loading="loading">
        <div v-if="hasMore" class="load-more">
          <el-button link @click="loadMore" :loading="loadingMore">
            加载更多
          </el-button>
        </div>
        
        <div 
          v-for="msg in messages" 
          :key="msg.id" 
          class="message-item"
          :class="{ 'self': msg.sender_id === currentUserId }"
        >
          <el-avatar 
            :size="36" 
            :src="msg.sender_id === currentUserId ? currentUser?.avatar : otherUser?.avatar"
            class="avatar"
          />
          <div class="message-content">
            <div class="bubble">
              <div v-if="msg.content" class="text" v-html="formatContent(msg.content)"></div>
              <div v-if="msg.images && msg.images.length > 0" class="images">
                <el-image
                  v-for="(img, idx) in msg.images"
                  :key="idx"
                  :src="img"
                  :preview-src-list="msg.images"
                  :initial-index="idx"
                  fit="cover"
                  class="message-image"
                />
              </div>
            </div>
            <div class="time">{{ formatTime(msg.created_at) }}</div>
          </div>
        </div>
        
        <div v-if="messages.length === 0 && !loading" class="empty-tip">
          暂无消息，发送第一条私信吧
        </div>
      </div>

      <!-- 底部输入区域 -->
      <div class="input-area">
        <el-upload
          :show-file-list="false"
          :before-upload="beforeImageUpload"
          :http-request="handleImageUpload"
          accept="image/*"
        >
          <el-button link>
            <el-icon size="20"><Picture /></el-icon>
          </el-button>
        </el-upload>
        <el-input
          v-model="inputMessage"
          placeholder="输入消息..."
          @keyup.enter="sendMessage"
          style="flex: 1; margin: 0 12px;"
        />
        <el-button type="primary" @click="sendMessage" :loading="sending">
          发送
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Picture } from '@element-plus/icons-vue'
import api from '@/api'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const loading = ref(false)
const loadingMore = ref(false)
const sending = ref(false)
const messages = ref([])
const page = ref(1)
const total = ref(0)
const hasMore = ref(false)
const otherUser = ref(null)

const inputMessage = ref('')
const messageListRef = ref(null)
let pollingTimer = null

const currentUserId = computed(() => userStore.user?.id)
const currentUser = computed(() => userStore.user)
const otherUserId = computed(() => parseInt(route.params.userId))

// 加载对话消息
const loadMessages = async (isLoadMore = false) => {
  if (isLoadMore) {
    loadingMore.value = true
  } else {
    loading.value = true
  }

  try {
    const data = await api.messages.getConversationMessages(otherUserId.value, {
      page: page.value,
      page_size: 20
    })

    if (isLoadMore) {
      // 加载更多时，消息插入到前面
      messages.value = [...data.items.reverse(), ...messages.value]
    } else {
      // 首次加载，消息倒序显示（最新在底部）
      messages.value = data.items.reverse()
    }

    total.value = data.total
    hasMore.value = messages.value.length < total.value

    // 获取对方用户信息
    if (messages.value.length > 0) {
      const firstMsg = messages.value[messages.value.length - 1]
      otherUser.value = firstMsg.sender_id === currentUserId.value
        ? firstMsg.receiver
        : firstMsg.sender
    }

    // 首次加载滚动到底部
    if (!isLoadMore) {
      await nextTick()
      scrollToBottom()
    }
  } catch (error) {
    console.error('加载消息失败:', error)
    ElMessage.error('加载消息失败')
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

// 轮询刷新新消息（只获取最新的消息）
const pollNewMessages = async () => {
  // 页面不可见时跳过
  if (document.visibilityState !== 'visible') return

  try {
    const data = await api.messages.getConversationMessages(otherUserId.value, {
      page: 1,
      page_size: 20
    })

    const newMessages = data.items.reverse()
    const currentLatestId = messages.value.length > 0 ? messages.value[messages.value.length - 1].id : 0

    // 找出新消息
    const newOnes = newMessages.filter(msg => msg.id > currentLatestId)
    if (newOnes.length > 0) {
      messages.value.push(...newOnes)
      await nextTick()
      scrollToBottom()
    }
  } catch (error) {
    console.error('轮询消息失败:', error)
  }
}

// 开始轮询
const startPolling = () => {
  // 每1秒轮询一次新消息
  pollingTimer = setInterval(pollNewMessages, 1000)
}

// 停止轮询
const stopPolling = () => {
  if (pollingTimer) {
    clearInterval(pollingTimer)
    pollingTimer = null
  }
}

// 加载更多
const loadMore = () => {
  page.value++
  loadMessages(true)
}

// 发送消息
const sendMessage = async () => {
  if (!inputMessage.value.trim() && !pendingImages.value.length) {
    return
  }
  
  sending.value = true
  try {
    const data = {
      receiver_id: otherUserId.value,
      content: inputMessage.value.trim() || null,
      images: pendingImages.value.length > 0 ? pendingImages.value : null
    }
    
    const newMsg = await api.messages.send(data)
    
    // 添加到消息列表
    messages.value.push({
      ...newMsg,
      sender: currentUser.value,
      receiver: otherUser.value
    })
    
    // 清空输入
    inputMessage.value = ''
    pendingImages.value = []
    
    // 滚动到底部
    await nextTick()
    scrollToBottom()
  } catch (error) {
    console.error('发送失败:', error)
    ElMessage.error('发送失败')
  } finally {
    sending.value = false
  }
}

// 图片上传
const pendingImages = ref([])

const beforeImageUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  const isLt5M = file.size / 1024 / 1024 < 5
  
  if (!isImage) {
    ElMessage.error('只能上传图片文件')
    return false
  }
  if (!isLt5M) {
    ElMessage.error('图片大小不能超过 5MB')
    return false
  }
  return true
}

const handleImageUpload = async (options) => {
  try {
    const res = await api.uploads.uploadImage(options.file)
    pendingImages.value.push(res.file_path)
    
    // 直接发送图片消息
    const data = {
      receiver_id: otherUserId.value,
      content: null,
      images: [res.file_path]
    }
    
    const newMsg = await api.messages.send(data)
    messages.value.push({
      ...newMsg,
      sender: currentUser.value,
      receiver: otherUser.value
    })
    
    await nextTick()
    scrollToBottom()
  } catch (error) {
    ElMessage.error('图片上传失败')
  }
}

// 滚动到底部
const scrollToBottom = () => {
  if (messageListRef.value) {
    messageListRef.value.scrollTop = messageListRef.value.scrollHeight
  }
}

// 格式化时间
const formatTime = (dateStr) => {
  const date = new Date(dateStr)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

// 格式化内容（处理换行）
const formatContent = (content) => {
  if (!content) return ''
  return content.replace(/\n/g, '<br>')
}

// 返回
const goBack = () => {
  router.push('/messages')
}

// 查看用户主页
const goToUserProfile = () => {
  router.push(`/user/${otherUserId.value}`)
}

// 监听路由变化
watch(() => route.params.userId, (newId) => {
  if (newId) {
    page.value = 1
    messages.value = []
    stopPolling()
    loadMessages()
    startPolling()
  }
})

onMounted(() => {
  loadMessages()
  startPolling()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style lang="scss" scoped>
.conversation {
  max-width: 800px;
  margin: 0 auto;

  .conversation-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .user-info {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;

      .username {
        font-weight: 500;
        font-size: 16px;
      }
    }
  }

  .message-list {
    height: 500px;
    overflow-y: auto;
    padding: 16px;
    background-color: #f5f7fa;

    .load-more {
      text-align: center;
      padding: 10px 0;
      margin-bottom: 10px;
    }

    .message-item {
      display: flex;
      gap: 12px;
      margin-bottom: 16px;

      &.self {
        flex-direction: row-reverse;

        .message-content {
          align-items: flex-end;
        }

        .bubble {
          background-color: #95ec69;
        }
      }

      .avatar {
        flex-shrink: 0;
      }

      .message-content {
        display: flex;
        flex-direction: column;
        gap: 4px;
        max-width: 60%;

        .bubble {
          padding: 10px 14px;
          background-color: #fff;
          border-radius: 8px;
          word-break: break-all;
          line-height: 1.5;

          .text {
            font-size: 14px;
            color: #303133;
          }

          .images {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;

            .message-image {
              width: 120px;
              height: 120px;
              border-radius: 4px;
              cursor: pointer;
            }
          }
        }

        .time {
          font-size: 11px;
          color: #909399;
          padding: 0 4px;
        }
      }
    }

    .empty-tip {
      text-align: center;
      color: #909399;
      padding: 40px 0;
    }
  }

  .input-area {
    display: flex;
    align-items: center;
    padding: 12px 16px;
    border-top: 1px solid #ebeef5;
    background-color: #fff;
  }
}
</style>
