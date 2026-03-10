from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.database import get_db
from app.models import Notification, User
from app.schemas import NotificationResponse, PaginatedResponse
from app.auth import get_current_active_user, require_admin
from app.utils.notification import NotificationService

router = APIRouter()

class AdminSendNotification(BaseModel):
    """管理员发送通知请求"""
    target_type: str  # all(全部用户) / user(指定用户) / role(指定角色)
    target_id: Optional[int] = None  # 当target_type=user时为用户ID，role时为角色值
    title: str  # 通知标题
    content: str  # 通知内容
    notification_type: str = "system"  # 通知类型

@router.get("/", response_model=PaginatedResponse)
async def get_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = False,
    notification_type: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取通知列表"""
    from sqlalchemy import desc

    query = db.query(Notification).filter(
        Notification.user_id == current_user.id
    )

    if unread_only:
        query = query.filter(Notification.is_read == False)

    if notification_type:
        query = query.filter(Notification.notification_type == notification_type)

    query = query.order_by(desc(Notification.created_at))

    total = query.count()
    notifications = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "items": [NotificationResponse.model_validate(n).model_dump() for n in notifications],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

@router.get("/unread-count")
async def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取未读通知数量"""
    count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()

    return {"count": count}

@router.put("/{notification_id}/read")
async def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """标记通知为已读"""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="通知不存在"
        )

    NotificationService.mark_as_read(db, notification_id)

    return {"message": "已标记为已读"}

@router.post("/read-all")
async def mark_all_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """标记所有通知为已读"""
    count = NotificationService.mark_all_as_read(db, current_user.id)

    return {"message": f"已将 {count} 条通知标记为已读"}

@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除通知"""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="通知不存在"
        )

    db.delete(notification)
    db.commit()

    return {"message": "通知已删除"}

@router.post("/admin/send")
@require_admin
async def admin_send_notification(
    data: AdminSendNotification,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """管理员发送通知（广播/定向）"""
    from app.models import Role

    target_users = []

    if data.target_type == "all":
        # 发送给所有用户
        target_users = db.query(User).filter(User.is_active == True).all()
    elif data.target_type == "user":
        # 发送给指定用户
        target_user = db.query(User).filter(User.id == data.target_id).first()
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="目标用户不存在"
            )
        target_users = [target_user]
    elif data.target_type == "role":
        # 发送给指定角色的用户
        if data.target_id not in [r.value for r in Role]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的角色"
            )
        target_users = db.query(User).filter(
            User.role == data.target_id,
            User.is_active == True
        ).all()
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的目标类型"
        )

    if not target_users:
        return {"message": "没有可发送的用户", "count": 0}

    # 批量创建通知
    count = 0
    for user in target_users:
        NotificationService.create_notification(
            db=db,
            user_id=user.id,
            notification_type=data.notification_type,
            title=data.title,
            content=data.content
        )
        count += 1

    return {"message": f"已发送 {count} 条通知", "count": count}
