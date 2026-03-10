from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from app.database import get_db
from app.models import User, Log, Post
from app.schemas import UserResponse, UserUpdate, PaginatedResponse
from app.auth import get_current_active_user, require_auth, require_moderator, require_admin
from app.security import SecurityService

router = APIRouter()


@router.get("/hot")
async def get_hot_users(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    获取热门用户（公开接口，按发帖数排序）
    无需登录即可访问
    """
    # 按发帖数排序
    top_posters = db.query(User).join(Post).filter(
        Post.is_deleted == False
    ).group_by(User.id).order_by(
        desc(func.count(Post.id))
    ).limit(limit).all()

    return [UserResponse.model_validate(u).model_dump() for u in top_posters]


@router.get("/me", response_model=UserResponse)
@require_auth  # 使用装饰器：需要登录
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取当前用户信息（装饰器鉴权）
    - @require_auth装饰器表示需要登录
    """
    return current_user

@router.put("/me", response_model=UserResponse)
@require_auth
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新当前用户信息"""
    # 验证手机号（如果提供）
    if user_update.phone and not SecurityService.validate_phone(user_update.phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="手机号格式不正确"
        )

    # 更新用户信息
    for field, value in user_update.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)

    # 记录日志
    log = Log(
        user_id=current_user.id,
        action="user_update",
        extra_data={"updated_fields": list(user_update.model_dump(exclude_unset=True).keys())}
    )
    db.add(log)
    db.commit()

    return current_user

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db)
):
    """根据ID获取用户信息"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 动态计算统计数据
    from app.models import Post, Follow
    post_count = db.query(Post).filter(
        Post.author_id == user_id,
        Post.status == "published",
        Post.is_deleted == False
    ).count()
    follower_count = db.query(Follow).filter(Follow.followed_id == user_id).count()
    following_count = db.query(Follow).filter(Follow.follower_id == user_id).count()

    # 将统计数据添加到返回结果
    user_dict = UserResponse.model_validate(user).model_dump()
    user_dict['post_count'] = post_count
    user_dict['follower_count'] = follower_count
    user_dict['following_count'] = following_count

    return user_dict

@router.get("/{user_id}/posts")
async def get_user_posts(
    user_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取用户的帖子列表"""
    from app.models import Post
    from sqlalchemy import desc

    query = db.query(Post).filter(
        Post.author_id == user_id,
        Post.status == "published",
        Post.is_deleted == False
    ).order_by(desc(Post.created_at))

    total = query.count()
    posts = query.offset((page - 1) * page_size).limit(page_size).all()

    # 加载关联数据
    from app.schemas import PostListResponse, UserResponse as UserResp, CategoryResponse
    from app.models import Category

    items = []
    for post in posts:
        author = db.query(User).filter(User.id == post.author_id).first()
        category = db.query(Category).filter(Category.id == post.category_id).first()
        post_dict = {
            **PostListResponse.model_validate(post).model_dump(),
            "author": UserResp.model_validate(author).model_dump() if author else None,
            "category": CategoryResponse.model_validate(category).model_dump() if category else None
        }
        items.append(post_dict)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

@router.get("/", response_model=PaginatedResponse)
@require_moderator  # 使用装饰器：需要版主或管理员权限
async def get_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    role: Optional[str] = None,
    user_group: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取用户列表（装饰器鉴权）
    - @require_moderator装饰器表示需要版主或管理员权限
    """
    query = db.query(User)

    # 搜索
    if search:
        query = query.filter(
            User.username.contains(search) |
            User.email.contains(search)
        )

    # 筛选角色
    if role:
        query = query.filter(User.role == role)

    # 筛选用户组
    if user_group:
        query = query.filter(User.user_group == user_group)

    # 总数
    total = query.count()

    # 分页
    users = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "items": [UserResponse.model_validate(u).model_dump() for u in users],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

@router.delete("/me")
@require_auth
async def delete_current_user(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除当前用户账号"""
    # 软删除
    current_user.is_active = False
    current_user.email = f"deleted_{current_user.id}@deleted.com"
    current_user.username = f"deleted_{current_user.id}"
    db.commit()

    return {"message": "账号已删除"}

@router.post("/{user_id}/ban")
@require_admin  # 使用装饰器：需要管理员权限
async def ban_user(
    user_id: int,
    ban_reason: str,
    ban_until: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    封禁用户（装饰器鉴权）
    - @require_admin装饰器表示需要管理员权限
    """
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    if target_user.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无法封禁管理员"
        )

    target_user.is_banned = True
    target_user.ban_reason = ban_reason

    if ban_until:
        from datetime import datetime
        target_user.ban_until = datetime.fromisoformat(ban_until)

    db.commit()

    return {"message": f"用户 {target_user.username} 已被封禁"}

@router.post("/{user_id}/unban")
@require_admin
async def unban_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """解封用户（管理员）"""
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    target_user.is_banned = False
    target_user.ban_reason = None
    target_user.ban_until = None
    db.commit()

    return {"message": f"用户 {target_user.username} 已解封"}
