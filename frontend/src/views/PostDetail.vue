<template>
  <div class="post-detail">
    <el-card v-loading="loading">
      <template v-if="post">
        <h1>
          <el-tag v-if="post.is_deleted" type="danger" size="small" style="margin-right: 8px;">已删除</el-tag>
          <el-tag v-else-if="post.is_hidden" type="info" size="small" style="margin-right: 8px;">已隐藏</el-tag>
          {{ post.title }}
        </h1>
        <div class="post-info">
          <el-avatar :size="40" :src="post.author?.avatar" />
          <div class="author-info" @click="goToUser(post.author?.id)" style="cursor: pointer;">
            <div>{{ post.author?.username }}</div>
            <div>{{ formatDateTime(post.created_at) }}</div>
          </div>
        </div>
        <div class="post-content" v-html="post.content"></div>
        <div class="post-actions">
          <el-button :type="isLiked ? 'primary' : 'default'" @click="handleLike">
            <el-icon><Pointer /></el-icon>
            {{ post.like_count }}
          </el-button>
          <el-button :type="isFavorited ? 'warning' : 'default'" @click="handleFavorite">
            <el-icon><Collection /></el-icon>
            {{ isFavorited ? '已收藏' : '收藏' }}
          </el-button>
          <el-button @click="showShareDialog">
            <el-icon><Share /></el-icon>
            分享
          </el-button>
          <!-- 管理员操作：取消隐藏 -->
          <el-button v-if="isAdmin && post.is_hidden && !post.is_deleted" type="success" @click="handleUnhide">
            <el-icon><View /></el-icon>
            取消隐藏
          </el-button>
          <!-- 管理员操作：恢复已删除帖子 -->
          <el-button v-if="isAdmin && post.is_deleted" type="warning" @click="handleRestore">
            <el-icon><RefreshRight /></el-icon>
            恢复帖子
          </el-button>
          <el-button v-if="canDeletePost && !post.is_deleted" type="danger" @click="deletePost">
            <el-icon><Delete /></el-icon>
            删除帖子
          </el-button>
          <el-button v-if="userStore.isLoggedIn && !post.is_deleted" @click="showReportDialog('post')">
            <el-icon><Warning /></el-icon>
            举报
          </el-button>
        </div>
      </template>
    </el-card>

    <!-- 评论区域 -->
    <el-card class="comments-section" v-if="post">
      <template #header>
        <div class="comments-header">
          <span>评论 ({{ post.comment_count }})</span>
        </div>
      </template>

      <!-- 发表评论 -->
      <div class="comment-form">
        <el-input
          v-model="newComment"
          type="textarea"
          :rows="3"
          placeholder="写下你的评论..."
          maxlength="500"
          show-word-limit
        />
        <el-button type="primary" @click="submitComment" :loading="submitting" style="margin-top: 10px;">
          发表评论
        </el-button>
      </div>

      <!-- 评论列表 -->
      <div class="comments-list" v-loading="commentsLoading">
        <CommentItem
          v-for="comment in comments"
          :key="comment.id"
          :comment="comment"
          :current-user-id="user?.id"
          @reply="replyToComment"
          @like="likeComment"
          @delete="deleteComment"
          @report="reportComment"
          @view-user="goToUser"
        />

        <el-empty v-if="!commentsLoading && comments.length === 0" description="暂无评论，快来抢沙发吧！" />
      </div>

      <!-- 分页 -->
      <el-pagination
        v-if="commentsTotal > 0"
        v-model:current-page="commentsPage"
        :page-size="10"
        :total="commentsTotal"
        layout="prev, pager, next"
        @current-change="loadComments"
        style="margin-top: 20px; justify-content: center;"
      />
    </el-card>

    <!-- 回复对话框 -->
    <el-dialog v-model="replyDialogVisible" title="回复评论" width="500px">
      <el-input
        v-model="replyContent"
        type="textarea"
        :rows="3"
        placeholder="写下你的回复..."
        maxlength="500"
        show-word-limit
      />
      <template #footer>
        <el-button @click="replyDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitReply" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <!-- 举报对话框 -->
    <el-dialog v-model="reportDialogVisible" title="举报内容" width="500px">
      <el-form :model="reportForm" label-width="80px">
        <el-form-item label="举报原因">
          <el-select v-model="reportForm.reason" placeholder="请选择举报原因" style="width: 100%">
            <el-option label="垃圾广告" value="spam" />
            <el-option label="违法违规" value="illegal" />
            <el-option label="色情低俗" value="porn" />
            <el-option label="人身攻击" value="harassment" />
            <el-option label="涉政敏感" value="sensitive" />
            <el-option label="其他原因" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="详细说明">
          <el-input
            v-model="reportForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入详细说明（选填）"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reportDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitReport" :loading="submitting">提交举报</el-button>
      </template>
    </el-dialog>

    <!-- 分享对话框 -->
    <el-dialog v-model="shareDialogVisible" title="分享帖子" width="450px">
      <div class="share-content">
        <div class="share-post-title">{{ post?.title }}</div>
        <div class="share-link">
          <el-input v-model="shareUrl" readonly>
            <template #append>
              <el-button @click="copyShareLink">复制链接</el-button>
            </template>
          </el-input>
        </div>
        <div class="share-qrcode">
          <canvas ref="qrcodeCanvas"></canvas>
          <p>扫码分享</p>
        </div>
        <div class="share-platforms">
          <el-button circle @click="shareToWeibo" title="分享到微博">
            <span class="platform-icon weibo">微</span>
          </el-button>
          <el-button circle @click="shareToQQ" title="分享到QQ">
            <span class="platform-icon qq">Q</span>
          </el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Pointer, Collection, ChatDotRound, Delete, Warning, Share, View, RefreshRight } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'
import { useUserStore } from '@/stores/user'
import { formatDateTime } from '@/utils/time'
import QRCode from 'qrcode'
import CommentItem from '@/components/CommentItem.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const post = ref(null)
const loading = ref(false)
const isLiked = ref(false)
const isFavorited = ref(false)

// 计算属性：判断是否可以删除帖子
const canDeletePost = computed(() => {
  return post.value && userStore.isLoggedIn && (
    post.value.author_id === userStore.user.id ||
    userStore.user.role === 'moderator' ||
    userStore.user.role === 'admin'
  )
})

// 计算属性：判断是否是管理员
const isAdmin = computed(() => {
  return userStore.isLoggedIn && (
    userStore.user.role === 'moderator' ||
    userStore.user.role === 'admin'
  )
})

// 判断是否可以删除评论
const canDeleteComment = (comment) => {
  return userStore.isLoggedIn && (
    comment.author_id === userStore.user.id ||
    userStore.user.role === 'moderator' ||
    userStore.user.role === 'admin'
  )
}

// 评论相关
const comments = ref([])
const commentsLoading = ref(false)
const commentsPage = ref(1)
const commentsTotal = ref(0)
const newComment = ref('')
const submitting = ref(false)

// 回复相关
const replyDialogVisible = ref(false)
const replyContent = ref('')
const replyingTo = ref(null)

// 举报相关
const reportDialogVisible = ref(false)
const reportForm = ref({
  reason: '',
  description: ''
})
const reportTarget = ref({
  type: '',
  data: null
})

// 分享相关
const shareDialogVisible = ref(false)
const shareUrl = ref('')
const qrcodeCanvas = ref(null)

const showShareDialog = () => {
  shareUrl.value = `${window.location.origin}/post/${post.value.id}`
  shareDialogVisible.value = true
  nextTick(() => {
    generateQRCode()
  })
}

const generateQRCode = async () => {
  if (qrcodeCanvas.value) {
    try {
      await QRCode.toCanvas(qrcodeCanvas.value, shareUrl.value, {
        width: 150,
        margin: 2
      })
    } catch (error) {
      console.error('生成二维码失败:', error)
    }
  }
}

const copyShareLink = async () => {
  try {
    await navigator.clipboard.writeText(shareUrl.value)
    ElMessage.success('链接已复制到剪贴板')
  } catch (error) {
    // 降级方案
    const input = document.createElement('input')
    input.value = shareUrl.value
    document.body.appendChild(input)
    input.select()
    document.execCommand('copy')
    document.body.removeChild(input)
    ElMessage.success('链接已复制到剪贴板')
  }
}

const shareToWeibo = () => {
  const url = encodeURIComponent(shareUrl.value)
  const title = encodeURIComponent(post.value.title)
  window.open(`https://service.weibo.com/share/share.php?url=${url}&title=${title}`, '_blank')
}

const shareToQQ = () => {
  const url = encodeURIComponent(shareUrl.value)
  const title = encodeURIComponent(post.value.title)
  window.open(`https://connect.qq.com/widget/shareqq/index.html?url=${url}&title=${title}`, '_blank')
}

onMounted(() => {
  loadPost()
  checkLikeStatus()
  checkFavoriteStatus()
})

async function loadPost() {
  loading.value = true
  try {
    post.value = await api.posts.getById(route.params.id)
    loadComments()
  } catch (error) {
    console.error('加载帖子失败:', error)
  } finally {
    loading.value = false
  }
}

async function checkLikeStatus() {
  try {
    const res = await api.likes.check({ post_id: parseInt(route.params.id) })
    isLiked.value = res.liked
  } catch (error) {
    // 未登录时忽略错误
  }
}

async function checkFavoriteStatus() {
  try {
    const res = await api.favorites.getList({ page: 1, page_size: 100 })
    isFavorited.value = res.items.some(item => item.id === parseInt(route.params.id))
  } catch (error) {
    // 未登录时忽略错误
  }
}

async function handleLike() {
  try {
    const res = await api.likes.like({ post_id: post.value.id })
    isLiked.value = res.liked
    ElMessage.success(res.message)
    loadPost()
  } catch (error) {
    console.error('操作失败:', error)
  }
}

async function handleFavorite() {
  try {
    if (isFavorited.value) {
      await api.favorites.remove(post.value.id)
      isFavorited.value = false
      ElMessage.success('已取消收藏')
    } else {
      await api.favorites.add({ post_id: post.value.id })
      isFavorited.value = true
      ElMessage.success('收藏成功')
    }
  } catch (error) {
    console.error('收藏操作失败:', error)
  }
}

async function loadComments() {
  commentsLoading.value = true
  try {
    const res = await api.comments.getByPost(route.params.id, {
      page: commentsPage.value,
      page_size: 10
    })
    comments.value = res.items || []
    commentsTotal.value = res.total || 0
  } catch (error) {
    console.error('加载评论失败:', error)
  } finally {
    commentsLoading.value = false
  }
}

async function submitComment() {
  if (!newComment.value.trim()) {
    ElMessage.warning('请输入评论内容')
    return
  }
  submitting.value = true
  try {
    await api.comments.create({
      post_id: post.value.id,
      content: newComment.value.trim()
    })
    ElMessage.success('评论成功')
    newComment.value = ''
    loadComments()
    loadPost()
  } catch (error) {
    console.error('评论失败:', error)
  } finally {
    submitting.value = false
  }
}

function replyToComment(comment) {
  replyingTo.value = { type: 'comment', data: comment }
  replyContent.value = ''
  replyDialogVisible.value = true
}

async function submitReply() {
  if (!replyContent.value.trim()) {
    ElMessage.warning('请输入回复内容')
    return
  }
  submitting.value = true
  try {
    const data = {
      post_id: post.value.id,
      content: replyContent.value.trim(),
      parent_id: replyingTo.value.data.id,
      reply_to_user_id: replyingTo.value.data.author_id
    }

    await api.comments.create(data)
    ElMessage.success('回复成功')
    replyDialogVisible.value = false
    replyContent.value = ''
    loadComments()
  } catch (error) {
    console.error('回复失败:', error)
  } finally {
    submitting.value = false
  }
}

async function likeReply(reply) {
  try {
    await api.likes.like({ comment_id: reply.id })
    loadComments()
  } catch (error) {
    console.error('点赞失败:', error)
  }
}

async function likeComment(comment) {
  try {
    await api.likes.like({ comment_id: comment.id })
    loadComments()
  } catch (error) {
    console.error('点赞失败:', error)
  }
}

async function deleteComment(comment) {
  try {
    await ElMessageBox.confirm('确定要删除这条评论吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await api.comments.delete(comment.id)
    ElMessage.success('删除成功')
    loadComments()
    loadPost()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除评论失败:', error)
    }
  }
}

async function deletePost() {
  try {
    await ElMessageBox.confirm('确定要删除这篇帖子吗？删除后将无法恢复！', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await api.posts.delete(post.value.id)
    ElMessage.success('帖子已删除')
    router.push('/')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除帖子失败:', error)
    }
  }
}

async function handleUnhide() {
  try {
    await api.posts.hide(post.value.id)
    ElMessage.success('已取消隐藏')
    loadPost()
  } catch (error) {
    console.error('操作失败:', error)
    ElMessage.error('操作失败')
  }
}

async function handleRestore() {
  try {
    await ElMessageBox.confirm('确定要恢复这篇帖子吗？', '确认恢复', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await api.posts.restore(post.value.id)
    ElMessage.success('帖子已恢复')
    loadPost()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('恢复失败:', error)
      ElMessage.error('恢复失败')
    }
  }
}

function showReportDialog(type, data = null) {
  reportTarget.value = { type, data }
  reportForm.value = { reason: '', description: '' }
  reportDialogVisible.value = true
}

function reportComment(comment) {
  showReportDialog('comment', comment)
}

async function submitReport() {
  if (!reportForm.value.reason) {
    ElMessage.warning('请选择举报原因')
    return
  }
  submitting.value = true
  try {
    const data = {
      reason: reportForm.value.reason,
      description: reportForm.value.description
    }
    if (reportTarget.value.type === 'post') {
      data.post_id = post.value.id
    } else if (reportTarget.value.type === 'comment') {
      data.comment_id = reportTarget.value.data.id
    }
    await api.reports.create(data)
    ElMessage.success('举报成功')
    reportDialogVisible.value = false
  } catch (error) {
    console.error('举报失败:', error)
  } finally {
    submitting.value = false
  }
}

function goToUser(userId) {
  router.push(`/user/${userId}`)
}
</script>

<style lang="scss" scoped>
.post-detail {
  .post-info {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 20px 0;
  }

  .post-content {
    margin: 20px 0;
    line-height: 1.8;
    
    img {
      max-width: 100%;
      height: auto;
      display: block;
      margin: 10px 0;
    }
  }

  .post-actions {
    display: flex;
    gap: 12px;
  }
}

.comments-section {
  margin-top: 20px;

  .comments-header {
    font-size: 16px;
    font-weight: bold;
  }

  .comment-form {
    margin-bottom: 20px;
    padding-bottom: 20px;
    border-bottom: 1px solid #eee;
  }

  .comments-list {
    padding: 0;
  }
}

.share-content {
  text-align: center;

  .share-post-title {
    font-size: 16px;
    font-weight: 500;
    margin-bottom: 20px;
    color: #333;
  }

  .share-link {
    margin-bottom: 20px;
  }

  .share-qrcode {
    margin-bottom: 20px;

    canvas {
      border: 1px solid #eee;
      border-radius: 4px;
    }

    p {
      margin-top: 10px;
      font-size: 12px;
      color: #909399;
    }
  }

  .share-platforms {
    display: flex;
    justify-content: center;
    gap: 16px;

    .platform-icon {
      font-size: 14px;
      font-weight: bold;

      &.weibo {
        color: #e6162d;
      }

      &.qq {
        color: #12b7f5;
      }
    }
  }
}
</style>
