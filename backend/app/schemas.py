"""
BBS论坛系统 - Pydantic数据验证模型
本文件负责：
1. 定义API请求的数据模型（接收客户端数据）
2. 定义API响应的数据模型（返回给客户端数据）
3. 提供数据验证规则（字段类型、长度、格式等）
4. 用于FastAPI的请求体验证和响应序列化

主要包含：
- 枚举类型（角色、状态等）
- 用户相关模型
- 版块相关模型
- 帖子相关模型
- 评论相关模型
- 其他功能模型（点赞、收藏、关注等）
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# ========== 枚举定义 ==========

class UserRole(str, Enum):
    """用户角色枚举"""
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"


class UserGroup(str, Enum):
    """用户组枚举"""
    NORMAL = "normal"
    VIP = "vip"
    HONOR = "honor"

class PostType(str, Enum):
    """帖子类型枚举"""
    NORMAL = "normal"
    TOP = "top"
    ESSENCE = "essence"
    ANNOUNCEMENT = "announcement"

class PostStatus(str, Enum):
    """帖子状态枚举"""
    DRAFT = "draft"
    PUBLISHED = "published"
    AUDITING = "auditing"
    DELETED = "deleted"

class NotificationType(str, Enum):
    """通知类型枚举"""
    SYSTEM = "system"
    REPLY = "reply"
    MENTION = "mention"
    LIKE = "like"
    FOLLOW = "follow"
    PRIVATE_MESSAGE = "private_message"
    REPORT = "report"  # 举报通知

class ReportStatus(str, Enum):
    """举报状态枚举"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class HandleAction(str, Enum):
    """举报处理操作枚举"""
    HIDE = "hide"        # 隐藏内容
    DELETE = "delete"    # 删除内容
    REJECT = "reject"    # 驳回举报
    IGNORE = "ignore"    # 忽略举报

class VerificationCodeType(str, Enum):
    """验证码类型枚举"""
    EMAIL = "email"      # 邮箱验证码
    PHONE = "phone"      # 手机验证码

# ========== 用户相关Schema ==========

class UserBase(BaseModel):
    """用户基础模型（共享字段）"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    phone: Optional[str] = None

class UserUpdate(BaseModel):
    avatar: Optional[str] = None
    signature: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None

class UserResponse(UserBase):
    id: int
    avatar: Optional[str] = None
    signature: Optional[str] = None
    bio: Optional[str] = None
    role: UserRole
    user_group: UserGroup
    level: int
    exp: int
    points: int
    post_count: int = 0
    follower_count: int = 0
    following_count: int = 0
    is_verified: bool
    is_active: bool
    is_banned: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None  # 刷新令牌（可选，用于刷新访问令牌）
    token_type: str

class TokenData(BaseModel):
    """JWT令牌数据模型（用于解析Token）"""
    username: Optional[str] = None
    user_id: Optional[int] = None

# ========== 版块相关Schema ==========

class CategoryBase(BaseModel):
    """版块基础模型（共享字段）"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: int = 0
    can_view: int = 0
    can_post: int = 0
    can_reply: int = 0

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: Optional[int] = None
    can_view: Optional[int] = None
    can_post: Optional[int] = None
    can_reply: Optional[int] = None

class CategoryResponse(CategoryBase):
    id: int
    post_count: int
    created_at: datetime

    class Config:
        from_attributes = True

class CategoryWithChildren(CategoryResponse):
    """版块响应模型（包含子版块）"""
    children: List["CategoryResponse"] = []

# ========== 帖子相关Schema ==========

class PostBase(BaseModel):
    """帖子基础模型（共享字段）"""
    title: str = Field(..., min_length=1, max_length=200)
    content: str
    category_id: int
    post_type: PostType = PostType.NORMAL
    tags: Optional[List[str]] = None

class PostCreate(PostBase):
    pass

class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category_id: Optional[int] = None
    post_type: Optional[PostType] = None
    tags: Optional[List[str]] = None

class PostResponse(PostBase):
    id: int
    author_id: int
    status: PostStatus
    tags: Optional[List[str]] = None
    view_count: int
    like_count: int
    comment_count: int
    is_pinned: bool
    is_locked: bool
    is_deleted: bool
    is_hidden: bool = False
    created_at: datetime
    updated_at: datetime
    author: Optional[UserResponse] = None
    category: Optional[CategoryResponse] = None

    class Config:
        from_attributes = True

class PostListResponse(BaseModel):
    id: int
    title: str
    author: UserResponse
    category: CategoryResponse
    post_type: PostType
    tags: Optional[List[str]] = None
    view_count: int
    like_count: int
    comment_count: int
    is_pinned: bool
    is_locked: bool
    is_hidden: bool = False
    created_at: datetime

    class Config:
        from_attributes = True

# Comment Schemas
class CommentBase(BaseModel):
    content: str = Field(..., min_length=1)
    post_id: int
    parent_id: Optional[int] = None
    reply_to_user_id: Optional[int] = None

class CommentCreate(CommentBase):
    pass

class CommentUpdate(BaseModel):
    content: Optional[str] = None

class CommentResponse(CommentBase):
    id: int
    author_id: int
    like_count: int
    dislike_count: int
    is_deleted: bool
    is_hidden: bool
    created_at: datetime
    author: Optional[UserResponse] = None
    post: Optional[PostResponse] = None
    replies: List["CommentResponse"] = []

    class Config:
        from_attributes = True

# Like/Dislike Schemas
class LikeCreate(BaseModel):
    post_id: Optional[int] = None
    comment_id: Optional[int] = None

# Favorite Schemas
class FavoriteCreate(BaseModel):
    post_id: int

# Follow Schemas
class FollowCreate(BaseModel):
    followed_id: int

# Message Schemas
class MessageCreate(BaseModel):
    receiver_id: int
    content: Optional[str] = Field(None, min_length=1)
    images: Optional[List[str]] = None

class MessageResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    content: Optional[str]
    images: Optional[List[str]]
    is_read: bool
    created_at: datetime
    sender: Optional[UserResponse] = None
    receiver: Optional[UserResponse] = None

    class Config:
        from_attributes = True

class ConversationResponse(BaseModel):
    """对话响应模型 - 用于对话列表"""
    user_id: int                          # 对方用户ID
    user: Optional[UserResponse] = None   # 对方用户信息
    last_message: Optional[MessageResponse] = None  # 最新一条消息
    unread_count: int = 0                 # 未读消息数
    updated_at: Optional[datetime] = None # 最后更新时间（最新消息时间）

# Notification Schemas
class NotificationCreate(BaseModel):
    user_id: int
    notification_type: NotificationType
    title: Optional[str] = None
    content: Optional[str] = None
    related_id: Optional[int] = None

class NotificationResponse(BaseModel):
    id: int
    user_id: int
    notification_type: NotificationType
    title: Optional[str] = None
    content: Optional[str] = None
    related_id: Optional[int] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Report Schemas
class ReportCreate(BaseModel):
    post_id: Optional[int] = None
    comment_id: Optional[int] = None
    reason: str = Field(..., max_length=500)
    description: Optional[str] = None

class ReportResponse(BaseModel):
    id: int
    reporter_id: int
    post_id: Optional[int] = None
    comment_id: Optional[int] = None
    reason: str
    description: Optional[str] = None
    status: ReportStatus
    handler_id: Optional[int] = None
    handler_note: Optional[str] = None
    created_at: datetime
    handled_at: Optional[datetime] = None
    reporter: Optional[UserResponse] = None
    handler: Optional[UserResponse] = None

    class Config:
        from_attributes = True

# Search Schemas
class SearchQuery(BaseModel):
    keyword: str
    search_type: str = "all"
    category_id: Optional[int] = None
    post_type: Optional[PostType] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    sort_by: str = "created_at"
    sort_order: str = "desc"
    page: int = 1
    page_size: int = 20

class SearchResult(BaseModel):
    posts: List[PostListResponse] = []
    users: List[UserResponse] = []
    total: int
    page: int
    page_size: int

# Pagination Schema
class PaginatedResponse(BaseModel):
    """分页响应模型（通用）"""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int

# ========== 管理后台Schema ==========

class UserManagementUpdate(BaseModel):
    """用户管理更新模型（管理员）"""
    role: Optional[UserRole] = None
    user_group: Optional[UserGroup] = None
    is_active: Optional[bool] = None
    is_banned: Optional[bool] = None
    ban_reason: Optional[str] = None
    ban_until: Optional[datetime] = None
    is_verified: Optional[bool] = None

class PostManagementUpdate(BaseModel):
    """帖子管理更新模型（管理员）"""
    status: Optional[PostStatus] = None
    is_pinned: Optional[bool] = None
    is_locked: Optional[bool] = None

# ========== 统计数据Schema ==========

class StatisticsResponse(BaseModel):
    """统计数据响应模型"""
    total_users: int
    total_posts: int
    total_comments: int
    active_users_today: int
    posts_today: int
    comments_today: int

# ========== 附件Schema ==========

class AttachmentResponse(BaseModel):
    """附件响应模型"""
    id: int
    user_id: int
    post_id: Optional[int] = None
    filename: str
    file_path: str
    file_size: int
    file_type: str
    download_count: int
    created_at: datetime

    class Config:
        from_attributes = True

# ========== 系统设置Schema ==========

class SystemSettingUpdate(BaseModel):
    """系统设置更新模型"""
    value: str

class SystemSettingResponse(BaseModel):
    """系统设置响应模型"""
    key: str
    value: Optional[str] = None
    description: Optional[str] = None
    updated_at: datetime

    class Config:
        from_attributes = True

# ========== 验证码Schema ==========

class SendVerificationCodeRequest(BaseModel):
    """发送验证码请求模型"""
    target: str  # 邮箱或手机号
    type: str    # email 或 phone

    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        if v not in ['email', 'phone']:
            raise ValueError('type 必须是 email 或 phone')
        return v

class RegisterWithCodeRequest(BaseModel):
    """验证码注册请求模型"""
    username: str
    password: str
    target: str       # 邮箱或手机号
    code: str         # 验证码
    type: str         # email 或 phone

    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        if v not in ['email', 'phone']:
            raise ValueError('type 必须是 email 或 phone')
        return v

class VerificationCodeResponse(BaseModel):
    """验证码发送响应模型"""
    message: str
    expires_in: int  # 有效期（秒）

# ========== 密码管理Schema ==========

class ChangePasswordRequest(BaseModel):
    """修改密码请求模型"""
    old_password: str = Field(..., min_length=6, description="旧密码")
    new_password: str = Field(..., min_length=6, description="新密码")

class ResetPasswordRequest(BaseModel):
    """重置密码请求模型"""
    target: str = Field(..., description="邮箱或手机号")
    code: str = Field(..., description="验证码")
    new_password: str = Field(..., min_length=6, description="新密码")
    type: str = Field(..., description="email 或 phone")

    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        if v not in ['email', 'phone']:
            raise ValueError('type 必须是 email 或 phone')
        return v
