<template>
  <div class="comment-item" :class="{ 'is-reply': isReply }">
    <div class="comment-avatar">
      <el-avatar :size="isReply ? 24 : 36" :src="comment.author?.avatar" />
    </div>
    <div class="comment-content">
      <div class="comment-header">
        <span class="comment-author" @click="$emit('view-user', comment.author?.id)">
          {{ comment.author?.username }}
        </span>
        <span v-if="comment.reply_to_user" class="reply-to">
          回复 <span class="reply-to-user">@{{ comment.reply_to_user?.username }}</span>
        </span>
        <span class="comment-time">{{ formatDateTime(comment.created_at, 'MM-DD HH:mm') }}</span>
      </div>
      <div class="comment-text">{{ comment.content }}</div>
      <div class="comment-actions">
        <el-button text size="small" @click="$emit('reply', comment)">
          <el-icon><ChatDotRound /></el-icon>
          回复
        </el-button>
        <el-button text size="small" @click="$emit('like', comment)">
          <el-icon><Pointer /></el-icon>
          {{ comment.like_count || 0 }}
        </el-button>
        <el-button v-if="canDelete" text size="small" type="danger" @click="$emit('delete', comment)">
          <el-icon><Delete /></el-icon>
          删除
        </el-button>
        <el-button v-if="currentUserId" text size="small" @click="$emit('report', comment)">
          <el-icon><Warning /></el-icon>
          举报
        </el-button>
      </div>

      <!-- 递归渲染子评论 -->
      <div v-if="comment.replies && comment.replies.length > 0" class="replies-list">
        <el-collapse-transition>
          <div v-show="!showAllReplies">
            <CommentItem
              v-for="reply in comment.replies.slice(0, 3)"
              :key="reply.id"
              :comment="reply"
              :current-user-id="currentUserId"
              :is-reply="true"
              @reply="$emit('reply', $event)"
              @like="$emit('like', $event)"
              @delete="$emit('delete', $event)"
              @view-user="$emit('view-user', $event)"
            />
            <el-button
              v-if="comment.replies.length > 3"
              text
              size="small"
              type="primary"
              @click="toggleReplies"
            >
              展开全部 {{ comment.replies.length }} 条回复
            </el-button>
          </div>
        </el-collapse-transition>

        <el-collapse-transition>
          <div v-show="showAllReplies">
            <CommentItem
              v-for="reply in comment.replies"
              :key="reply.id"
              :comment="reply"
              :current-user-id="currentUserId"
              :is-reply="true"
              @reply="$emit('reply', $event)"
              @like="$emit('like', $event)"
              @delete="$emit('delete', $event)"
              @view-user="$emit('view-user', $event)"
            />
            <el-button
              v-if="comment.replies.length > 3"
              text
              size="small"
              type="primary"
              @click="toggleReplies"
            >
              收起回复
            </el-button>
          </div>
        </el-collapse-transition>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { ChatDotRound, Pointer, Delete, Warning } from '@element-plus/icons-vue'
import { formatDateTime } from '@/utils/time'

const props = defineProps({
  comment: {
    type: Object,
    required: true
  },
  currentUserId: {
    type: Number,
    default: null
  },
  isReply: {
    type: Boolean,
    default: false
  }
})

const canDelete = computed(() => {
  return props.currentUserId === props.comment.author_id
})

// 回复折叠控制
const showAllReplies = ref(false)

const toggleReplies = () => {
  showAllReplies.value = !showAllReplies.value
}

defineEmits(['reply', 'like', 'delete', 'report', 'view-user'])
</script>

<style lang="scss" scoped>
.comment-item {
  display: flex;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;

  &.is-reply {
    padding: 8px 0;
    margin-left: 40px;
    border-bottom: none;
  }

  &:last-child {
    border-bottom: none;
  }

  .comment-avatar {
    flex-shrink: 0;
  }

  .comment-content {
    flex: 1;
    min-width: 0;
  }

  .comment-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 4px;
    flex-wrap: wrap;

    .comment-author {
      font-weight: 500;
      color: #409eff;
      cursor: pointer;

      &:hover {
        text-decoration: underline;
      }
    }

    .reply-to {
      font-size: 13px;
      color: #909399;

      .reply-to-user {
        color: #409eff;
      }
    }

    .comment-time {
      font-size: 12px;
      color: #909399;
    }
  }

  .comment-text {
    color: #303133;
    line-height: 1.6;
    margin-bottom: 8px;
    word-break: break-all;
  }

  .comment-actions {
    display: flex;
    gap: 8px;
  }

  .replies-list {
    margin-top: 12px;
  }
}
</style>
