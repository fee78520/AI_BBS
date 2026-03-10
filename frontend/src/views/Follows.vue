<template>
  <div class="follows">
    <el-tabs v-model="activeTab" @tab-change="handleTabChange">
      <el-tab-pane label="我关注的" name="following">
        <el-card v-loading="loading">
          <el-empty v-if="!loading && followingItems.length === 0" description="暂无关注" />
          <div v-else>
            <el-table :data="followingItems" style="width: 100%">
              <el-table-column label="用户" min-width="200">
                <template #default="{ row }">
                  <div class="user-cell">
                    <el-avatar :size="40" :src="row.avatar" />
                    <div class="user-info">
                      <div class="username">{{ row.username }}</div>
                      <div class="nickname">{{ row.nickname || '无昵称' }}</div>
                    </div>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="post_count" label="帖子" width="80" />
              <el-table-column prop="follower_count" label="粉丝" width="80" />
              <el-table-column label="关注时间" width="180">
                <template #default="{ row }">
                  {{ formatDate(row.followed_at) }}
                </template>
              </el-table-column>
              <el-table-column label="操作" width="120">
                <template #default="{ row }">
                  <el-button type="danger" size="small" @click="handleUnfollow(row)">
                    取消关注
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
            <el-pagination
              v-if="followingTotal > 0"
              :current-page="followingPage"
              :page-size="20"
              :total="followingTotal"
              @current-change="loadFollowing"
              layout="prev, pager, next, jumper"
              style="margin-top: 20px; text-align: center"
            />
          </div>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="关注我的" name="followers">
        <el-card v-loading="loading">
          <el-empty v-if="!loading && followerItems.length === 0" description="暂无粉丝" />
          <div v-else>
            <el-table :data="followerItems" style="width: 100%">
              <el-table-column label="用户" min-width="200">
                <template #default="{ row }">
                  <div class="user-cell">
                    <el-avatar :size="40" :src="row.avatar" />
                    <div class="user-info">
                      <div class="username">{{ row.username }}</div>
                      <div class="nickname">{{ row.nickname || '无昵称' }}</div>
                    </div>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="post_count" label="帖子" width="80" />
              <el-table-column prop="follower_count" label="粉丝" width="80" />
              <el-table-column label="关注时间" width="180">
                <template #default="{ row }">
                  {{ formatDate(row.followed_at) }}
                </template>
              </el-table-column>
              <el-table-column label="操作" width="120">
                <template #default="{ row }">
                  <el-button
                    v-if="!isFollowing(row.id)"
                    type="primary"
                    size="small"
                    @click="handleFollow(row)"
                  >
                    关注
                  </el-button>
                  <el-button
                    v-else
                    type="danger"
                    size="small"
                    @click="handleUnfollow(row)"
                  >
                    取消关注
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
            <el-pagination
              v-if="followerTotal > 0"
              :current-page="followerPage"
              :page-size="20"
              :total="followerTotal"
              @current-change="loadFollowers"
              layout="prev, pager, next, jumper"
              style="margin-top: 20px; text-align: center"
            />
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const activeTab = ref('following')
const loading = ref(false)

// 我关注的
const followingItems = ref([])
const followingPage = ref(1)
const followingTotal = ref(0)

// 关注我的
const followerItems = ref([])
const followerPage = ref(1)
const followerTotal = ref(0)

onMounted(() => {
  loadFollowing()
})

function handleTabChange(tab) {
  if (tab === 'following') {
    loadFollowing()
  } else {
    loadFollowers()
  }
}

async function loadFollowing() {
  loading.value = true
  try {
    const response = await api.follows.getFollowing({
      page: followingPage.value,
      page_size: 20
    })
    followingItems.value = response.items || []
    followingTotal.value = response.total || 0
  } catch (error) {
    console.error('加载关注列表失败:', error)
    ElMessage.error('加载关注列表失败')
  } finally {
    loading.value = false
  }
}

async function loadFollowers() {
  loading.value = true
  try {
    const response = await api.follows.getFollowers({
      page: followerPage.value,
      page_size: 20
    })
    followerItems.value = response.items || []
    followerTotal.value = response.total || 0
  } catch (error) {
    console.error('加载粉丝列表失败:', error)
    ElMessage.error('加载粉丝列表失败')
  } finally {
    loading.value = false
  }
}

async function handleFollow(user) {
  try {
    await api.follows.follow({ followed_id: user.id })
    ElMessage.success('关注成功')
    // 重新加载当前列表
    if (activeTab.value === 'following') {
      loadFollowing()
    } else {
      loadFollowers()
    }
  } catch (error) {
    console.error('关注失败:', error)
    ElMessage.error('关注失败')
  }
}

async function handleUnfollow(user) {
  try {
    await api.follows.unfollow(user.id)
    ElMessage.success('已取消关注')
    // 重新加载当前列表
    if (activeTab.value === 'following') {
      loadFollowing()
    } else {
      loadFollowers()
    }
  } catch (error) {
    console.error('取消关注失败:', error)
    ElMessage.error('取消关注失败')
  }
}

function isFollowing(userId) {
  return followingItems.value.some(item => item.id === userId)
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}
</script>

<style lang="scss" scoped>
.follows {
  max-width: 1000px;
  margin: 0 auto;

  .user-cell {
    display: flex;
    align-items: center;
    gap: 12px;

    .user-info {
      .username {
        font-weight: 500;
        color: #333;
      }

      .nickname {
        font-size: 12px;
        color: #999;
      }
    }
  }
}
</style>
