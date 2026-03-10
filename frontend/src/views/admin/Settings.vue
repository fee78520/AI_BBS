<template>
  <div class="admin-settings">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>系统设置</span>
          <el-button type="primary" @click="saveSettings" :loading="saving">保存设置</el-button>
        </div>
      </template>

      <el-form :model="settings" label-width="150px" v-loading="loading">
        <el-divider content-position="left">基本设置</el-divider>
        
        <el-form-item label="网站名称">
          <el-input v-model="settings.site_name" placeholder="请输入网站名称" />
        </el-form-item>
        
        <el-form-item label="网站描述">
          <el-input v-model="settings.site_description" type="textarea" :rows="2" placeholder="请输入网站描述" />
        </el-form-item>
        
        <el-form-item label="网站关键词">
          <el-input v-model="settings.site_keywords" placeholder="多个关键词用逗号分隔" />
        </el-form-item>

        <el-divider content-position="left">注册设置</el-divider>
        
        <el-form-item label="允许注册">
          <el-switch v-model="settings.allow_register" />
        </el-form-item>
        
        <el-form-item label="邮箱验证">
          <el-switch v-model="settings.require_email_verify" />
        </el-form-item>
        
        <el-form-item label="默认用户组">
          <el-select v-model="settings.default_user_group" style="width: 200px">
            <el-option label="普通用户" value="normal" />
            <el-option label="VIP用户" value="vip" />
            <el-option label="荣誉用户" value="honor" />
          </el-select>
        </el-form-item>

        <el-divider content-position="left">发帖设置</el-divider>
        
        <el-form-item label="发帖需审核">
          <el-switch v-model="settings.post_require_review" />
        </el-form-item>
        
        <el-form-item label="帖子最小字数">
          <el-input-number v-model="settings.post_min_length" :min="1" :max="10000" />
        </el-form-item>
        
        <el-form-item label="帖子最大字数">
          <el-input-number v-model="settings.post_max_length" :min="100" :max="100000" />
        </el-form-item>

        <el-divider content-position="left">评论设置</el-divider>
        
        <el-form-item label="评论需审核">
          <el-switch v-model="settings.comment_require_review" />
        </el-form-item>
        
        <el-form-item label="评论最小字数">
          <el-input-number v-model="settings.comment_min_length" :min="1" :max="1000" />
        </el-form-item>
        
        <el-form-item label="评论最大字数">
          <el-input-number v-model="settings.comment_max_length" :min="10" :max="10000" />
        </el-form-item>

        <el-divider content-position="left">积分设置</el-divider>
        
        <el-form-item label="发帖积分">
          <el-input-number v-model="settings.points_per_post" :min="0" />
        </el-form-item>
        
        <el-form-item label="评论积分">
          <el-input-number v-model="settings.points_per_comment" :min="0" />
        </el-form-item>
        
        <el-form-item label="被点赞积分">
          <el-input-number v-model="settings.points_per_like" :min="0" />
        </el-form-item>

        <el-divider content-position="left">文件上传设置</el-divider>
        
        <el-form-item label="允许上传图片">
          <el-switch v-model="settings.allow_image_upload" />
        </el-form-item>
        
        <el-form-item label="图片最大尺寸(MB)">
          <el-input-number v-model="settings.max_image_size" :min="1" :max="50" />
        </el-form-item>
        
        <el-form-item label="允许的图片类型">
          <el-input v-model="settings.allowed_image_types" placeholder="如: jpg,jpeg,png,gif" />
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const loading = ref(false)
const saving = ref(false)
const settings = ref({
  site_name: '',
  site_description: '',
  site_keywords: '',
  allow_register: true,
  require_email_verify: false,
  default_user_group: 'normal',
  post_require_review: false,
  post_min_length: 10,
  post_max_length: 50000,
  comment_require_review: false,
  comment_min_length: 1,
  comment_max_length: 5000,
  points_per_post: 5,
  points_per_comment: 1,
  points_per_like: 1,
  allow_image_upload: true,
  max_image_size: 5,
  allowed_image_types: 'jpg,jpeg,png,gif,webp'
})

onMounted(() => {
  loadSettings()
})

async function loadSettings() {
  loading.value = true
  try {
    const data = await api.system.getList()
    // 将列表转换为对象
    if (data && Array.isArray(data)) {
      for (const item of data) {
        if (settings.value.hasOwnProperty(item.key)) {
          // 转换布尔值和数字
          let value = item.value
          if (value === 'true') value = true
          else if (value === 'false') value = false
          else if (!isNaN(value) && value !== '') value = Number(value)
          settings.value[item.key] = value
        }
      }
    }
  } catch (error) {
    console.error('加载设置失败:', error)
    // 尝试初始化默认设置
    try {
      await api.system.initDefaults()
      loadSettings()
    } catch (e) {
      console.error('初始化默认设置失败:', e)
    }
  } finally {
    loading.value = false
  }
}

async function saveSettings() {
  saving.value = true
  try {
    // 逐个更新设置
    for (const [key, value] of Object.entries(settings.value)) {
      await api.system.update(key, { value: String(value) })
    }
    ElMessage.success('设置已保存')
  } catch (error) {
    console.error('保存设置失败:', error)
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
