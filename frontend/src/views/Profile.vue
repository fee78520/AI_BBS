<template>
  <div class="profile">
    <el-card>
      <h2>个人中心</h2>
      <el-form :model="user" label-width="80px">
        <el-form-item label="头像">
          <div class="avatar-upload">
            <el-upload
              class="avatar-uploader"
              action=""
              :show-file-list="false"
              :before-upload="beforeAvatarUpload"
              :http-request="handleAvatarUpload"
            >
              <el-avatar :size="100" :src="avatarUrl" class="avatar-preview">
                <el-icon :size="40"><User /></el-icon>
              </el-avatar>
              <div class="avatar-overlay">
                <el-icon><Camera /></el-icon>
                <span>更换头像</span>
              </div>
            </el-upload>
            <div class="avatar-tip">支持 jpg/png/gif/webp 格式，大小不超过 2MB</div>
          </div>
        </el-form-item>
        <el-form-item label="用户名">
          <el-input v-model="user.username" disabled />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="user.email" disabled />
        </el-form-item>
        <el-form-item label="签名">
          <el-input v-model="form.signature" placeholder="个性签名" />
        </el-form-item>
        <el-form-item label="简介">
          <el-input v-model="form.bio" type="textarea" placeholder="个人简介" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleUpdate" :loading="saving">保存</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 修改密码 -->
    <el-card class="password-card">
      <h3>修改密码</h3>
      <el-form :model="passwordForm" label-width="100px" :rules="passwordRules" ref="passwordFormRef">
        <el-form-item label="旧密码" prop="old_password">
          <el-input
            v-model="passwordForm.old_password"
            type="password"
            show-password
            placeholder="请输入旧密码"
          />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input
            v-model="passwordForm.new_password"
            type="password"
            show-password
            placeholder="请输入新密码（至少6位）"
          />
        </el-form-item>
        <el-form-item label="确认新密码" prop="confirm_password">
          <el-input
            v-model="passwordForm.confirm_password"
            type="password"
            show-password
            placeholder="请再次输入新密码"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleChangePassword" :loading="changingPassword">
            修改密码
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import { User, Camera } from '@element-plus/icons-vue'
import api from '@/api'

const router = useRouter()
const userStore = useUserStore()

const user = computed(() => userStore.user)
const form = ref({
  signature: '',
  bio: ''
})
const saving = ref(false)
const uploading = ref(false)

// 修改密码相关
const passwordFormRef = ref(null)
const changingPassword = ref(false)
const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const passwordRules = {
  old_password: [
    { required: true, message: '请输入旧密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.new_password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

const avatarUrl = computed(() => {
  if (form.value.avatar) {
    return form.value.avatar
  }
  return user.value?.avatar || ''
})

onMounted(() => {
  if (user.value) {
    form.value.signature = user.value.signature || ''
    form.value.bio = user.value.bio || ''
    form.value.avatar = user.value.avatar || ''
  }
})

function beforeAvatarUpload(file) {
  const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
  const isImage = allowedTypes.includes(file.type)
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isImage) {
    ElMessage.error('只能上传 jpg/png/gif/webp 格式的图片')
    return false
  }
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过 2MB')
    return false
  }
  return true
}

async function handleAvatarUpload(options) {
  uploading.value = true
  try {
    const res = await api.uploads.uploadImage(options.file)
    form.value.avatar = res.file_path
    // 立即更新头像
    await userStore.updateUser({ avatar: res.file_path })
    ElMessage.success('头像更新成功')
  } catch (error) {
    ElMessage.error('头像上传失败')
  } finally {
    uploading.value = false
  }
}

async function handleUpdate() {
  saving.value = true
  try {
    await userStore.updateUser(form.value)
    ElMessage.success('更新成功')
  } catch (error) {
    ElMessage.error('更新失败')
  } finally {
    saving.value = false
  }
}

async function handleChangePassword() {
  const valid = await passwordFormRef.value.validate().catch(() => false)
  if (!valid) return

  changingPassword.value = true
  try {
    await api.auth.changePassword({
      old_password: passwordForm.old_password,
      new_password: passwordForm.new_password
    })
    ElMessage.success('密码修改成功，请重新登录')
    // 清除登录状态
    userStore.logout()
    // 跳转到登录页
    router.push('/login')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '修改密码失败')
  } finally {
    changingPassword.value = false
  }
}
</script>

<style lang="scss" scoped>
.profile {
  max-width: 800px;
  margin: 0 auto;
}

.password-card {
  margin-top: 20px;

  h3 {
    margin-bottom: 20px;
    color: #303133;
  }
}

.avatar-upload {
  display: flex;
  align-items: center;
  gap: 20px;

  .avatar-uploader {
    position: relative;
    cursor: pointer;

    :deep(.el-upload) {
      position: relative;
      border-radius: 50%;
      overflow: hidden;

      &:hover .avatar-overlay {
        opacity: 1;
      }
    }

    .avatar-preview {
      border: 2px solid #dcdfe6;
      background-color: #f5f7fa;
    }

    .avatar-overlay {
      position: absolute;
      top: 0;
      left: 0;
      width: 100px;
      height: 100px;
      border-radius: 50%;
      background-color: rgba(0, 0, 0, 0.5);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      opacity: 0;
      transition: opacity 0.3s;
      color: white;
      font-size: 12px;

      .el-icon {
        font-size: 20px;
        margin-bottom: 4px;
      }
    }
  }

  .avatar-tip {
    font-size: 12px;
    color: #909399;
  }
}
</style>
