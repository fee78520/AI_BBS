"""
BBS论坛系统 - 数据库模型定义
本文件定义了所有数据库表结构和ORM模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

# 从 schemas 导入所有枚举类型，统一管理
from app.schemas import (
    UserRole, UserGroup, PostType, PostStatus,
    NotificationType, ReportStatus, VerificationCodeType
)

# 创建SQLAlchemy的基类，所有模型类都继承自这个基类
Base = declarative_base()

class User(Base):
    """用户表 - 存储用户基本信息"""
    __tablename__ = "users"

    # 主键ID
    id = Column(Integer, primary_key=True, index=True)
    # 用户名（唯一，索引）
    username = Column(String(50), unique=True, index=True, nullable=False)
    # 邮箱（唯一，索引）
    email = Column(String(100), unique=True, index=True, nullable=False)
    # 手机号（可选，唯一，索引）
    phone = Column(String(20), unique=True, index=True)
    # 密码哈希值（加密存储）
    password_hash = Column(String(255), nullable=False)
    # 头像URL
    avatar = Column(String(255))
    # 个性签名
    signature = Column(Text)
    # 个人简介
    bio = Column(Text)
    # 用户角色（普通用户/版主/管理员）
    role = Column(SQLEnum(UserRole), default=UserRole.USER)
    # 用户组（普通/VIP/荣誉）
    user_group = Column(SQLEnum(UserGroup), default=UserGroup.NORMAL)
    # 用户等级
    level = Column(Integer, default=1)
    # 经验值
    exp = Column(Integer, default=0)
    # 积分
    points = Column(Integer, default=0)
    # 是否已实名认证
    is_verified = Column(Boolean, default=False)
    # 账号是否激活
    is_active = Column(Boolean, default=True)
    # 是否被封禁
    is_banned = Column(Boolean, default=False)
    # 封禁原因
    ban_reason = Column(Text)
    # 封禁截止时间
    ban_until = Column(DateTime)
    # 注册时间
    created_at = Column(DateTime, default=datetime.utcnow)
    # 更新时间（自动更新）
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # 最后登录时间
    last_login_at = Column(DateTime)
    # 最后登录IP
    last_login_ip = Column(String(50))

    # 关系定义 - 用户与其他表的关联
    # 用户发表的帖子
    posts = relationship("Post", back_populates="author")
    # 用户发表的评论
    comments = relationship("Comment", back_populates="author", foreign_keys="Comment.author_id")
    # 用户的点赞记录
    likes = relationship("Like", back_populates="user")
    # 用户的收藏记录
    favorites = relationship("Favorite", back_populates="user")
    # 用户关注的人（follower_id是当前用户）
    follows = relationship("Follow", foreign_keys="Follow.follower_id", back_populates="follower")
    # 关注当前用户的人（followed_id是当前用户）
    followers = relationship("Follow", foreign_keys="Follow.followed_id", back_populates="followed")
    # 用户发送的私信
    sent_messages = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")
    # 用户收到的私信
    received_messages = relationship("Message", foreign_keys="Message.receiver_id", back_populates="receiver")
    # 用户的通知
    notifications = relationship("Notification", back_populates="user")
    # 用户提交的举报
    reports = relationship("Report", back_populates="reporter", foreign_keys="Report.reporter_id")
    # 用户管理的版块（版主）
    moderations = relationship("CategoryModerator", back_populates="moderator")

class Category(Base):
    """版块表 - 存储论坛版块信息"""
    __tablename__ = "categories"

    # 主键ID
    id = Column(Integer, primary_key=True, index=True)
    # 版块名称
    name = Column(String(100), nullable=False)
    # 版块描述
    description = Column(Text)
    # 版块图标URL
    icon = Column(String(255))
    # 父版块ID（用于创建子版块，支持层级结构）
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    # 排序序号
    sort_order = Column(Integer, default=0)
    # 帖子总数
    post_count = Column(Integer, default=0)
    # 可查看的最低等级（0表示所有用户）
    can_view = Column(Integer, default=0)
    # 可发帖的最低等级
    can_post = Column(Integer, default=0)
    # 可回复的最低等级
    can_reply = Column(Integer, default=0)
    # 创建时间
    created_at = Column(DateTime, default=datetime.utcnow)
    # 更新时间（自动更新）
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系定义
    # 子版块列表
    children = relationship("Category", backref="parent", remote_side=[id])
    # 版块下的帖子列表
    posts = relationship("Post", back_populates="category")
    # 版块的版主列表
    moderators = relationship("CategoryModerator", back_populates="category")

class CategoryModerator(Base):
    """版主表 - 版块与用户的关联表（多对多）"""
    __tablename__ = "category_moderators"

    # 主键ID
    id = Column(Integer, primary_key=True, index=True)
    # 版块ID（外键）
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    # 用户ID（外键）
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # 任命时间
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系定义
    # 关联的版块
    category = relationship("Category", back_populates="moderators")
    # 关联的用户（版主）
    moderator = relationship("User", back_populates="moderations")

class Post(Base):
    """帖子表 - 存储论坛帖子"""
    __tablename__ = "posts"

    # 主键ID
    id = Column(Integer, primary_key=True, index=True)
    # 帖子标题
    title = Column(String(200), nullable=False)
    # 帖子内容（支持富文本）
    content = Column(Text, nullable=False)
    # 作者ID（外键）
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # 版块ID（外键）
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    # 帖子类型（普通/置顶/精华/公告）- 使用枚举值存储
    post_type = Column(SQLEnum(PostType, values_callable=lambda obj: [e.value for e in obj]), default=PostType.NORMAL)
    # 帖子状态（草稿/已发布/审核中/已删除）- 使用枚举值存储
    status = Column(SQLEnum(PostStatus, values_callable=lambda obj: [e.value for e in obj]), default=PostStatus.PUBLISHED)
    # 标签列表（JSON格式存储）
    tags = Column(JSON)
    # 浏览量
    view_count = Column(Integer, default=0)
    # 点赞数
    like_count = Column(Integer, default=0)
    # 评论数
    comment_count = Column(Integer, default=0)
    # 是否置顶
    is_pinned = Column(Boolean, default=False)
    # 是否锁定（锁定后无法回复）
    is_locked = Column(Boolean, default=False)
    # 是否删除（软删除）
    is_deleted = Column(Boolean, default=False)
    # 是否隐藏（管理员隐藏，对普通用户不可见）
    is_hidden = Column(Boolean, default=False)
    # 创建时间
    created_at = Column(DateTime, default=datetime.utcnow)
    # 更新时间（自动更新）
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系定义
    # 帖子作者
    author = relationship("User", back_populates="posts")
    # 帖子所属版块
    category = relationship("Category", back_populates="posts")
    # 帖子的所有评论（级联删除）
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    # 帖子的点赞记录
    likes = relationship("Like", back_populates="post")
    # 帖子的收藏记录
    favorites = relationship("Favorite", back_populates="post")
    # 帖子的举报记录
    reports = relationship("Report", back_populates="post")

class Comment(Base):
    """评论表 - 存储帖子评论和回复（支持楼中楼）"""
    __tablename__ = "comments"

    # 主键ID
    id = Column(Integer, primary_key=True, index=True)
    # 评论内容
    content = Column(Text, nullable=False)
    # 评论作者ID
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # 所属帖子ID
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    # 父评论ID（用于实现楼中楼，为空表示是顶级评论）
    parent_id = Column(Integer, ForeignKey("comments.id"), nullable=True)
    # 回复的用户ID（用于@提醒）
    reply_to_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    # 点赞数
    like_count = Column(Integer, default=0)
    # 踩数
    dislike_count = Column(Integer, default=0)
    # 是否删除（软删除）
    is_deleted = Column(Boolean, default=False)
    # 是否隐藏（管理员隐藏，对普通用户不可见）
    is_hidden = Column(Boolean, default=False)
    # 创建时间
    created_at = Column(DateTime, default=datetime.utcnow)
    # 更新时间（自动更新）
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系定义
    # 评论作者
    author = relationship("User", back_populates="comments", foreign_keys=[author_id])
    # 所属帖子
    post = relationship("Post", back_populates="comments")
    # 父评论
    parent = relationship("Comment", remote_side=[id], backref="replies")
    # 回复的用户
    reply_to_user = relationship("User", foreign_keys=[reply_to_user_id])

class Like(Base):
    """点赞表 - 记录用户对帖子或评论的点赞"""
    __tablename__ = "likes"

    # 主键ID
    id = Column(Integer, primary_key=True, index=True)
    # 点赞用户ID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # 点赞的帖子ID（可为空）
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=True)
    # 点赞的评论ID（可为空）
    comment_id = Column(Integer, ForeignKey("comments.id"), nullable=True)
    # 点赞时间
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系定义
    # 点赞用户
    user = relationship("User", back_populates="likes")
    # 点赞的帖子
    post = relationship("Post", back_populates="likes")
    # 点赞的评论
    comment = relationship("Comment")

class Favorite(Base):
    """收藏表 - 记录用户收藏的帖子"""
    __tablename__ = "favorites"

    # 主键ID
    id = Column(Integer, primary_key=True, index=True)
    # 收藏用户ID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # 收藏的帖子ID
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    # 收藏时间
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系定义
    # 收藏用户
    user = relationship("User", back_populates="favorites")
    # 收藏的帖子
    post = relationship("Post", back_populates="favorites")

class Follow(Base):
    """关注表 - 记录用户之间的关注关系"""
    __tablename__ = "follows"

    # 主键ID
    id = Column(Integer, primary_key=True, index=True)
    # 关注者ID
    follower_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # 被关注者ID
    followed_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # 关注时间
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系定义
    # 关注者
    follower = relationship("User", back_populates="follows", foreign_keys=[follower_id])
    # 被关注者
    followed = relationship("User", back_populates="followers", foreign_keys=[followed_id])

class Message(Base):
    """私信表 - 存储用户之间的私信消息"""
    __tablename__ = "messages"

    # 主键ID
    id = Column(Integer, primary_key=True, index=True)
    # 发送者ID
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # 接收者ID
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # 消息内容（支持富文本）
    content = Column(Text, nullable=True)
    # 消息图片（可选，支持多张图片，JSON数组）
    images = Column(JSON, nullable=True)
    # 是否已读
    is_read = Column(Boolean, default=False)
    # 发送时间
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系定义
    # 发送者
    sender = relationship("User", back_populates="sent_messages", foreign_keys=[sender_id])
    # 接收者
    receiver = relationship("User", back_populates="received_messages", foreign_keys=[receiver_id])

class Notification(Base):
    """通知表 - 存储系统通知和各类提醒"""
    __tablename__ = "notifications"

    # 主键ID
    id = Column(Integer, primary_key=True, index=True)
    # 接收通知的用户ID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # 通知类型（系统/回复/@提醒/点赞/关注/私信）
    notification_type = Column(SQLEnum(NotificationType), nullable=False)
    # 通知标题
    title = Column(String(200))
    # 通知内容
    content = Column(Text)
    # 相关内容ID（如帖子ID、评论ID等）
    related_id = Column(Integer)
    # 是否已读
    is_read = Column(Boolean, default=False)
    # 创建时间
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系定义
    # 接收通知的用户
    user = relationship("User", back_populates="notifications")

class Report(Base):
    """举报表 - 存储用户举报的内容和处理记录"""
    __tablename__ = "reports"

    # 主键ID
    id = Column(Integer, primary_key=True, index=True)
    # 举报人ID
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # 被举报的帖子ID（可为空）
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=True)
    # 被举报的评论ID（可为空）
    comment_id = Column(Integer, ForeignKey("comments.id"), nullable=True)
    # 举报原因
    reason = Column(String(500), nullable=False)
    # 举报详细描述
    description = Column(Text)
    # 举报状态（待处理/已通过/已拒绝）
    status = Column(SQLEnum(ReportStatus), default=ReportStatus.PENDING)
    # 处理人ID（管理员）
    handler_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    # 处理备注
    handler_note = Column(Text)
    # 举报时间
    created_at = Column(DateTime, default=datetime.utcnow)
    # 处理时间
    handled_at = Column(DateTime)

    # 关系定义
    # 举报人
    reporter = relationship("User", back_populates="reports", foreign_keys=[reporter_id])
    # 处理人
    handler = relationship("User", foreign_keys=[handler_id])
    # 被举报的帖子
    post = relationship("Post", back_populates="reports")

class SearchHistory(Base):
    """搜索历史表 - 记录用户的搜索历史"""
    __tablename__ = "search_history"

    # 主键ID
    id = Column(Integer, primary_key=True, index=True)
    # 搜索用户ID（可为空，支持匿名搜索）
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    # 搜索关键词
    keyword = Column(String(200), nullable=False)
    # 搜索结果数量
    result_count = Column(Integer, default=0)
    # 搜索时间
    created_at = Column(DateTime, default=datetime.utcnow)

class Attachment(Base):
    """附件表 - 存储用户上传的文件信息"""
    __tablename__ = "attachments"

    # 主键ID
    id = Column(Integer, primary_key=True, index=True)
    # 上传用户ID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # 关联的帖子ID（可为空）
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=True)
    # 文件名
    filename = Column(String(255), nullable=False)
    # 文件存储路径
    file_path = Column(String(500), nullable=False)
    # 文件大小（字节）
    file_size = Column(Integer, default=0)
    # 文件类型（MIME类型）
    file_type = Column(String(50))
    # 下载次数
    download_count = Column(Integer, default=0)
    # 上传时间
    created_at = Column(DateTime, default=datetime.utcnow)

class Log(Base):
    """日志表 - 记录系统操作日志"""
    __tablename__ = "logs"

    # 主键ID
    id = Column(Integer, primary_key=True, index=True)
    # 操作用户ID（可为空，记录系统操作）
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    # 操作类型（如：user_register、post_create等）
    action = Column(String(100), nullable=False)
    # 操作IP地址
    ip_address = Column(String(50))
    # 用户代理（浏览器信息）
    user_agent = Column(String(500))
    # 额外数据（JSON格式）
    extra_data = Column(JSON)
    # 操作时间
    created_at = Column(DateTime, default=datetime.utcnow)

class SystemSetting(Base):
    """系统设置表 - 存储系统配置"""
    __tablename__ = "system_settings"

    # 主键ID
    id = Column(Integer, primary_key=True, index=True)
    # 设置键（唯一）
    key = Column(String(100), unique=True, nullable=False)
    # 设置值
    value = Column(Text)
    # 设置说明
    description = Column(Text)
    # 更新时间（自动更新）
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class VerificationCode(Base):
    """验证码表 - 存储邮箱/手机验证码"""
    __tablename__ = "verification_codes"

    # 主键ID
    id = Column(Integer, primary_key=True, index=True)
    # 目标地址（邮箱或手机号）
    target = Column(String(100), nullable=False, index=True)
    # 验证码（6位数字）
    code = Column(String(6), nullable=False)
    # 验证码类型（邮箱/手机）
    type = Column(SQLEnum(VerificationCodeType), nullable=False)
    # 过期时间
    expires_at = Column(DateTime, nullable=False)
    # 是否已使用
    used = Column(Boolean, default=False)
    # 创建时间
    created_at = Column(DateTime, default=datetime.utcnow)
