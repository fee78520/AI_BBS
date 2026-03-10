<template>
  <div class="admin-dashboard">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-value">{{ stats.total_users || 0 }}</div>
            <div class="stat-label">总用户数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-value">{{ stats.total_posts || 0 }}</div>
            <div class="stat-label">总帖子数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-value">{{ stats.total_comments || 0 }}</div>
            <div class="stat-label">总评论数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-value">{{ stats.active_users_today || 0 }}</div>
            <div class="stat-label">今日活跃用户</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api'

const stats = ref({})

onMounted(async () => {
  try {
    stats.value = await api.admin.getStatistics()
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
})
</script>

<style lang="scss" scoped>
.admin-dashboard {
  .stat-card {
    .stat-item {
      text-align: center;

      .stat-value {
        font-size: 32px;
        font-weight: bold;
        color: #409eff;
        margin-bottom: 8px;
      }

      .stat-label {
        color: #666;
        font-size: 14px;
      }
    }
  }
}
</style>
