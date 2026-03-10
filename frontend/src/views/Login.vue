<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-header">
        <h1>欢迎登录</h1>
        <p>BBS论坛</p>
      </div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        class="login-form"
        @submit.prevent="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="用户名"
            size="large"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            size="large"
            show-password
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            native-type="submit"
            :loading="loading"
            style="width: 100%"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-footer">
        <router-link to="/forgot-password" class="forgot-link">忘记密码？</router-link>
        <span class="divider">|</span>
        <span>还没有账号？</span>
        <router-link to="/register">立即注册</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ]
}

async function handleLogin() {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch {
    return
  }

  loading.value = true
  const success = await userStore.login(form.username, form.password)
  loading.value = false

  if (success) {
    ElMessage.success('登录成功')
    const redirect = route.query.redirect || '/'
    router.push(redirect)
  } else {
    ElMessage.error('登录失败，请检查用户名和密码')
  }
}
</script>

<style lang="scss" scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

  .login-container {
    width: 400px;
    background: #fff;
    border-radius: 8px;
    padding: 40px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);

    .login-header {
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

    .login-form {
      margin-bottom: 20px;
    }

    .login-footer {
      text-align: center;
      color: #666;
      font-size: 14px;

      .forgot-link {
        color: #909399;
        &:hover {
          color: #409eff;
        }
      }

      .divider {
        margin: 0 12px;
        color: #dcdfe6;
      }

      a {
        color: #409eff;
        margin-left: 4px;

        &:hover {
          text-decoration: underline;
        }
      }
    }
  }
}
</style>
