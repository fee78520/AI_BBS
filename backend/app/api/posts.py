from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models import Post, User, Category, Comment
from app.schemas import PostCreate, PostUpdate, PostResponse, PostListResponse, PaginatedResponse, UserResponse, CategoryResponse
from app.auth import (
    get_current_active_user,
    get_optional_user,
    require_auth,
    require_moderator
)
from app.security import SecurityService
from app.utils.notification import NotificationService

router = APIRouter()

@router.get("/", response_model=PaginatedResponse)
async def get_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = None,
    post_type: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = Query("created_at", regex="^(created_at|updated_at|view_count|like_count|comment_count)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    include_hidden: bool = Query(False, description="是否包含隐藏内容（仅管理员）"),
    db: Session = Depends(get_db)
):
    """获取帖子列表"""
    query = db.query(Post).filter(Post.status == "published", Post.is_deleted == False)

    # 过滤隐藏内容（普通用户不可见）
    if not include_hidden:
        query = query.filter(Post.is_hidden == False)

    # 筛选版块
    if category_id:
        query = query.filter(Post.category_id == category_id)

    # 筛选帖子类型
    if post_type:
        query = query.filter(Post.post_type == post_type)

    # 搜索
    if search:
        query = query.filter(
            or_(
                Post.title.contains(search),
                Post.content.contains(search)
            )
        )

    # 排序
    order_column = getattr(Post, sort_by)
    if sort_order == "desc":
        query = query.order_by(desc(order_column))
    else:
        query = query.order_by(order_column)

    # 总数
    total = query.count()

    # 分页
    posts = query.offset((page - 1) * page_size).limit(page_size).all()

    # 加载关联数据
    result = []
    for post in posts:
        author = db.query(User).filter(User.id == post.author_id).first()
        category = db.query(Category).filter(Category.id == post.category_id).first()
        post_dict = {
            **PostListResponse.model_validate(post).model_dump(),
            "author": UserResponse.model_validate(author).model_dump() if author else None,
            "category": CategoryResponse.model_validate(category).model_dump() if category else None
        }
        result.append(post_dict)

    return {
        "items": result,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

@router.get("/hot", response_model=List[PostListResponse])
async def get_hot_posts(
    limit: int = Query(10, ge=1, le=50),
    include_hidden: bool = Query(False, description="是否包含隐藏内容（仅管理员）"),
    db: Session = Depends(get_db)
):
    """获取热门帖子"""
    query = db.query(Post).filter(
        Post.status == "published",
        Post.is_deleted == False
    )

    if not include_hidden:
        query = query.filter(Post.is_hidden == False)

    posts = query.order_by(
        Post.view_count.desc(),
        Post.like_count.desc(),
        Post.comment_count.desc()
    ).limit(limit).all()

    # 加载关联数据
    result = []
    for post in posts:
        author = db.query(User).filter(User.id == post.author_id).first()
        category = db.query(Category).filter(Category.id == post.category_id).first()
        post_dict = {
            **PostListResponse.model_validate(post).model_dump(),
            "author": UserResponse.model_validate(author).model_dump() if author else None,
            "category": CategoryResponse.model_validate(category).model_dump() if category else None
        }
        result.append(post_dict)

    return result

@router.get("/trash", response_model=PaginatedResponse)
@require_moderator
async def get_trash_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    filter_type: str = Query("all", regex="^(all|hidden|deleted)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取回收站帖子（隐藏和删除的帖子）- 仅管理员"""
    query = db.query(Post)

    # 根据筛选类型过滤
    if filter_type == "hidden":
        query = query.filter(Post.is_hidden == True, Post.is_deleted == False)
    elif filter_type == "deleted":
        query = query.filter(Post.is_deleted == True)
    else:  # all
        query = query.filter(or_(Post.is_hidden == True, Post.is_deleted == True))

    query = query.order_by(desc(Post.updated_at))

    total = query.count()
    posts = query.offset((page - 1) * page_size).limit(page_size).all()

    # 加载关联数据
    result = []
    for post in posts:
        author = db.query(User).filter(User.id == post.author_id).first()
        category = db.query(Category).filter(Category.id == post.category_id).first()
        post_dict = {
            **PostListResponse.model_validate(post).model_dump(),
            "author": UserResponse.model_validate(author).model_dump() if author else None,
            "category": CategoryResponse.model_validate(category).model_dump() if category else None
        }
        result.append(post_dict)

    return {
        "items": result,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """获取帖子详情"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="帖子不存在"
        )

    # 检查隐藏/删除状态：隐藏或删除的帖子仅管理员/版主可查看
    if post.is_hidden or post.is_deleted:
        if not current_user or current_user.role not in ["moderator", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="帖子不存在"
            )

    # 增加浏览量
    post.view_count += 1
    db.commit()

    # 加载关联数据
    author = db.query(User).filter(User.id == post.author_id).first()
    category = db.query(Category).filter(Category.id == post.category_id).first()

    return {
        **PostResponse.model_validate(post).model_dump(),
        "author": UserResponse.model_validate(author).model_dump() if author else None,
        "category": CategoryResponse.model_validate(category).model_dump() if category else None
    }

@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
@require_auth  # 使用装饰器：需要登录
async def create_post(
    post: PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    创建帖子（装饰器鉴权）
    - @require_auth装饰器表示需要登录
    - current_user由Depends注入
    """
    # 验证版块是否存在
    category = db.query(Category).filter(Category.id == post.category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="版块不存在"
        )

    # 检查发帖权限
    if category.can_post > current_user.level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"需要达到等级 {category.can_post} 才能在此版块发帖"
        )

    # 验证标题
    is_valid, msg = SecurityService.validate_post_title(post.title)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg
        )

    # 验证内容
    is_valid, msg = SecurityService.validate_post_content(post.content)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg
        )

    # 提取@用户
    mentions = SecurityService.extract_mentions(post.content)

    # 创建帖子
    db_post = Post(
        **post.model_dump(),
        author_id=current_user.id
    )
    db.add(db_post)

    # 更新版块帖子数
    category.post_count += 1

    # 增加用户经验和积分
    current_user.exp += 5
    current_user.points += 5

    db.commit()
    db.refresh(db_post)

    # 发送@通知
    from app.schemas import NotificationType
    for username in mentions:
        mentioned_user = db.query(User).filter(User.username == username).first()
        if mentioned_user:
            NotificationService.create_notification(
                db=db,
                user_id=mentioned_user.id,
                notification_type=NotificationType.MENTION.value,
                title=f"{current_user.username} 在帖子中提到了你",
                content=f"帖子：{post.title}",
                related_id=db_post.id
            )

    # 加载关联数据
    author = db.query(User).filter(User.id == db_post.author_id).first()
    category = db.query(Category).filter(Category.id == db_post.category_id).first()

    return {
        **PostResponse.model_validate(db_post).model_dump(),
        "author": UserResponse.model_validate(author).model_dump() if author else None,
        "category": CategoryResponse.model_validate(category).model_dump() if category else None
    }

@router.put("/{post_id}", response_model=PostResponse)
@require_auth  # 使用装饰器：需要登录
async def update_post(
    post_id: int,
    post_update: PostUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    更新帖子（装饰器鉴权）
    - @require_auth装饰器表示需要登录
    """
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="帖子不存在"
        )

    # 检查权限
    if post.author_id != current_user.id and current_user.role not in ["moderator", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权编辑此帖子"
        )

    # 如果帖子被锁定，只有管理员可以编辑
    if post.is_locked and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="帖子已被锁定，无法编辑"
        )

    # 更新字段
    for field, value in post_update.model_dump(exclude_unset=True).items():
        if field == "title" and value:
            is_valid, msg = SecurityService.validate_post_title(value)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=msg
                )
        if field == "content" and value:
            is_valid, msg = SecurityService.validate_post_content(value)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=msg
                )
        setattr(post, field, value)

    post.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(post)

    # 加载关联数据
    author = db.query(User).filter(User.id == post.author_id).first()
    category = db.query(Category).filter(Category.id == post.category_id).first()

    return {
        **PostResponse.model_validate(post).model_dump(),
        "author": UserResponse.model_validate(author).model_dump() if author else None,
        "category": CategoryResponse.model_validate(category).model_dump() if category else None
    }

@router.delete("/{post_id}")
@require_auth  # 使用装饰器：需要登录
async def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    删除帖子（装饰器鉴权）
    - @require_auth装饰器表示需要登录
    """
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="帖子不存在"
        )

    # 检查权限
    if post.author_id != current_user.id and current_user.role not in ["moderator", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此帖子"
        )

    # 软删除
    post.is_deleted = True
    post.status = "deleted"

    # 更新版块帖子数
    category = db.query(Category).filter(Category.id == post.category_id).first()
    if category and category.post_count > 0:
        category.post_count -= 1

    db.commit()

    return {"message": "帖子已删除"}

@router.post("/{post_id}/pin")
@require_moderator  # 使用装饰器：需要版主或管理员权限
async def pin_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    置顶帖子（装饰器鉴权）
    - @require_moderator装饰器表示需要版主或管理员权限
    """
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="帖子不存在"
        )

    post.is_pinned = not post.is_pinned
    db.commit()

    action = "置顶" if post.is_pinned else "取消置顶"
    return {"message": f"帖子已{action}"}

@router.post("/{post_id}/lock")
@require_moderator  # 使用装饰器：需要版主或管理员权限
async def lock_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    锁定帖子（装饰器鉴权）
    - @require_moderator装饰器表示需要版主或管理员权限
    """
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="帖子不存在"
        )

    post.is_locked = not post.is_locked
    db.commit()

    action = "锁定" if post.is_locked else "解锁"
    return {"message": f"帖子已{action}"}


@router.post("/{post_id}/essence")
@require_moderator  # 使用装饰器：需要版主或管理员权限
async def set_essence(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    设置/取消精华帖子（装饰器鉴权）
    - @require_moderator装饰器表示需要版主或管理员权限
    """
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="帖子不存在"
        )

    from app.schemas import PostType
    if post.post_type == PostType.ESSENCE:
        post.post_type = PostType.NORMAL
        action = "取消精华"
    else:
        post.post_type = PostType.ESSENCE
        action = "设为精华"

    db.commit()

    return {"message": f"帖子已{action}", "post_type": post.post_type.value}


@router.post("/{post_id}/hide")
@require_moderator
async def toggle_post_visibility(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """隐藏/取消隐藏帖子（仅管理员/版主）"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="帖子不存在"
        )

    post.is_hidden = not post.is_hidden
    db.commit()

    action = "隐藏" if post.is_hidden else "取消隐藏"
    return {"message": f"帖子已{action}", "is_hidden": post.is_hidden}


@router.post("/{post_id}/restore")
@require_moderator
async def restore_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """恢复已删除的帖子（仅管理员/版主）"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="帖子不存在"
        )

    # 恢复帖子
    post.is_deleted = False
    post.is_hidden = False
    post.status = "published"

    # 恢新版块帖子数
    category = db.query(Category).filter(Category.id == post.category_id).first()
    if category:
        category.post_count += 1

    db.commit()

    return {"message": "帖子已恢复"}

