/**
 * BBS论坛系统 - API接口封装
 * 本文件负责：
 * 1. 创建Axios实例并配置默认设置
 * 2. 配置请求拦截器（添加认证Token）
 * 3. 配置响应拦截器（统一错误处理）
 * 4. 封装所有后端API接口
 * 5. 导出统一的API对象供组件使用
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

// ========== Axios实例配置 ==========
const request = axios.create({
  baseURL: '/api',  // API基础路径（会被Vite代理到后端）
  timeout: 30000  // 请求超时时间：30秒
})

// ========== 请求拦截器 ==========
request.interceptors.request.use(
  config => {
    // 在发送请求之前做些什么
    const userStore = useUserStore()
    // 如果用户已登录，自动添加JWT Token到请求头
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`
    }
    return config
  },
  error => {
    // 对请求错误做些什么
    return Promise.reject(error)
  }
)

// ========== 响应拦截器 ==========
// 用于存储正在刷新token的请求
let isRefreshing = false
let refreshSubscribers = []

// 添加订阅者函数
function subscribeTokenRefresh(cb) {
  refreshSubscribers.push(cb)
}

// 执行订阅者函数
function onRefreshed(token) {
  refreshSubscribers.forEach(cb => cb(token))
  refreshSubscribers = []
}

request.interceptors.response.use(
  response => {
    // 对响应数据做点什么
    // 直接返回响应数据（不包含headers等）
    return response.data
  },
  async error => {
    const originalRequest = error.config

    // 对响应错误做点什么
    const message = error.response?.data?.detail || error.message || '请求失败'

    // Token过期处理（401错误且未尝试过刷新）
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      const userStore = useUserStore()

      // 如果有刷新token，尝试刷新
      if (userStore.refreshToken) {
        if (!isRefreshing) {
          isRefreshing = true
          try {
            // 调用刷新token接口
            const response = await api.auth.refreshToken(userStore.refreshToken)
            const { access_token, refresh_token } = response

            // 更新store中的token
            userStore.setTokens(access_token, refresh_token)

            isRefreshing = false
            onRefreshed(access_token)

            // 重试原始请求
            originalRequest.headers.Authorization = `Bearer ${access_token}`
            return request(originalRequest)
          } catch (refreshError) {
            isRefreshing = false
            // 刷新失败，清除登录状态
            userStore.logout()
            ElMessage.error('登录已过期，请重新登录')
            window.location.href = '/login'
            return Promise.reject(refreshError)
          }
        } else {
          // 如果正在刷新，将请求加入队列
          return new Promise((resolve) => {
            subscribeTokenRefresh(token => {
              originalRequest.headers.Authorization = `Bearer ${token}`
              resolve(request(originalRequest))
            })
          })
        }
      } else {
        // 没有刷新token，直接清除登录状态
        userStore.logout()
        ElMessage.error('登录已过期，请重新登录')
        window.location.href = '/login'
      }
    } else if (error.response?.status === 403) {
      // 403: 禁止访问，权限不足
      ElMessage.error('没有权限访问')
    } else if (error.response?.status === 404) {
      // 404: 资源不存在
      ElMessage.error('请求的资源不存在')
    } else if (error.response?.status === 422) {
      // 422: 参数验证失败
      ElMessage.error('请求参数错误')
    } else if (error.response?.status === 500) {
      // 500: 服务器内部错误
      ElMessage.error('服务器错误，请稍后重试')
    } else {
      // 其他错误
      ElMessage.error(message)
    }

    return Promise.reject(error)
  }
)

// ========== API接口封装 ==========
const api = {
  // ========== 认证接口 ==========
  auth: {
    register: (data) => request.post('/auth/register', data),  // 用户注册
    sendCode: (target, type) => request.post('/auth/send-code', { target, type }),  // 发送验证码
    registerWithCode: (data) => request.post('/auth/register-with-code', data),  // 验证码注册
    login: (username, password) => {  // 用户登录（表单格式，支持用户名/手机号/邮箱）
      const formData = new FormData()
      formData.append('username', username)
      formData.append('password', password)
      return request.post('/auth/login', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
    },
    loginJson: (username, password) => {  // 用户登录（JSON格式，支持用户名/手机号/邮箱）
      return request.post('/auth/login/json', { username, password })
    },
    refreshToken: (refreshToken) => request.post('/auth/refresh', { refresh_token: refreshToken }),  // 刷新访问令牌
    getMe: () => request.get('/auth/me'),  // 获取当前用户信息
    logout: () => request.post('/auth/logout'),  // 用户登出
    changePassword: (data) => request.post('/auth/change-password', data),  // 修改密码
    sendResetCode: (target, type) => request.post('/auth/send-reset-code', { target, type }),  // 发送重置密码验证码
    resetPassword: (data) => request.post('/auth/reset-password', data)  // 重置密码
  },

  // ========== 用户接口 ==========
  users: {
    getMe: () => request.get('/users/me'),  // 获取当前用户信息
    updateMe: (data) => request.put('/users/me', data),  // 更新当前用户信息
    getById: (id) => request.get(`/users/${id}`),  // 根据ID获取用户信息
    getUserPosts: (id, params) => request.get(`/users/${id}/posts`, { params }),  // 获取用户的帖子
    getHotUsers: (params) => request.get('/users/hot', { params }),  // 获取热门用户（公开）
    getList: (params) => request.get('/users/', { params }),  // 获取用户列表（管理员）
    deleteMe: () => request.delete('/users/me'),  // 删除当前用户账号
    banUser: (id, data) => request.post(`/users/${id}/ban`, data),  // 封禁用户（管理员）
    unbanUser: (id) => request.post(`/users/${id}/unban`)  // 解封用户（管理员）
  },

  // ========== 版块接口 ==========
  categories: {
    getList: (params) => request.get('/categories/', { params }),  // 获取版块列表
    getById: (id) => request.get(`/categories/${id}`),  // 获取版块详情
    create: (data) => request.post('/categories/', data),  // 创建版块（管理员）
    update: (id, data) => request.put(`/categories/${id}`, data),  // 更新版块（管理员）
    delete: (id) => request.delete(`/categories/${id}`),  // 删除版块（管理员）
    addModerator: (categoryId, userId) =>  // 添加版主（管理员）
      request.post(`/categories/${categoryId}/moderators/${userId}`),
    removeModerator: (categoryId, userId) =>  // 移除版主（管理员）
      request.delete(`/categories/${categoryId}/moderators/${userId}`)
  },

  // ========== 帖子接口 ==========
  posts: {
    getList: (params) => request.get('/posts/', { params }),  // 获取帖子列表
    getHot: (params) => request.get('/posts/hot', { params }),  // 获取热门帖子
    getTrash: (params) => request.get('/posts/trash', { params }),  // 获取回收站帖子（管理员）
    getById: (id) => request.get(`/posts/${id}`),  // 获取帖子详情
    create: (data) => request.post('/posts/', data),  // 创建帖子
    update: (id, data) => request.put(`/posts/${id}`, data),  // 更新帖子
    delete: (id) => request.delete(`/posts/${id}`),  // 删除帖子
    restore: (id) => request.post(`/posts/${id}/restore`),  // 恢复已删除的帖子（管理员）
    pin: (id) => request.post(`/posts/${id}/pin`),  // 置顶/取消置顶帖子（版主/管理员）
    lock: (id) => request.post(`/posts/${id}/lock`),  // 锁定/解锁帖子（版主/管理员）
    setEssence: (id) => request.post(`/posts/${id}/essence`),  // 设为精华/取消精华（版主/管理员）
    hide: (id) => request.post(`/posts/${id}/hide`)  // 隐藏/取消隐藏帖子（版主/管理员）
  },

  // ========== 评论接口 ==========
  comments: {
    getByPost: (postId, params) => request.get(`/comments/post/${postId}`, { params }),  // 获取帖子评论
    create: (data) => request.post('/comments/', data),  // 创建评论
    update: (id, data) => request.put(`/comments/${id}`, data),  // 更新评论
    delete: (id) => request.delete(`/comments/${id}`),  // 删除评论
    hide: (id) => request.post(`/comments/${id}/hide`)  // 隐藏/取消隐藏评论（版主/管理员）
  },

  // ========== 点赞接口 ==========
  likes: {
    like: (data) => request.post('/likes/', data),  // 点赞/取消点赞
    check: (params) => request.get('/likes/check', { params }),  // 检查点赞状态
    getLikedPosts: (params) => request.get('/likes/posts', { params }),  // 获取点赞的帖子列表
    getLikedComments: (params) => request.get('/likes/comments', { params })  // 获取点赞的评论列表
  },

  // ========== 收藏接口 ==========
  favorites: {
    add: (data) => request.post('/favorites/', data),  // 添加收藏
    remove: (postId) => request.delete(`/favorites/${postId}`),  // 取消收藏
    getList: (params) => request.get('/favorites/', { params })  // 获取收藏列表
  },

  // ========== 关注接口 ==========
  follows: {
    follow: (data) => request.post('/follows/', data),  // 关注用户
    unfollow: (userId) => request.delete(`/follows/${userId}`),  // 取消关注
    getFollowing: (params) => request.get('/follows/following', { params }),  // 获取关注列表
    getFollowers: (params) => request.get('/follows/followers', { params })  // 获取粉丝列表
  },

  // ========== 私信接口 ==========
  messages: {
    send: (data) => request.post('/messages/', data),  // 发送私信
    getInbox: (params) => request.get('/messages/inbox', { params }),  // 获取收件箱
    getSent: (params) => request.get('/messages/sent', { params }),  // 获取已发送消息
    getById: (id) => request.get(`/messages/${id}`),  // 获取消息详情
    markAsRead: (id) => request.put(`/messages/${id}/read`),  // 标记消息为已读
    markAllAsRead: () => request.post('/messages/read-all'),  // 标记所有消息为已读
    delete: (id) => request.delete(`/messages/${id}`),  // 删除消息
    // 对话相关接口
    getConversations: () => request.get('/messages/conversations'),  // 获取对话列表
    getConversationMessages: (userId, params) => request.get(`/messages/conversations/${userId}`, { params }),  // 获取对话消息
    markConversationRead: (userId) => request.put(`/messages/conversations/${userId}/read`),  // 标记对话已读
    getUnreadCount: () => request.get('/messages/unread-count')  // 获取私信未读数
  },

  // ========== 通知接口 ==========
  notifications: {
    getList: (params) => request.get('/notifications/', { params }),  // 获取通知列表
    getUnreadCount: () => request.get('/notifications/unread-count'),  // 获取未读通知数量
    markAsRead: (id) => request.put(`/notifications/${id}/read`),  // 标记通知为已读
    markAllAsRead: () => request.post('/notifications/read-all'),  // 标记所有通知为已读
    delete: (id) => request.delete(`/notifications/${id}`),  // 删除通知
    adminSend: (data) => request.post('/notifications/admin/send', data)  // 管理员发送通知
  },

  // ========== 举报接口 ==========
  reports: {
    create: (data) => request.post('/reports/', data),  // 创建举报
    getList: (params) => request.get('/reports/', { params }),  // 获取举报列表（管理员）
    getById: (id) => request.get(`/reports/${id}`),  // 获取举报详情（管理员）
    handle: (id, data) => request.put(`/reports/${id}/handle`, data)  // 处理举报（管理员）
  },

  // ========== 搜索接口 ==========
  search: {
    search: (data) => request.post('/search/', data),  // 搜索内容
    getHistory: (params) => request.get('/search/history', { params }),  // 获取搜索历史
    clearHistory: () => request.delete('/search/history')  // 清空搜索历史
  },

  // ========== 管理后台接口 ==========
  admin: {
    getStatistics: () => request.get('/admin/statistics'),  // 获取统计数据
    manageUser: (id, data) => request.put(`/admin/users/${id}`, data),  // 管理用户
    managePost: (id, data) => request.put(`/admin/posts/${id}`, data),  // 管理帖子
    getLogs: (params) => request.get('/admin/logs', { params }),  // 获取操作日志
    getHotUsers: (params) => request.get('/admin/hot-users', { params }),  // 获取热门用户
    getActivityData: (params) => request.get('/admin/activity-data', { params })  // 获取活动数据
  },

  // ========== 文件上传接口 ==========
  uploads: {
    uploadImage: (file, postId) => {  // 上传图片
      const formData = new FormData()
      formData.append('file', file)
      if (postId) formData.append('post_id', postId)
      return request.post('/uploads/image', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
    },
    uploadFile: (file, postId) => {  // 上传文件
      const formData = new FormData()
      formData.append('file', file)
      if (postId) formData.append('post_id', postId)
      return request.post('/uploads/file', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
    },
    delete: (id) => request.delete(`/uploads/${id}`)  // 删除附件
  },

  // ========== 系统设置接口 ==========
  system: {
    getList: () => request.get('/system'),  // 获取所有系统设置
    get: (key) => request.get(`/system/${key}`),  // 获取单个系统设置
    update: (key, data) => request.put(`/system/${key}`, data),  // 更新系统设置
    initDefaults: () => request.post('/system/init-defaults')  // 初始化默认设置
  }
}

// ========== 导出API对象 ==========
export default api

