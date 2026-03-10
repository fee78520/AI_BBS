"""
BBS论坛系统 - 通知服务
本文件负责：
1. 创建系统通知
2. 标记单个通知为已读
3. 标记用户所有通知为已读
"""
from sqlalchemy.orm import Session
from app.models import Notification

class NotificationService:
    """通知服务类 - 提供通知相关的静态方法"""

    @staticmethod
    def create_notification(
        db: Session,
        user_id: int,
        notification_type: str,
        title: str,
        content: str,
        related_id: int = None
    ):
        """
        创建通知

        参数:
            db: 数据库会话
            user_id: 接收通知的用户ID
            notification_type: 通知类型（system/reply/mention/like/follow/private_message）
            title: 通知标题
            content: 通知内容
            related_id: 相关内容ID（如帖子ID、评论ID等，可选）

        返回:
            Notification: 创建的通知对象

        示例:
            >>> notification = NotificationService.create_notification(
            ...     db=db,
            ...     user_id=1,
            ...     notification_type="reply",
            ...     title="有人回复了你的评论",
            ...     content="用户A回复了你的评论",
            ...     related_id=123
            ... )
        """
        notification = Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            content=content,
            related_id=related_id
        )
        db.add(notification)
        db.commit()
        return notification

    @staticmethod
    def mark_as_read(
        db: Session,
        notification_id: int
    ):
        """
        标记单个通知为已读

        参数:
            db: 数据库会话
            notification_id: 通知ID

        返回:
            Notification: 标记后的通知对象，不存在返回None

        示例:
            >>> notification = NotificationService.mark_as_read(db=db, notification_id=123)
        """
        notification = db.query(Notification).filter(
            Notification.id == notification_id
        ).first()
        if notification:
            notification.is_read = True
            db.commit()
        return notification

    @staticmethod
    def mark_all_as_read(
        db: Session,
        user_id: int
    ):
        """
        标记用户所有未读通知为已读

        参数:
            db: 数据库会话
            user_id: 用户ID

        返回:
            int: 标记为已读的通知数量

        示例:
            >>> count = NotificationService.mark_all_as_read(db=db, user_id=1)
            >>> print(f"已标记 {count} 条通知为已读")
        """
        notifications = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).all()
        for notification in notifications:
            notification.is_read = True
        db.commit()
        return len(notifications)

