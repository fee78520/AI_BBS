"""
BBS论坛系统 - FastAPI主应用
本文件是整个后端应用的入口点，负责：
1. 创建FastAPI应用实例
2. 配置CORS跨域
3. 挂载静态文件服务
4. 注册所有API路由
5. 定义启动事件
"""
# ========== 日志配置（必须在所有 import 之前）==========
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True  # 强制重新配置，确保生效
)

# ========== 加载环境变量（必须在其他 import 之前）==========
from dotenv import load_dotenv
load_dotenv()

# ========== 其他导入 ==========
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from app.database import get_db, init_db
from app.models import User, Category, SystemSetting, Log
from app.auth import get_current_active_user
import os

# 创建FastAPI应用实例
app = FastAPI(
    title="BBS Forum API",  # API标题
    description="A complete BBS forum system built with FastAPI",  # API描述
    version="1.0.0"  # API版本
)

# ========== CORS跨域配置 ==========
# 允许前端跨域访问后端API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源（生产环境建议指定具体域名）
    allow_credentials=True,  # 允许携带凭证
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有请求头
)

# ========== 静态文件服务 ==========
# 用于提供用户上传的文件（图片、文档等）
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# ========== 路由注册 ==========
# 导入所有API路由模块
from app.api import auth, users, categories, posts, comments, likes, favorites, follows, messages, notifications, reports, search, admin, uploads, system

# 注册路由到FastAPI应用
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(users.router, prefix="/api/users", tags=["用户"])
app.include_router(categories.router, prefix="/api/categories", tags=["版块"])
app.include_router(posts.router, prefix="/api/posts", tags=["帖子"])
app.include_router(comments.router, prefix="/api/comments", tags=["评论"])
app.include_router(likes.router, prefix="/api/likes", tags=["点赞"])
app.include_router(favorites.router, prefix="/api/favorites", tags=["收藏"])
app.include_router(follows.router, prefix="/api/follows", tags=["关注"])
app.include_router(messages.router, prefix="/api/messages", tags=["私信"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["通知"])
app.include_router(reports.router, prefix="/api/reports", tags=["举报"])
app.include_router(search.router, prefix="/api/search", tags=["搜索"])
app.include_router(admin.router, prefix="/api/admin", tags=["管理后台"])
app.include_router(uploads.router, prefix="/api/uploads", tags=["文件上传"])
app.include_router(system.router, prefix="/api/system", tags=["系统"])

# ========== 启动事件 ==========
@app.on_event("startup")
async def startup_event():
    """应用启动时执行的初始化操作"""
    init_db()  # 初始化数据库（创建所有表）
    print("Database initialized successfully!")  # 输出初始化成功信息

# ========== 根路由 ==========
@app.get("/")
async def root():
    """API根路径，返回欢迎信息"""
    return {
        "message": "Welcome to BBS Forum API",
        "version": "1.0.0",
        "docs": "/docs"  # Swagger UI文档地址
    }

# ========== 健康检查路由 ==========
@app.get("/api/health")
async def health_check():
    """健康检查接口，用于监控服务状态"""
    return {"status": "healthy"}

# ========== 应用入口 ==========
if __name__ == "__main__":
    import uvicorn
    # 启动开发服务器（生产环境建议使用gunicorn）
    uvicorn.run(app, host="0.0.0.0", port=8000)
