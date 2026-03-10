from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models import Like, User, Post, Comment
from app.schemas import LikeCreate
from app.auth import get_current_active_user
from app.utils.notification import NotificationService

router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED)
async def like_content(
    like: LikeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """点赞帖子或评论"""
    # 检查是否已点赞
    existing = db.query(Like).filter(
        Like.user_id == current_user.id,
        Like.post_id == like.post_id,
        Like.comment_id == like.comment_id
    ).first()

    if existing:
        # 取消点赞
        db.delete(existing)

        # 更新计数
        if like.post_id:
            post = db.query(Post).filter(Post.id == like.post_id).first()
            if post and post.like_count > 0:
                post.like_count -= 1

        if like.comment_id:
            comment = db.query(Comment).filter(Comment.id == like.comment_id).first()
            if comment and comment.like_count > 0:
                comment.like_count -= 1

        db.commit()
        return {"message": "已取消点赞", "liked": False}
    else:
        # 创建点赞
        db_like = Like(
            user_id=current_user.id,
            post_id=like.post_id,
            comment_id=like.comment_id
        )
        db.add(db_like)

        # 更新计数
        from app.schemas import NotificationType
        if like.post_id:
            post = db.query(Post).filter(Post.id == like.post_id).first()
            if post:
                post.like_count += 1
                # 发送通知
                if post.author_id != current_user.id:
                    NotificationService.create_notification(
                        db=db,
                        user_id=post.author_id,
                        notification_type=NotificationType.LIKE.value,
                        title=f"{current_user.username} 点赞了你的帖子",
                        content=post.title[:100],
                        related_id=post.id
                    )

        if like.comment_id:
            comment = db.query(Comment).filter(Comment.id == like.comment_id).first()
            if comment:
                comment.like_count += 1
                # 发送通知
                if comment.author_id != current_user.id:
                    NotificationService.create_notification(
                        db=db,
                        user_id=comment.author_id,
                        notification_type=NotificationType.LIKE.value,
                        title=f"{current_user.username} 点赞了你的评论",
                        content=comment.content[:100],
                        related_id=comment.id
                    )

        # 增加用户积分
        current_user.points += 1

        db.commit()
        return {"message": "点赞成功", "liked": True}

@router.get("/check")
async def check_like_status(
    post_id: int = None,
    comment_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """检查是否已点赞"""
    existing = db.query(Like).filter(
        Like.user_id == current_user.id,
        Like.post_id == post_id,
        Like.comment_id == comment_id
    ).first()

    return {"liked": existing is not None}

@router.get("/posts")
async def get_liked_posts(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取我点赞的帖子列表"""
    from fastapi import Query
    from sqlalchemy import desc
    from app.schemas import PostListResponse, PaginatedResponse

    # 查询用户点赞的帖子
    query = db.query(Like).filter(
        Like.user_id == current_user.id,
        Like.post_id.isnot(None)
    ).order_by(desc(Like.created_at))

    total = query.count()
    likes = query.offset((page - 1) * page_size).limit(page_size).all()

    # 加载帖子数据
    items = []
    from app.models import Category
    for like in likes:
        post = db.query(Post).filter(Post.id == like.post_id).first()
        if post:
            author = db.query(User).filter(User.id == post.author_id).first()
            category = db.query(Category).filter(Category.id == post.category_id).first() if post.category_id else None
            from app.schemas import UserResponse, CategoryResponse
            post_dict = {
                **PostListResponse.model_validate(post).model_dump(),
                "author": UserResponse.model_validate(author).model_dump() if author else None,
                "category": CategoryResponse.model_validate(category).model_dump() if category else None,
                "liked_at": like.created_at.isoformat() if like.created_at else None
            }
            items.append(post_dict)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

@router.get("/comments")
async def get_liked_comments(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取我点赞的评论列表"""
    from fastapi import Query
    from sqlalchemy import desc
    from app.schemas import CommentResponse, UserResponse, PostListResponse
    from app.models import Category

    # 查询用户点赞的评论
    query = db.query(Like).filter(
        Like.user_id == current_user.id,
        Like.comment_id.isnot(None)
    ).order_by(desc(Like.created_at))

    total = query.count()
    likes = query.offset((page - 1) * page_size).limit(page_size).all()

    # 加载评论数据
    items = []
    for like in likes:
        comment = db.query(Comment).filter(Comment.id == like.comment_id).first()
        if comment and not comment.is_deleted:
            author = db.query(User).filter(User.id == comment.author_id).first()
            post = db.query(Post).filter(Post.id == comment.post_id).first()
            category = None
            if post and post.category_id:
                category = db.query(Category).filter(Category.id == post.category_id).first()

            post_data = PostListResponse.model_validate(post).model_dump() if post else {}
            if category and post:
                post_data["category"] = CategoryResponse.model_validate(category).model_dump()

            comment_dict = {
                **CommentResponse.model_validate(comment).model_dump(),
                "author": UserResponse.model_validate(author).model_dump() if author else None,
                "post": post_data if post else None,
                "liked_at": like.created_at.isoformat() if like.created_at else None
            }
            items.append(comment_dict)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }
