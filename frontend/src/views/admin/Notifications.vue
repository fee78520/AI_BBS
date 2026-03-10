<template>
  <div class="admin-notifications">
    <el-card>
      <h2>发送通知</h2>
      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
        <el-form-item label="目标类型" prop="target_type">
          <el-radio-group v-model="form.target_type">
            <el-radio label="all">全部用户</el-radio>
            <el-radio label="user">指定用户</el-radio>
            <el-radio label="role">指定角色</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item
          v-if="form.target_type === 'user'"
          label="选择用户"
          prop="target_id"
        >
          <el-select
            v-model="form.target_id"
            filterable
            remote
            reserve-keyword
            placeholder="搜索用户名"
            :remote-method="searchUser"
            :loading="searchLoading"
            style="width: 100%"
          >
            <el-option
              v-for="user in userOptions"
              :key="user.id"
              :label="`${user.username} (${user.nickname || '无昵称'})`"
              :value="user.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item
          v-if="form.target_type === 'role'"
          label="选择角色"
          prop="target_id"
        >
          <el-select v-model="form.target_id" placeholder="选择角色" style="width: 100%">
            <el-option label="管理员" :value="0" />
            <el-option label="版主" :value="1" />
            <el-option label="普通用户" :value="2" />
          </el-select>
        </el-form-item>

        <el-form-item label="通知类型" prop="notification_type">
          <el-select v-model="form.notification_type" placeholder="选择通知类型" style="width: 100%">
            <el-option label="系统通知" value="system" />
            <el-option label="公告" value="announcement" />
            <el-option label="活动" value="activity" />
          </el-select>
        </el-form-item>

        <el-form-item label="通知标题" prop="title">
          <el-input
            v-model="form.title"
            placeholder="请输入通知标题"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="通知内容" prop="content">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="6"
            placeholder="请输入通知内容"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            发送通知
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const formRef = ref(null)
const form = reactive({
  target_type: 'all',
  target_id: null,
  notification_type: 'system',
  title: '',
  content: ''
})

const rules = {
  title: [{ required: true, message: '请输入通知标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入通知内容', trigger: 'blur' }],
  target_id: [{ required: true, message: '请选择目标', trigger: 'change' }]
}

const userOptions = ref([])
const searchLoading = ref(false)
const submitting = ref(false)

async function searchUser(query) {
  if (!query) {
    return
  }

  searchLoading.value = true
  try {
    const response = await api.users.getList({
      page: 1,
      page_size: 10,
      search: query
    })
    userOptions.value = response.items || []
  } catch (error) {
    console.error('搜索用户失败:', error)
  } finally {
    searchLoading.value = false
  }
}

async function handleSubmit() {
  if (!formRef.value) return

  try {
    await formRef.value.validate()

    if (form.target_type === 'user' && !form.target_id) {
      ElMessage.warning('请选择目标用户')
      return
    }

    if (form.target_type === 'role' && form.target_id === null) {
      ElMessage.warning('请选择目标角色')
      return
    }

    submitting.value = true

    const data = {
      target_type: form.target_type,
      title: form.title,
      content: form.content,
      notification_type: form.notification_type
    }

    if (form.target_type === 'user' || form.target_type === 'role') {
      data.target_id = form.target_id
    }

    const response = await api.notifications.adminSend(data)
    ElMessage.success(response.message || '发送成功')
    handleReset()
  } catch (error) {
    console.error('发送通知失败:', error)
    ElMessage.error('发送通知失败')
  } finally {
    submitting.value = false
  }
}

function handleReset() {
  formRef.value?.resetFields()
  form.target_type = 'all'
  form.target_id = null
  form.notification_type = 'system'
  userOptions.value = []
}
</script>

<style lang="scss" scoped>
.admin-notifications {
  max-width: 800px;
  margin: 0 auto;
}
</style>
