/**
 * BBS论坛系统 - 路由配置
 * 本文件负责：
 * 1. 定义所有路由规则
 * 2. 配置路由元信息（标题、权限等）
 * 3. 配置路由守卫（登录检查、权限验证）
 * 4. 动态加载路由组件（懒加载）
 */
import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

// ========== 路由定义 ==========
const routes = [
  // ========== 主布局路由 ==========
  {
    path: '/',
    name: 'Layout',
    component: () => import('@/layouts/MainLayout.vue'),  // 主布局组件
    children: [
      // --- 公共页面 ---
      {
        path: '',  // 根路径
        name: 'Home',
        component: () => import('@/views/Home.vue'),
        meta: { title: '首页' }
      },
      {
        path: 'category/:id',  // 版块详情页（动态参数：版块ID）
        name: 'Category',
        component: () => import('@/views/Category.vue'),
        meta: { title: '版块' }
      },
      {
        path: 'post/:id',  // 帖子详情页（动态参数：帖子ID）
        name: 'PostDetail',
        component: () => import('@/views/PostDetail.vue'),
        meta: { title: '帖子详情' }
      },
      {
        path: 'user/:id',  // 用户主页（动态参数：用户ID）
        name: 'UserProfile',
        component: () => import('@/views/UserProfile.vue'),
        meta: { title: '用户主页' }
      },
      {
        path: 'post/create',  // 发帖页面
        name: 'CreatePost',
        component: () => import('@/views/CreatePost.vue'),
        meta: { title: '发帖', requiresAuth: true }  // 需要登录
      },
      {
        path: 'search',  // 搜索页面
        name: 'Search',
        component: () => import('@/views/Search.vue'),
        meta: { title: '搜索' }
      },
      
      // --- 个人中心页面 ---
      {
        path: 'profile',  // 个人中心
        name: 'Profile',
        component: () => import('@/views/Profile.vue'),
        meta: { title: '个人中心', requiresAuth: true }
      },
      {
        path: 'messages',  // 私信列表（对话列表）
        name: 'Messages',
        component: () => import('@/views/Messages.vue'),
        meta: { title: '私信', requiresAuth: true }
      },
      {
        path: 'messages/:userId',  // 与某用户的对话详情
        name: 'Conversation',
        component: () => import('@/views/Conversation.vue'),
        meta: { title: '对话', requiresAuth: true }
      },
      {
        path: 'notifications',  // 通知列表
        name: 'Notifications',
        component: () => import('@/views/Notifications.vue'),
        meta: { title: '通知', requiresAuth: true }
      },
      {
        path: 'favorites',  // 收藏列表
        name: 'Favorites',
        component: () => import('@/views/Favorites.vue'),
        meta: { title: '收藏', requiresAuth: true }
      },
      {
        path: 'likes',  // 点赞列表
        name: 'Likes',
        component: () => import('@/views/Likes.vue'),
        meta: { title: '点赞', requiresAuth: true }
      },
      {
        path: 'follows',  // 关注列表
        name: 'Follows',
        component: () => import('@/views/Follows.vue'),
        meta: { title: '关注', requiresAuth: true }
      }
    ]
  },

  // ========== 认证路由（独立布局）==========
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录' }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { title: '注册' }
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: () => import('@/views/ForgotPassword.vue'),
    meta: { title: '找回密码' }
  },
  {
    path: '/reset-password',
    name: 'ResetPassword',
    component: () => import('@/views/ResetPassword.vue'),
    meta: { title: '重置密码' }
  },

  // ========== 管理后台路由 ==========
  {
    path: '/admin',
    name: 'AdminLayout',
    component: () => import('@/layouts/AdminLayout.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },  // 需要登录和管理员权限
    children: [
      {
        path: '',  // 管理后台首页
        name: 'AdminDashboard',
        component: () => import('@/views/admin/Dashboard.vue'),
        meta: { title: '管理后台' }
      },
      {
        path: 'users',  // 用户管理
        name: 'AdminUsers',
        component: () => import('@/views/admin/Users.vue'),
        meta: { title: '用户管理' }
      },
      {
        path: 'posts',  // 帖子管理
        name: 'AdminPosts',
        component: () => import('@/views/admin/Posts.vue'),
        meta: { title: '帖子管理' }
      },
      {
        path: 'categories',  // 版块管理
        name: 'AdminCategories',
        component: () => import('@/views/admin/Categories.vue'),
        meta: { title: '版块管理' }
      },
      {
        path: 'notifications',  // 发送通知
        name: 'AdminNotifications',
        component: () => import('@/views/admin/Notifications.vue'),
        meta: { title: '发送通知' }
      },
      {
        path: 'reports',  // 举报管理
        name: 'AdminReports',
        component: () => import('@/views/admin/Reports.vue'),
        meta: { title: '举报管理' }
      },
      {
        path: 'trash',  // 回收站
        name: 'AdminTrash',
        component: () => import('@/views/admin/Trash.vue'),
        meta: { title: '回收站' }
      },
      {
        path: 'settings',  // 系统设置
        name: 'AdminSettings',
        component: () => import('@/views/admin/Settings.vue'),
        meta: { title: '系统设置' }
      }
    ]
  },

  // ========== 404页面 ==========
  {
    path: '/:pathMatch(.*)*',  // 匹配所有未定义的路径
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue')
  }
]

// ========== 创建路由实例 ==========
const router = createRouter({
  history: createWebHistory(),  // 使用HTML5 History模式
  routes  // 路由配置
})

// ========== 全局路由守卫 ==========
router.beforeEach((to, from, next) => {
  /**
   * 路由前置守卫
   * 在每次路由切换前执行
   * 
   * 参数:
   *   to: 即将进入的目标路由对象
   *   from: 当前正要离开的路由对象
   *   next: 必须调用的函数，决定路由跳转
   * 
   * 用法:
   *   next(): 继续路由跳转
   *   next(false): 中止路由跳转
   *   next('/path'): 重定向到指定路径
   */
  
  const userStore = useUserStore()

  // 设置页面标题
  // 优先使用路由meta中的title，否则使用默认标题
  document.title = to.meta.title ? `${to.meta.title} - BBS论坛` : 'BBS论坛'

  // 检查路由是否需要登录
  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    // 未登录，重定向到登录页
    // 保存原路径，登录后跳转回来
    next({
      name: 'Login',
      query: { redirect: to.fullPath }
    })
    return  // 结束守卫
  }

  // 检查路由是否需要管理员权限
  if (to.meta.requiresAdmin && userStore.user?.role !== 'admin') {
    // 不是管理员，重定向到首页
    next({ name: 'Home' })
    return  // 结束守卫
  }

  // 满足所有条件，继续路由跳转
  next()
})

// ========== 导出路由实例 ==========
export default router
