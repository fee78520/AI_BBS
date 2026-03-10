# AI_BBS - 智能论坛系统

<div align="center">

![Vue](https://img.shields.io/badge/Vue-3.x-4FC08D?logo=vue.js)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688?logo=fastapi)
![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python)
![SQLite](https://img.shields.io/badge/SQLite-3.x-003B57?logo=sqlite)
![License](https://img.shields.io/badge/License-MIT-green)

**一个功能完整、开箱即用的现代化论坛系统**

[在线体验](http://82.156.187.38:8080) · [快速开始](#快速开始) · [功能特性](#功能特性) · [技术架构](#技术架构)

</div>

---

## 项目亮点

- **AI 驱动开发**：99.9% 代码由 AI 生成，仅需一天完成完整论坛系统
- **功能完备**：涵盖用户、帖子、评论、私信、通知、管理等 12 大模块
- **开箱即用**：提供 Windows/Linux 一键部署脚本，5 分钟搭建完成
- **现代技术栈**：Vue 3 + FastAPI + SQLite，轻量高效
- **响应式设计**：完美适配 PC 端与移动端

---

## 功能特性

### 核心功能

| 模块 | 功能 |
|------|------|
| **用户系统** | 注册登录、个人资料、等级权限、积分系统、用户组管理 |
| **帖子管理** | 发帖、编辑、删除、置顶、精华、锁定、富文本编辑、附件上传 |
| **评论系统** | 楼中楼评论、引用回复、点赞踩、@用户提醒 |
| **互动功能** | 点赞、收藏、关注、私信、系统通知 |
| **搜索系统** | 全文搜索、高级搜索、用户搜索、搜索历史 |
| **管理后台** | 用户管理、版块管理、内容审核、数据统计、系统设置 |

### 安全防护

- JWT 认证 + 密码加密存储
- SQL 注入 / XSS / CSRF 防护
- 敏感词过滤
- IP 封禁
- 防灌水机制

---

## 技术架构

### 后端技术栈

| 技术 | 说明 |
|------|------|
| **FastAPI** | 高性能异步 Web 框架 |
| **SQLAlchemy** | ORM 数据库操作 |
| **SQLite** | 轻量级数据库，零配置 |
| **Pydantic** | 数据验证与序列化 |
| **Passlib** | 密码加密 |
| **JWT** | 无状态认证 |

### 前端技术栈

| 技术 | 说明 |
|------|------|
| **Vue 3** | 渐进式 JavaScript 框架 |
| **Element Plus** | 企业级 UI 组件库 |
| **Pinia** | 新一代状态管理 |
| **Vue Router** | 路由管理 |
| **Axios** | HTTP 客户端 |
| **Vite** | 新一代构建工具 |

### 项目结构

```
AI_BBS/
├── backend/                 # 后端代码
│   ├── app/
│   │   ├── api/            # API 路由 (17 个模块)
│   │   ├── models.py       # 数据库模型
│   │   ├── schemas.py      # Pydantic 模式
│   │   ├── auth.py         # 认证模块
│   │   └── database.py     # 数据库配置
│   └── requirements.txt
│
├── frontend/                # 前端代码
│   ├── src/
│   │   ├── views/          # 页面组件 (20+ 页面)
│   │   ├── layouts/        # 布局组件
│   │   ├── stores/         # 状态管理
│   │   ├── router/         # 路由配置
│   │   └── api/            # API 封装
│   └── package.json
│
├── nginx/                   # Nginx 配置
├── scripts/                 # 部署脚本
│   ├── start-windows.bat
│   └── start-linux.sh
└── docs/                    # 项目文档
```

---

## 快速开始

### 环境要求

- Python 3.9+
- Node.js 16+
- SQLite 3.x

### Windows 一键启动

```bash
# 克隆项目
git clone https://github.com/your-username/AI_BBS.git
cd AI_BBS

# 运行启动脚本
scripts\start-windows.bat
```

### Linux 一键部署

```bash
# 克隆项目
git clone https://github.com/your-username/AI_BBS.git
cd AI_BBS

# 添加执行权限
chmod +x scripts/*.sh

# 一键部署
sudo ./scripts/start-linux.sh
```

部署完成后访问：`http://localhost:8080`

### 手动启动

<details>
<summary>点击展开详细步骤</summary>

#### 后端启动

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置数据库等

# 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 开发模式
npm run dev

# 生产构建
npm run build
```

</details>

---

## API 文档

启动后端服务后，访问以下地址查看自动生成的 API 文档：

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 功能模块清单

<details>
<summary>点击查看完整清单</summary>

### 后端 API 模块

| 模块 | 文件 | 功能 |
|------|------|------|
| 认证 | `api/auth.py` | 登录、注册、Token 刷新 |
| 用户 | `api/users.py` | 用户 CRUD、资料管理 |
| 版块 | `api/categories.py` | 版块管理 |
| 帖子 | `api/posts.py` | 帖子 CRUD、置顶、精华 |
| 评论 | `api/comments.py` | 评论、回复管理 |
| 点赞 | `api/likes.py` | 点赞功能 |
| 收藏 | `api/favorites.py` | 收藏功能 |
| 关注 | `api/follows.py` | 关注功能 |
| 私信 | `api/messages.py` | 私信功能 |
| 通知 | `api/notifications.py` | 系统通知 |
| 举报 | `api/reports.py` | 举报管理 |
| 搜索 | `api/search.py` | 全文搜索 |
| 管理 | `api/admin.py` | 后台管理 |
| 上传 | `api/uploads.py` | 文件上传 |
| 系统 | `api/system.py` | 系统配置 |

### 前端页面模块

| 类型 | 页面 | 说明 |
|------|------|------|
| 公共 | Home, Login, Register, Search | 基础功能页面 |
| 帖子 | CreatePost, PostDetail, Category | 帖子相关页面 |
| 用户 | Profile, UserProfile, Follows | 用户中心页面 |
| 消息 | Messages, Notifications | 消息通知页面 |
| 管理 | Dashboard, Users, Posts, Reports... | 后台管理页面 |

</details>

---

## 在线体验

**体验地址**：http://82.156.187.38:8080

### 体验说明

- 支持邮箱注册（手机号注册因短信费用暂未开放）
- 如需体验完整后台管理功能，请联系获取管理员账号
- 联系邮箱：17853530715@163.com

---

## 部署说明

### 生产环境配置

1. **环境变量配置**（`.env` 文件）

```env
# 数据库配置
DATABASE_URL=sqlite:///./bbs.db

# JWT 配置
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 管理员密码（首次部署时创建）
ADMIN_PASSWORD=your-secure-password
```

2. **Nginx 反向代理配置**

项目已提供完整的 Nginx 配置文件：
- Windows: `nginx/nginx.conf`
- Linux: `nginx/conf/nginx.conf`

3. **Systemd 服务配置**

Linux 部署脚本会自动创建 `mybbs` 服务：

```bash
# 服务管理
sudo systemctl start mybbs     # 启动
sudo systemctl stop mybbs      # 停止
sudo systemctl restart mybbs   # 重启
sudo systemctl status mybbs    # 状态
```

---

## 开发历程

本项目是一个 **AI 辅助开发的实践案例**：

- **开发时间**：约 1 天
- **AI 参与度**：99.9% 代码由 AI 生成
- **代码行数**：约 15,000+ 行
- **功能模块**：12 大模块，70+ API 接口

### AI 开发心得

> "未来的程序员，尤其针对新项目，一定要学会驾驭 Agent，全新的时代即将来临。"

AI 辅助开发的关键点：
1. **清晰的提示词**：准确描述需求，AI 才能生成高质量代码
2. **迭代优化**：逐步完善功能，而非一次性生成全部代码
3. **代码审查**：AI 生成的代码仍需人工审查和测试
4. **架构设计**：先设计好架构，再让 AI 填充细节

---

## 常见问题

<details>
<summary>点击展开 FAQ</summary>

### Q: 如何修改管理员密码？

A: 首次部署时，在 `.env` 文件中设置 `ADMIN_PASSWORD` 环境变量。部署后可通过后台管理界面修改。

### Q: 数据库文件在哪里？

A: SQLite 数据库文件位于 `backend/bbs.db`，可直接备份此文件。

### Q: 如何更换端口？

A: 修改 `scripts/start-linux.sh` 中的 `HTTP_PORT` 变量，或直接修改 Nginx 配置文件。

### Q: 忘记密码怎么办？

A: 管理员可通过后台重置用户密码；管理员密码重置需直接操作数据库。

</details>

---

## 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

---

## 开源协议

本项目采用 [MIT](LICENSE) 协议开源。

---

## 联系方式

- **邮箱**：17853530715@163.com
- **项目地址**：https://github.com/your-username/AI_BBS

---

<div align="center">

**如果这个项目对你有帮助，请给一个 ⭐️ Star 支持一下！**

Made with ❤️ and AI

</div>
