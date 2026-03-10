from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Follow, User
from app.schemas import FollowCreate, UserResponse, PaginatedResponse
from app.auth import get_current_active_user, require_auth
from app.utils.notification import NotificationService

router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED)
@require_auth
async def follow_user(
    follow: FollowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """关注用户"""
    # 不能关注自己
    if follow.followed_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能关注自己"
        )

    # 检查用户是否存在
    target_user = db.query(User).filter(User.id == follow.followed_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 检查是否已关注
    existing = db.query(Follow).filter(
        Follow.follower_id == current_user.id,
        Follow.followed_id == follow.followed_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已经关注过该用户"
        )

    # 创建关注关系
    db_follow = Follow(
        follower_id=current_user.id,
        followed_id=follow.followed_id
    )
    db.add(db_follow)
    db.commit()

    # 发送关注通知
    from app.schemas import NotificationType
    NotificationService.create_notification(
        db=db,
        user_id=follow.followed_id,
        notification_type=NotificationType.FOLLOW.value,
        title=f"{current_user.username} 关注了你",
        content=f"查看 {current_user.username} 的个人资料",
        related_id=current_user.id
    )

    return {"message": "关注成功"}

@router.delete("/{user_id}")
@require_auth
async def unfollow_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """取消关注用户"""
    follow = db.query(Follow).filter(
        Follow.follower_id == current_user.id,
        Follow.followed_id == user_id
    ).first()

    if not follow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未关注该用户"
        )

    db.delete(follow)
    db.commit()

    return {"message": "已取消关注"}

@router.get("/following", response_model=PaginatedResponse)
@require_auth
async def get_my_following(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取我关注的用户列表"""
    from sqlalchemy import desc

    query = db.query(Follow).filter(
        Follow.follower_id == current_user.id
    ).order_by(desc(Follow.created_at))

    total = query.count()
    follows = query.offset((page - 1) * page_size).limit(page_size).all()

    # 加载用户数据
    items = []
    for follow in follows:
        user = db.query(User).filter(User.id == follow.followed_id).first()
        if user:
            items.append(UserResponse.model_validate(user).model_dump())

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

@router.get("/followers", response_model=PaginatedResponse)
@require_auth
async def get_my_followers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取关注我的用户列表"""
    from sqlalchemy import desc

    query = db.query(Follow).filter(
        Follow.followed_id == current_user.id
    ).order_by(desc(Follow.created_at))

    total = query.count()
    follows = query.offset((page - 1) * page_size).limit(page_size).all()

    # 加载用户数据
    items = []
    for follow in follows:
        user = db.query(User).filter(User.id == follow.follower_id).first()
        if user:
            items.append(UserResponse.model_validate(user).model_dump())

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }
