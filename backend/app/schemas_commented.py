"""
BBS论坛系统 - Pydantic数据验证模式
本文件负责：
1. 定义API请求的数据模型
2. 定义API响应的数据模型
3. 提供数据验证规则
4. 用于FastAPI的请求体验证和响应序列化
"""
from pydantic import BaseModel, EmailStr, Field
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

class ReportStatus(str, Enum):
    """举报状态枚举"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

# ========== 用户相关Schema ==========

class UserBase(BaseModel):
    """用户基础模型"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr

class UserCreate(UserBase):
    """用户创建模型（注册请求）"""
    password: str = Field(..., min_length=6)
    phone: Optional[str] = None

class UserUpdate(BaseModel):
    """用户更新模型（个人资料更新）"""
    avatar: Optional[str] = None
    signature: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None

class UserResponse(UserBase):
    """用户响应模型（用户信息）"""
    id: int
    avatar: Optional[str] = None
    signature: Optional[str] = None
    bio: Optional[str] = None
    role: UserRole
    user_group: UserGroup
    level: int
    exp: int
    points: int
    is_verified: bool
    is_active: bool
    is_banned: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    """用户登录模型"""
    username: str
    password: str

class Token(BaseModel):
    """JWT令牌模型"""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """JWT令牌数据模型（用于解析Token）"""
    username: Optional[str] = None
    user_id: Optional[int] = None

# ========== 版块相关Schema ==========

class CategoryBase(BaseModel):
    """版块基础模型"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: int = 0
    can_view: int = 0
    can_post: int = 0
    can_reply: int = 0

class CategoryCreate(CategoryBase):
    """版块创建模型"""
    pass

class CategoryUpdate(BaseModel):
    """版块更新模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: Optional[int] = None
    can_view: Optional[int] = None
    can_post: Optional[int] = None
    can_reply: Optional[int] = None

class CategoryResponse(CategoryBase):
    """版块响应模型"""
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
    """帖子基础模型"""
    title: str = Field(..., min_length=1, max_length=200)
    content: str
    category_id: int
    post_type: PostType = PostType.NORMAL
    tags: Optional[List[str]] = None

class PostCreate(PostBase):
    """帖子创建模型"""
    pass

class PostUpdate(BaseModel):
    """帖子更新模型"""
    title: Optional[str] = None
    content: Optional[str] = None
    category_id: Optional[int] = None
    post_type: Optional[PostType] = None
    tags: Optional[List[str]] = None

class PostResponse(PostBase):
    """帖子响应模型"""
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
    created_at: datetime
    updated_at: datetime
    author: Optional[UserResponse] = None
    category: Optional[CategoryResponse] = None

    class Config:
        from_attributes = True

class PostListResponse(BaseModel):
    """帖子列表响应模型（精简版）"""
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
    created_at: datetime

    class Config:
        from_attributes = True

# ========== 评论相关Schema ==========

class CommentBase(BaseModel):
    """评论基础模型"""
    content: str = Field(..., min_length=1)
    post_id: int
    parent_id: Optional[int] = None
    reply_to_user_id: Optional[int] = None

class CommentCreate(CommentBase):
    """评论创建模型"""
    pass

class CommentUpdate(BaseModel):
    """评论更新模型"""
    content: Optional[str] = None

class CommentResponse(CommentBase):
    """评论响应模型"""
    id: int
    author_id: int
    like_count: int
    dislike_count: int
    is_deleted: bool
    created_at: datetime
    author: Optional[UserResponse] = None
    post: Optional[PostResponse] = None
    replies: List["CommentResponse"] = []

    class Config:
        from_attributes = True

# ========== 其他Schema ==========

class LikeCreate(BaseModel):
    """点赞创建模型"""
    post_id: Optional[int] = None
    comment_id: Optional[int] = None

class FavoriteCreate(BaseModel):
    """收藏创建模型"""
    post_id: int

class FollowCreate(BaseModel):
    """关注创建模型"""
    followed_id: int

class MessageCreate(BaseModel):
    """私信创建模型"""
    receiver_id: int
    content: str = Field(..., min_length=1)

class MessageResponse(BaseModel):
    """私信响应模型"""
    id: int
    sender_id: int
    receiver_id: int
    content: str
    is_read: bool
    created_at: datetime
    sender: Optional[UserResponse] = None
    receiver: Optional[UserResponse] = None

    class Config:
        from_attributes = True

class NotificationCreate(BaseModel):
    """通知创建模型"""
    user_id: int
    notification_type: NotificationType
    title: Optional[str] = None
    content: Optional[str] = None
    related_id: Optional[int] = None

class NotificationResponse(BaseModel):
    """通知响应模型"""
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

class ReportCreate(BaseModel):
    """举报创建模型"""
    post_id: Optional[int] = None
    comment_id: Optional[int] = None
    reason: str = Field(..., max_length=500)
    description: Optional[str] = None

class ReportResponse(BaseModel):
    """举报响应模型"""
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

class SearchQuery(BaseModel):
    """搜索查询模型"""
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
    """搜索结果模型"""
    posts: List[PostListResponse] = []
    users: List[UserResponse] = []
    total: int
    page: int
    page_size: int

# ========== 分页模型 ==========

class PaginatedResponse(BaseModel):
    """分页响应模型"""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int

# ========== 管理后台Schema ==========

class UserManagementUpdate(BaseModel):
    """用户管理更新模型"""
    role: Optional[UserRole] = None
    user_group: Optional[UserGroup] = None
    is_active: Optional[bool] = None
    is_banned: Optional[bool] = None
    ban_reason: Optional[str] = None
    ban_until: Optional[datetime] = None
    is_verified: Optional[bool] = None

class PostManagementUpdate(BaseModel):
    """帖子管理更新模型"""
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
