from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.database import get_db
from app.models import Comment, User, Post
from app.schemas import CommentCreate, CommentUpdate, CommentResponse, PaginatedResponse, UserResponse
from app.auth import get_current_active_user, require_auth
from app.security import SecurityService
from app.utils.notification import NotificationService

router = APIRouter()

def build_comment_tree(comment: Comment, db: Session) -> dict:
    """递归构建评论树"""
    author = db.query(User).filter(User.id == comment.author_id).first()
    reply_to_user = db.query(User).filter(User.id == comment.reply_to_user_id).first() if comment.reply_to_user_id else None

    # 获取所有子评论（排除隐藏和删除的）
    child_comments = db.query(Comment).filter(
        Comment.parent_id == comment.id,
        Comment.is_deleted == False,
        Comment.is_hidden == False
    ).order_by(Comment.created_at).all()

    comment_dict = {
        **CommentResponse.model_validate(comment).model_dump(),
        "author": UserResponse.model_validate(author).model_dump() if author else None,
        "reply_to_user": UserResponse.model_validate(reply_to_user).model_dump() if reply_to_user else None,
        "replies": [build_comment_tree(child, db) for child in child_comments]
    }

    return comment_dict

@router.get("/post/{post_id}", response_model=PaginatedResponse)
async def get_post_comments(
    post_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取帖子的评论列表（支持无限层级回复）"""
    # 检查帖子是否存在
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="帖子不存在"
        )

    # 获取顶级评论（排除隐藏和删除的）
    query = db.query(Comment).filter(
        Comment.post_id == post_id,
        Comment.parent_id == None,
        Comment.is_deleted == False,
        Comment.is_hidden == False
    ).order_by(Comment.created_at)

    total = query.count()
    comments = query.offset((page - 1) * page_size).limit(page_size).all()

    # 递归加载所有层级的回复
    result = [build_comment_tree(comment, db) for comment in comments]

    return {
        "items": result,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

@router.post("/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
@require_auth  # 使用装饰器：需要登录
async def create_comment(
    comment: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    创建评论（装饰器鉴权）
    - @require_auth装饰器表示需要登录
    """
    # 检查帖子是否存在
    post = db.query(Post).filter(Post.id == comment.post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="帖子不存在"
        )

    # 检查帖子是否被锁定
    if post.is_locked and current_user.role not in ["moderator", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="帖子已被锁定，无法评论"
        )

    # 检查父评论是否存在（如果是回复）
    if comment.parent_id:
        parent_comment = db.query(Comment).filter(Comment.id == comment.parent_id).first()
        if not parent_comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="父评论不存在"
            )

    # 检查被回复用户是否存在
    if comment.reply_to_user_id:
        reply_to_user = db.query(User).filter(User.id == comment.reply_to_user_id).first()
        if not reply_to_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="被回复用户不存在"
            )

    # 验证内容
    has_sensitive, word = SecurityService.check_sensitive_word(comment.content)
    if has_sensitive:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"内容包含敏感词: {word}"
        )

    # 创建评论
    db_comment = Comment(
        **comment.model_dump(),
        author_id=current_user.id
    )
    db.add(db_comment)

    # 更新帖子评论数
    post.comment_count += 1

    # 增加用户经验和积分
    current_user.exp += 2
    current_user.points += 2

    db.commit()
    db.refresh(db_comment)

    # 发送回复通知
    from app.schemas import NotificationType
    if comment.reply_to_user_id and comment.reply_to_user_id != current_user.id:
        NotificationService.create_notification(
            db=db,
            user_id=comment.reply_to_user_id,
            notification_type=NotificationType.REPLY.value,
            title=f"{current_user.username} 回复了你的评论",
            content=comment.content[:100],
            related_id=db_comment.id
        )

    # 发送评论通知给帖子作者（如果不是作者自己评论）
    if post.author_id != current_user.id:
        # 如果回复的不是帖子作者，才给帖子作者发送通知
        if not comment.reply_to_user_id or comment.reply_to_user_id != post.author_id:
            NotificationService.create_notification(
                db=db,
                user_id=post.author_id,
                notification_type=NotificationType.REPLY.value,
                title=f"{current_user.username} 评论了你的帖子",
                content=comment.content[:100],
                related_id=db_comment.id
            )

    # 发送@通知
    mentions = SecurityService.extract_mentions(comment.content)
    for username in mentions:
        mentioned_user = db.query(User).filter(User.username == username).first()
        if mentioned_user and mentioned_user.id != current_user.id:
            NotificationService.create_notification(
                db=db,
                user_id=mentioned_user.id,
                notification_type=NotificationType.MENTION.value,
                title=f"{current_user.username} 在评论中提到了你",
                content=comment.content[:100],
                related_id=db_comment.id
            )

    # 加载关联数据
    author = db.query(User).filter(User.id == db_comment.author_id).first()

    return {
        **CommentResponse.model_validate(db_comment).model_dump(),
        "author": UserResponse.model_validate(author).model_dump() if author else None,
        "replies": []
    }

@router.put("/{comment_id}", response_model=CommentResponse)
@require_auth
async def update_comment(
    comment_id: int,
    comment_update: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新评论"""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="评论不存在"
        )

    # 检查权限
    if comment.author_id != current_user.id and current_user.role not in ["moderator", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权编辑此评论"
        )

    # 验证内容
    if comment_update.content:
        has_sensitive, word = SecurityService.check_sensitive_word(comment_update.content)
        if has_sensitive:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"内容包含敏感词: {word}"
            )

    # 更新字段
    for field, value in comment_update.model_dump(exclude_unset=True).items():
        setattr(comment, field, value)

    comment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(comment)

    # 加载关联数据
    author = db.query(User).filter(User.id == comment.author_id).first()

    return {
        **CommentResponse.model_validate(comment).model_dump(),
        "author": UserResponse.model_validate(author).model_dump() if author else None,
        "replies": []
    }

@router.delete("/{comment_id}")
@require_auth  # 使用装饰器：需要登录
async def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    删除评论（装饰器鉴权）
    - @require_auth装饰器表示需要登录
    """
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="评论不存在"
        )

    # 检查权限
    if comment.author_id != current_user.id and current_user.role not in ["moderator", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此评论"
        )

    # 软删除
    comment.is_deleted = True

    # 更新帖子评论数
    post = db.query(Post).filter(Post.id == comment.post_id).first()
    if post and post.comment_count > 0:
        post.comment_count -= 1

    db.commit()

    return {"message": "评论已删除"}


@router.post("/{comment_id}/hide")
@require_auth
async def toggle_comment_visibility(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """隐藏/取消隐藏评论（仅管理员/版主）"""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="评论不存在"
        )

    # 检查权限
    if current_user.role not in ["moderator", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权隐藏评论"
        )

    comment.is_hidden = not comment.is_hidden
    db.commit()

    action = "隐藏" if comment.is_hidden else "取消隐藏"
    return {"message": f"评论已{action}", "is_hidden": comment.is_hidden}

