from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models import Post, User, Category, SearchHistory
from app.schemas import SearchQuery, SearchResult, PostListResponse, UserResponse, CategoryResponse, PaginatedResponse
from app.auth import get_current_active_user

router = APIRouter()

@router.post("/", response_model=SearchResult)
async def search(
    query: SearchQuery,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """搜索内容"""
    if not query.keyword or len(query.keyword.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="搜索关键词不能为空"
        )

    results = {"posts": [], "users": [], "total": 0, "page": query.page, "page_size": query.page_size}

    # 搜索帖子
    if query.search_type in ["all", "posts"]:
        posts_query = db.query(Post).filter(
            Post.status == "published",
            Post.is_deleted == False
        )

        # 关键词搜索
        if query.keyword:
            posts_query = posts_query.filter(
                or_(
                    Post.title.contains(query.keyword),
                    Post.content.contains(query.keyword)
                )
            )

        # 版块筛选
        if query.category_id:
            posts_query = posts_query.filter(Post.category_id == query.category_id)

        # 帖子类型筛选
        if query.post_type:
            posts_query = posts_query.filter(Post.post_type == query.post_type)

        # 日期范围筛选
        if query.date_from:
            posts_query = posts_query.filter(Post.created_at >= query.date_from)
        if query.date_to:
            posts_query = posts_query.filter(Post.created_at <= query.date_to)

        # 排序
        order_column = getattr(Post, query.sort_by)
        if query.sort_order == "desc":
            posts_query = posts_query.order_by(desc(order_column))
        else:
            posts_query = posts_query.order_by(order_column)

        # 分页
        total_posts = posts_query.count()
        posts = posts_query.offset((query.page - 1) * query.page_size).limit(query.page_size).all()

        # 加载关联数据
        for post in posts:
            author = db.query(User).filter(User.id == post.author_id).first()
            category = db.query(Category).filter(Category.id == post.category_id).first()
            results["posts"].append({
                **PostListResponse.model_validate(post).model_dump(),
                "author": UserResponse.model_validate(author).model_dump() if author else None,
                "category": CategoryResponse.model_validate(category).model_dump() if category else None
            })

        results["total"] += total_posts

    # 搜索用户
    if query.search_type in ["all", "users"]:
        users_query = db.query(User).filter(
            User.is_active == True
        ).filter(
            or_(
                User.username.contains(query.keyword),
                User.email.contains(query.keyword),
                User.bio.contains(query.keyword)
            )
        ).order_by(User.created_at.desc())

        users = users_query.limit(query.page_size).all()
        for user in users:
            results["users"].append(UserResponse.model_validate(user).model_dump())

        results["total"] += users_query.count()

    # 保存搜索历史
    history = SearchHistory(
        user_id=current_user.id,
        keyword=query.keyword,
        result_count=results["total"]
    )
    db.add(history)
    db.commit()

    return results

@router.get("/history", response_model=List[str])
async def get_search_history(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取搜索历史"""
    from sqlalchemy import distinct, desc

    keywords = db.query(SearchHistory.keyword).filter(
        SearchHistory.user_id == current_user.id
    ).order_by(
        desc(SearchHistory.created_at)
    ).distinct().limit(limit).all()

    return [k[0] for k in keywords]

@router.delete("/history")
async def clear_search_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """清空搜索历史"""
    db.query(SearchHistory).filter(
        SearchHistory.user_id == current_user.id
    ).delete()

    db.commit()

    return {"message": "搜索历史已清空"}
