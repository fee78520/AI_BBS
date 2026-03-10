from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import Category, CategoryModerator, User, Post
from app.schemas import CategoryCreate, CategoryUpdate, CategoryResponse, CategoryWithChildren, PaginatedResponse
from app.auth import get_current_active_user, require_admin

router = APIRouter()

@router.get("/", response_model=List[CategoryWithChildren])
async def get_categories(
    parent_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """获取版块列表"""
    query = db.query(Category)

    if parent_id is not None:
        query = query.filter(Category.parent_id == parent_id)
    else:
        query = query.filter(Category.parent_id == None)

    categories = query.order_by(Category.sort_order).all()

    # 构建层级结构
    result = []
    for category in categories:
        children = db.query(Category).filter(Category.parent_id == category.id).order_by(Category.sort_order).all()
        category_dict = {
            **CategoryResponse.model_validate(category).model_dump(),
            "children": [CategoryResponse.model_validate(child).model_dump() for child in children]
        }
        result.append(category_dict)

    return result

@router.get("/{category_id}", response_model=CategoryWithChildren)
async def get_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    """获取版块详情"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="版块不存在"
        )

    # 获取子版块
    children = db.query(Category).filter(Category.parent_id == category.id).order_by(Category.sort_order).all()

    return {
        **CategoryResponse.model_validate(category).model_dump(),
        "children": [CategoryResponse.model_validate(child).model_dump() for child in children]
    }

@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
@require_admin
async def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建版块（管理员）"""
    # 检查父版块是否存在（如果指定）
    if category.parent_id:
        parent = db.query(Category).filter(Category.id == category.parent_id).first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="父版块不存在"
            )

    db_category = Category(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)

    return db_category

@router.put("/{category_id}", response_model=CategoryResponse)
@require_admin
async def update_category(
    category_id: int,
    category_update: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新版块（管理员）"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="版块不存在"
        )

    # 检查父版块是否存在（如果指定）
    if category_update.parent_id is not None:
        if category_update.parent_id == category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能将自己设为父版块"
            )
        if category_update.parent_id:
            parent = db.query(Category).filter(Category.id == category_update.parent_id).first()
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="父版块不存在"
                )

    # 更新字段
    for field, value in category_update.model_dump(exclude_unset=True).items():
        setattr(category, field, value)

    db.commit()
    db.refresh(category)

    return category

@router.delete("/{category_id}")
@require_admin
async def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除版块（管理员）"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="版块不存在"
        )

    # 检查是否有子版块
    children = db.query(Category).filter(Category.parent_id == category_id).count()
    if children > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先删除子版块"
        )

    # 检查是否有帖子
    post_count = db.query(Post).filter(Post.category_id == category_id).count()
    if post_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"该版块下有 {post_count} 个帖子，无法删除"
        )

    db.delete(category)
    db.commit()

    return {"message": "版块已删除"}

@router.post("/{category_id}/moderators/{user_id}")
@require_admin
async def add_moderator(
    category_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """添加版主（管理员）"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="版块不存在"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 检查是否已经是版主
    existing = db.query(CategoryModerator).filter(
        CategoryModerator.category_id == category_id,
        CategoryModerator.user_id == user_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该用户已经是该版块的版主"
        )

    # 创建版主关系
    moderator = CategoryModerator(
        category_id=category_id,
        user_id=user_id
    )
    db.add(moderator)

    # 更新用户角色
    if user.role == "user":
        user.role = "moderator"

    db.commit()

    return {"message": f"已添加 {user.username} 为版块版主"}

@router.delete("/{category_id}/moderators/{user_id}")
@require_admin
async def remove_moderator(
    category_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """移除版主（管理员）"""
    moderator = db.query(CategoryModerator).filter(
        CategoryModerator.category_id == category_id,
        CategoryModerator.user_id == user_id
    ).first()

    if not moderator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="版主关系不存在"
        )

    db.delete(moderator)

    # 检查用户是否还管理其他版块
    other_count = db.query(CategoryModerator).filter(
        CategoryModerator.user_id == user_id
    ).count()

    if other_count == 0:
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.role == "moderator":
            user.role = "user"

    db.commit()

    return {"message": "已移除版主"}
