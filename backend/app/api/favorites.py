from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Favorite, User, Post, Category
from app.schemas import FavoriteCreate, PostListResponse, PaginatedResponse, UserResponse, CategoryResponse
from app.auth import get_current_active_user, require_auth

router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED)
@require_auth
async def add_favorite(
    favorite: FavoriteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """收藏帖子"""
    # 检查帖子是否存在
    post = db.query(Post).filter(Post.id == favorite.post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="帖子不存在"
        )

    # 检查是否已收藏
    existing = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.post_id == favorite.post_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已经收藏过该帖子"
        )

    # 创建收藏
    db_favorite = Favorite(
        user_id=current_user.id,
        post_id=favorite.post_id
    )
    db.add(db_favorite)
    db.commit()

    return {"message": "收藏成功"}

@router.delete("/{post_id}")
@require_auth
async def remove_favorite(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """取消收藏帖子"""
    favorite = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.post_id == post_id
    ).first()

    if not favorite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未收藏该帖子"
        )

    db.delete(favorite)
    db.commit()

    return {"message": "已取消收藏"}

@router.get("/", response_model=PaginatedResponse)
@require_auth
async def get_my_favorites(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取我的收藏列表"""
    from sqlalchemy import desc

    query = db.query(Favorite).filter(
        Favorite.user_id == current_user.id
    ).order_by(desc(Favorite.created_at))

    total = query.count()
    favorites = query.offset((page - 1) * page_size).limit(page_size).all()

    # 加载帖子数据
    items = []
    for favorite in favorites:
        post = db.query(Post).filter(Post.id == favorite.post_id).first()
        if post:
            author = db.query(User).filter(User.id == post.author_id).first()
            category = db.query(Category).filter(Category.id == post.category_id).first() if post.category_id else None
            if category:
                post_dict = {
                    **PostListResponse.model_validate(post).model_dump(),
                    "author": UserResponse.model_validate(author).model_dump() if author else None,
                    "category": CategoryResponse.model_validate(category).model_dump()
                }
                items.append(post_dict)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }
