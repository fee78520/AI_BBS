<template>
  <div class="reset-password-page">
    <div class="reset-container">
      <div class="reset-header">
        <h1>重置密码</h1>
        <p>请输入验证码和新密码</p>
      </div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        class="reset-form"
      >
        <el-form-item>
          <el-input
            :model-value="form.target"
            disabled
            size="large"
          />
        </el-form-item>

        <el-form-item prop="code">
          <el-input
            v-model="form.code"
            placeholder="请输入验证码"
            size="large"
            maxlength="6"
          />
        </el-form-item>

        <el-form-item prop="new_password">
          <el-input
            v-model="form.new_password"
            type="password"
            placeholder="请输入新密码（至少6位）"
            size="large"
            show-password
          />
        </el-form-item>

        <el-form-item prop="confirm_password">
          <el-input
            v-model="form.confirm_password"
            type="password"
            placeholder="请确认新密码"
            size="large"
            show-password
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            style="width: 100%"
            :loading="resetting"
            @click="handleReset"
          >
            重置密码
          </el-button>
        </el-form-item>
      </el-form>

      <div class="reset-footer">
        <router-link to="/login">返回登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '@/api'

const router = useRouter()
const route = useRoute()
const formRef = ref(null)
const resetting = ref(false)

const form = reactive({
  target: '',
  type: 'email',
  code: '',
  new_password: '',
  confirm_password: ''
})

const rules = {
  code: [
    { required: true, message: '请输入验证码', trigger: 'blur' },
    { len: 6, message: '验证码为6位数字', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== form.new_password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

onMounted(() => {
  // 从路由参数获取 target 和 type
  if (route.query.target) {
    form.target = route.query.target
  }
  if (route.query.type) {
    form.type = route.query.type
  }

  // 如果没有参数，跳转到忘记密码页面
  if (!form.target) {
    router.push('/forgot-password')
  }
})

async function handleReset() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  resetting.value = true
  try {
    await api.auth.resetPassword({
      target: form.target,
      code: form.code,
      new_password: form.new_password,
      type: form.type
    })
    ElMessage.success('密码重置成功，请登录')
    router.push('/login')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '密码重置失败')
  } finally {
    resetting.value = false
  }
}
</script>

<style lang="scss" scoped>
.reset-password-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

  .reset-container {
    width: 400px;
    background: #fff;
    border-radius: 8px;
    padding: 40px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);

    .reset-header {
      text-align: center;
      margin-bottom: 30px;

      h1 {
        font-size: 28px;
        color: #333;
        margin-bottom: 8px;
      }

      p {
        color: #999;
        font-size: 14px;
      }
    }

    .reset-form {
      margin-bottom: 20px;
    }

    .reset-footer {
      text-align: center;

      a {
        color: #409eff;
        font-size: 14px;

        &:hover {
          text-decoration: underline;
        }
      }
    }
  }
}
</style>
