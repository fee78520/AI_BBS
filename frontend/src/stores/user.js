/**
 * BBS论坛系统 - 用户状态管理
 * 本文件负责：
 * 1. 管理用户登录状态
 * 2. 存储和管理用户信息
 * 3. 管理JWT Token
 * 4. 提供用户相关的操作方法
 * 
 * 使用Pinia进行状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const useUserStore = defineStore('user', () => {
  // ========== 状态定义 ==========

  // 用户信息对象
  const user = ref(null)

  // JWT Token（从localStorage初始化）
  const token = ref(localStorage.getItem('token'))

  // 刷新Token（从localStorage初始化）
  const refreshToken = ref(localStorage.getItem('refresh_token'))

  // ========== 计算属性 ==========

  /**
   * 是否已登录
   * Token存在且用户信息存在即视为已登录
   */
  const isLoggedIn = computed(() => !!token.value && !!user.value)

  // ========== 异步操作 ==========

  /**
   * 用户登录
   * 支持用户名/手机号/邮箱登录
   *
   * @param {string} username - 用户名/手机号/邮箱
   * @param {string} password - 密码
   * @returns {Promise<boolean>} 登录是否成功
   *
   * @example
   * const success = await userStore.login('admin', '123456')
   */
  async function login(username, password) {
    try {
      // 调用后端登录接口（使用JSON格式）
      const response = await api.auth.loginJson(username, password)
      // 保存Token和刷新Token
      token.value = response.access_token
      refreshToken.value = response.refresh_token
      localStorage.setItem('token', response.access_token)
      localStorage.setItem('refresh_token', response.refresh_token)
      // 获取用户信息
      await getUserInfo()
      return true
    } catch (error) {
      console.error('登录失败:', error)
      return false
    }
  }

  /**
   * 设置Token和刷新Token
   * 用于Token刷新后更新store和localStorage
   *
   * @param {string} accessToken - 新的访问令牌
   * @param {string} newRefreshToken - 新的刷新令牌
   */
  function setTokens(accessToken, newRefreshToken) {
    token.value = accessToken
    refreshToken.value = newRefreshToken
    localStorage.setItem('token', accessToken)
    localStorage.setItem('refresh_token', newRefreshToken)
  }

  /**
   * 用户注册
   * 
   * @param {Object} userData - 用户注册数据
   * @param {string} userData.username - 用户名
   * @param {string} userData.email - 邮箱
   * @param {string} userData.password - 密码
   * @param {string} [userData.phone] - 手机号（可选）
   * @returns {Promise<boolean>} 注册是否成功
   * 
   * @example
   * const success = await userStore.register({
   *   username: 'newuser',
   *   email: 'user@example.com',
   *   password: '123456'
   * })
   */
  async function register(userData) {
    try {
      // 调用后端注册接口
      await api.auth.register(userData)
      return true
    } catch (error) {
      console.error('注册失败:', error)
      return false
    }
  }

  /**
   * 获取当前用户信息
   * 
   * @returns {Promise<Object|null>} 用户信息对象，失败返回null
   * 
   * @example
   * const userInfo = await userStore.getUserInfo()
   * console.log(userInfo.username)
   */
  async function getUserInfo() {
    try {
      // 调用后端获取当前用户信息接口
      const response = await api.auth.getMe()
      user.value = response
      return response
    } catch (error) {
      console.error('获取用户信息失败:', error)
      // Token失效，执行登出
      logout()
      return null
    }
  }

  /**
   * 检查登录状态
   * 
   * 在应用启动时调用，如果Token存在则获取用户信息
   * 
   * @example
   * // 在App.vue中调用
   * onMounted(() => {
   *   userStore.checkAuth()
   * })
   */
  async function checkAuth() {
    if (token.value) {
      // Token存在，尝试获取用户信息
      await getUserInfo()
    }
  }

  /**
   * 用户登出
   * 
   * 清除Token和用户信息
   * 
   * @example
   * userStore.logout()
   * // 自动跳转到登录页（路由守卫）
   */
  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
  }

  /**
   * 更新用户信息
   * 
   * @param {Object} userData - 要更新的用户数据
   * @param {string} [userData.signature] - 个性签名
   * @param {string} [userData.bio] - 个人简介
   * @returns {Promise<Object>} 更新后的用户信息
   * 
   * @example
   * const updatedUser = await userStore.updateUser({
   *   signature: '这是我的个性签名',
   *   bio: '这是我的个人简介'
   * })
   */
  function updateUser(userData) {
    return api.users.updateMe(userData).then(response => {
      // 合并用户信息
      user.value = { ...user.value, ...response }
      return response
    })
  }

  // ========== 导出状态和方法 ==========
  return {
    user,           // 用户信息
    token,         // JWT Token
    refreshToken,   // 刷新Token
    isLoggedIn,    // 是否已登录
    login,         // 登录方法
    register,      // 注册方法
    getUserInfo,   // 获取用户信息
    checkAuth,     // 检查登录状态
    logout,        // 登出方法
    updateUser,    // 更新用户信息
    setTokens      // 设置Token和刷新Token
  }
})

