from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List
from datetime import datetime, timedelta
from app.database import get_db
from app.models import User, Post, Comment, Category, Log
from app.schemas import UserManagementUpdate, PostManagementUpdate, StatisticsResponse, PaginatedResponse
from app.auth import get_current_active_user, require_admin

router = APIRouter()

@router.get("/statistics", response_model=StatisticsResponse)
@require_admin
async def get_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取系统统计数据"""
    # 总用户数
    total_users = db.query(User).count()

    # 总帖子数
    total_posts = db.query(Post).filter(Post.is_deleted == False).count()

    # 总评论数
    total_comments = db.query(Comment).filter(Comment.is_deleted == False).count()

    # 今日活跃用户数（最近24小时内登录）
    today = datetime.utcnow()
    yesterday = today - timedelta(days=1)
    active_users_today = db.query(User).filter(
        User.last_login_at >= yesterday
    ).count()

    # 今日帖子数
    posts_today = db.query(Post).filter(
        Post.created_at >= yesterday,
        Post.is_deleted == False
    ).count()

    # 今日评论数
    comments_today = db.query(Comment).filter(
        Comment.created_at >= yesterday,
        Comment.is_deleted == False
    ).count()

    return {
        "total_users": total_users,
        "total_posts": total_posts,
        "total_comments": total_comments,
        "active_users_today": active_users_today,
        "posts_today": posts_today,
        "comments_today": comments_today
    }

@router.put("/users/{user_id}")
@require_admin
async def manage_user(
    user_id: int,
    user_update: UserManagementUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """管理用户"""
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 不能修改最高管理员的权限
    if target_user.id == current_user.id and user_update.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能修改自己的管理员权限"
        )

    # 更新字段
    for field, value in user_update.model_dump(exclude_unset=True).items():
        setattr(target_user, field, value)

    db.commit()

    return {"message": "用户信息已更新"}

@router.put("/posts/{post_id}")
@require_admin
async def manage_post(
    post_id: int,
    post_update: PostManagementUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """管理帖子"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="帖子不存在"
        )

    # 更新字段
    for field, value in post_update.model_dump(exclude_unset=True).items():
        setattr(post, field, value)

    db.commit()

    return {"message": "帖子信息已更新"}

@router.get("/logs", response_model=PaginatedResponse)
@require_admin
async def get_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: int = None,
    action: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取系统日志"""
    from sqlalchemy import desc

    query = db.query(Log)

    if user_id:
        query = query.filter(Log.user_id == user_id)

    if action:
        query = query.filter(Log.action == action)

    query = query.order_by(desc(Log.created_at))

    total = query.count()
    logs = query.offset((page - 1) * page_size).limit(page_size).all()

    # 加载用户数据
    items = []
    for log in logs:
        user = db.query(User).filter(User.id == log.user_id).first() if log.user_id else None
        log_dict = {
            "id": log.id,
            "user_id": log.user_id,
            "action": log.action,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "extra_data": log.extra_data,
            "created_at": log.created_at,
            "user": UserResponse.model_validate(user).model_dump() if user else None
        }
        items.append(log_dict)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

@router.get("/hot-users")
@require_admin
async def get_hot_users(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取热门用户（按发帖数、回复数等）"""
    # 按发帖数排序
    top_posters = db.query(User).join(Post).filter(
        Post.is_deleted == False
    ).group_by(User.id).order_by(
        desc(func.count(Post.id))
    ).limit(limit).all()

    from app.schemas import UserResponse

    return [UserResponse.model_validate(u).model_dump() for u in top_posters]

@router.get("/activity-data")
@require_admin
async def get_activity_data(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取活动数据（最近N天）"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    data = []

    for i in range(days):
        date = start_date + timedelta(days=i)
        date_end = date + timedelta(days=1)

        # 当日注册用户数
        new_users = db.query(User).filter(
            User.created_at >= date,
            User.created_at < date_end
        ).count()

        # 当日发帖数
        new_posts = db.query(Post).filter(
            Post.created_at >= date,
            Post.created_at < date_end,
            Post.is_deleted == False
        ).count()

        # 当日评论数
        new_comments = db.query(Comment).filter(
            Comment.created_at >= date,
            Comment.created_at < date_end,
            Comment.is_deleted == False
        ).count()

        data.append({
            "date": date.strftime("%Y-%m-%d"),
            "new_users": new_users,
            "new_posts": new_posts,
            "new_comments": new_comments
        })

    return data
