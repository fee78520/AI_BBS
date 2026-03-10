<template>
  <div class="register-page">
    <div class="register-container">
      <div class="register-header">
        <h1>欢迎注册</h1>
        <p>BBS论坛</p>
      </div>

      <!-- 注册方式选择 -->
      <div class="register-type-tabs">
        <el-radio-group v-model="registerType" size="large">
          <el-radio-button label="email">邮箱注册</el-radio-button>
          <el-radio-button label="phone" disabled>手机注册</el-radio-button>
        </el-radio-group>
      </div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        class="register-form"
        @submit.prevent="handleRegister"
      >
        <!-- 邮箱/手机号输入 -->
        <el-form-item :prop="registerType === 'email' ? 'email' : 'phone'">
          <el-input
            v-model="targetValue"
            :placeholder="registerType === 'email' ? '邮箱地址' : '手机号码'"
            size="large"
          >
            <template #prefix>
              <el-icon><Message v-if="registerType === 'email'" /><Iphone v-else /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <!-- 验证码输入 -->
        <el-form-item prop="code">
          <div class="code-input-wrapper">
            <el-input
              v-model="form.code"
              placeholder="验证码"
              size="large"
              maxlength="6"
            >
              <template #prefix>
                <el-icon><Key /></el-icon>
              </template>
            </el-input>
            <el-button
              type="primary"
              size="large"
              :disabled="countdown > 0 || !isTargetValid"
              :loading="sendingCode"
              @click="handleSendCode"
              style="width: 120px; margin-left: 10px;"
            >
              {{ countdown > 0 ? `${countdown}s` : '获取验证码' }}
            </el-button>
          </div>
        </el-form-item>

        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="用户名"
            size="large"
          >
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            size="large"
            show-password
          >
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item prop="confirmPassword">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            placeholder="确认密码"
            size="large"
            show-password
          >
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            native-type="submit"
            :loading="loading"
            style="width: 100%"
          >
            注册
          </el-button>
        </el-form-item>
      </el-form>

      <div class="register-footer">
        <span>已有账号？</span>
        <router-link to="/login">立即登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Message, Iphone, Key } from '@element-plus/icons-vue'
import api from '@/api'

const router = useRouter()

const formRef = ref(null)
const loading = ref(false)
const sendingCode = ref(false)
const countdown = ref(0)
const registerType = ref('email') // email 或 phone

const form = reactive({
  email: '',
  phone: '',
  code: '',
  username: '',
  password: '',
  confirmPassword: ''
})

// 计算属性：根据注册类型获取当前目标输入框的值
const targetValue = computed({
  get() {
    return registerType.value === 'email' ? form.email : form.phone
  },
  set(value) {
    if (registerType.value === 'email') {
      form.email = value
    } else {
      form.phone = value
    }
  }
})

// 验证目标（邮箱/手机号）是否有效
const isTargetValid = computed(() => {
  if (registerType.value === 'email') {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)
  } else {
    return /^1[3-9]\d{9}$/.test(form.phone)
  }
})

const validatePass = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请输入密码'))
  } else if (value.length < 6) {
    callback(new Error('密码长度至少6位'))
  } else {
    if (form.confirmPassword !== '') {
      formRef.value.validateField('confirmPassword')
    }
    callback()
  }
}

const validatePass2 = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== form.password) {
    callback(new Error('两次输入密码不一致'))
  } else {
    callback()
  }
}

const validateCode = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请输入验证码'))
  } else if (!/^\d{6}$/.test(value)) {
    callback(new Error('验证码为6位数字'))
  } else {
    callback()
  }
}

const validateEmail = (rule, value, callback) => {
  if (registerType.value !== 'email') {
    callback()
    return
  }
  if (value === '') {
    callback(new Error('请输入邮箱'))
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
    callback(new Error('请输入正确的邮箱地址'))
  } else {
    callback()
  }
}

const validatePhone = (rule, value, callback) => {
  if (registerType.value !== 'phone') {
    callback()
    return
  }
  if (value === '') {
    callback(new Error('请输入手机号'))
  } else if (!/^1[3-9]\d{9}$/.test(value)) {
    callback(new Error('请输入正确的手机号'))
  } else {
    callback()
  }
}

const rules = {
  email: [{ required: true, validator: validateEmail, trigger: 'blur' }],
  phone: [{ required: true, validator: validatePhone, trigger: 'blur' }],
  code: [{ required: true, validator: validateCode, trigger: 'blur' }],
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度在3-50个字符', trigger: 'blur' }
  ],
  password: [{ required: true, validator: validatePass, trigger: 'blur' }],
  confirmPassword: [{ required: true, validator: validatePass2, trigger: 'blur' }]
}

// 发送验证码
async function handleSendCode() {
  const target = registerType.value === 'email' ? form.email : form.phone
  
  if (!isTargetValid.value) {
    ElMessage.warning(registerType.value === 'email' ? '请输入正确的邮箱地址' : '请输入正确的手机号')
    return
  }

  sendingCode.value = true
  try {
    await api.auth.sendCode(target, registerType.value)
    ElMessage.success('验证码已发送')
    // 开始倒计时
    countdown.value = 60
    const timer = setInterval(() => {
      countdown.value--
      if (countdown.value <= 0) {
        clearInterval(timer)
      }
    }, 1000)
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '验证码发送失败')
  } finally {
    sendingCode.value = false
  }
}

// 注册
async function handleRegister() {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch {
    return
  }

  loading.value = true
  try {
    const target = registerType.value === 'email' ? form.email : form.phone
    await api.auth.registerWithCode({
      username: form.username,
      password: form.password,
      target: target,
      code: form.code,
      type: registerType.value
    })
    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.register-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

  .register-container {
    width: 420px;
    background: #fff;
    border-radius: 8px;
    padding: 40px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);

    .register-header {
      text-align: center;
      margin-bottom: 20px;

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

    .register-type-tabs {
      display: flex;
      justify-content: center;
      margin-bottom: 20px;

      :deep(.el-radio-group) {
        width: 100%;
      }

      :deep(.el-radio-button) {
        flex: 1;
      }

      :deep(.el-radio-button__inner) {
        width: 100%;
      }
    }

    .register-form {
      margin-bottom: 20px;
    }

    .code-input-wrapper {
      display: flex;
      width: 100%;
    }

    .register-footer {
      text-align: center;
      color: #666;
      font-size: 14px;

      a {
        color: #409eff;
        margin-left: 8px;

        &:hover {
          text-decoration: underline;
        }
      }
    }
  }
}
</style>
