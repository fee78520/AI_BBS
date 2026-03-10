<template>
  <div class="forgot-password-page">
    <div class="forgot-container">
      <div class="forgot-header">
        <h1>找回密码</h1>
        <p>请输入您的邮箱或手机号</p>
      </div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        class="forgot-form"
      >
        <el-form-item prop="target">
          <el-input
            v-model="form.target"
            placeholder="请输入邮箱或手机号"
            size="large"
          />
        </el-form-item>

        <el-form-item prop="type">
          <el-radio-group v-model="form.type" size="large">
            <el-radio-button value="email">邮箱</el-radio-button>
            <el-radio-button value="phone">手机号</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            style="width: 100%"
            :loading="sending"
            @click="handleSendCode"
          >
            发送验证码
          </el-button>
        </el-form-item>
      </el-form>

      <div class="forgot-footer">
        <router-link to="/login">返回登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '@/api'

const router = useRouter()
const formRef = ref(null)
const sending = ref(false)

const form = reactive({
  target: '',
  type: 'email'
})

const rules = {
  target: [
    { required: true, message: '请输入邮箱或手机号', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择类型', trigger: 'change' }
  ]
}

async function handleSendCode() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  sending.value = true
  try {
    await api.auth.sendResetCode(form.target, form.type)
    ElMessage.success('验证码发送成功')
    // 跳转到重置密码页面，带上参数
    router.push({
      path: '/reset-password',
      query: {
        target: form.target,
        type: form.type
      }
    })
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '验证码发送失败')
  } finally {
    sending.value = false
  }
}
</script>

<style lang="scss" scoped>
.forgot-password-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

  .forgot-container {
    width: 400px;
    background: #fff;
    border-radius: 8px;
    padding: 40px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);

    .forgot-header {
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

    .forgot-form {
      margin-bottom: 20px;

      .el-radio-group {
        width: 100%;
        display: flex;

        .el-radio-button {
          flex: 1;
        }
      }
    }

    .forgot-footer {
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
