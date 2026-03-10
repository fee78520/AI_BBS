"""
BBS论坛系统 - 装饰器鉴权使用示例
本文件展示如何使用装饰器方式进行API鉴权
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Post, Comment
from app.schemas import PostCreate, PostResponse, CommentCreate, CommentResponse
from app.auth import (
    get_current_active_user,  # 依赖注入方式（原有方式）
    auth_required,          # 装饰器方式（新增）
    require_auth,            # 需要登录装饰器
    require_moderator,       # 需要版主权限装饰器
    require_admin            # 需要管理员权限装饰器
)

router = APIRouter()

# ========== 装饰器鉴权示例 ==========

@router.get("/decorator/posts")
@require_auth  # 使用装饰器：需要登录
async def get_posts_with_decorator(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),  # 仍需要注入current_user
    db: Session = Depends(get_db)
):
    """
    获取帖子列表（使用装饰器鉴权）
    - 使用@require_auth装饰器表示需要登录
    - current_user由FastAPI依赖注入提供
    - 装饰器会检查用户是否已登录
    """
    posts = db.query(Post).filter(Post.author_id == current_user.id).all()
    return {
        "posts": posts,
        "total": len(posts),
        "user": current_user.username
    }


@router.get("/decorator/admin/stats")
@require_admin  # 使用装饰器：需要管理员权限
async def get_admin_stats_with_decorator(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    获取管理员统计数据（使用装饰器鉴权）
    - 使用@require_admin装饰器表示需要管理员权限
    - 只有管理员角色才能访问此接口
    """
    from app.models import User, Post, Comment

    stats = {
        "total_users": db.query(User).count(),
        "total_posts": db.query(Post).count(),
        "total_comments": db.query(Comment).count(),
        "admin": current_user.username
    }
    return stats


@router.post("/decorator/posts")
@require_auth  # 需要登录
async def create_post_with_decorator(
    post: PostCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    创建帖子（使用装饰器鉴权）
    """
    db_post = Post(
        **post.model_dump(),
        author_id=current_user.id
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


@router.post("/decorator/posts/{post_id}/pin")
@require_moderator  # 需要版主或管理员权限
async def pin_post_with_decorator(
    post_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    置顶帖子（使用装饰器鉴权）
    - 使用@require_moderator装饰器表示需要版主或管理员权限
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


# ========== 自定义角色鉴权 ==========

@router.get("/decorator/vip/posts")
@auth_required(required_roles=["user", "moderator", "admin"])  # 指定允许的角色
async def get_vip_posts_with_decorator(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    获取VIP帖子（自定义角色鉴权）
    - 使用auth_required装饰器指定允许的角色列表
    - 只有user、moderator、admin角色可以访问
    """
    return {
        "message": "VIP内容",
        "user": current_user.username,
        "role": current_user.role
    }


# ========== 公开接口示例（无需鉴权）==========

@router.get("/decorator/public/posts")
async def get_public_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    获取公开帖子列表（无需鉴权）
    - 不使用任何装饰器或依赖
    - 所有用户都可以访问
    """
    posts = db.query(Post).limit(page_size).offset((page - 1) * page_size).all()
    return {
        "posts": posts,
        "page": page,
        "page_size": page_size
    }


# ========== 装饰器与依赖混合使用示例 ==========

@router.get("/decorator/mixed/example")
@require_auth  # 装饰器处理登录验证
async def mixed_auth_example(
    current_user: User = Depends(get_current_active_user),  # 依赖注入用户对象
    db: Session = Depends(get_db)  # 依赖注入数据库会话
):
    """
    混合使用示例
    - 装饰器@require_auth处理权限验证
    - Depends注入需要的依赖对象（用户、数据库等）
    - 装饰器和依赖可以配合使用
    """
    return {
        "user": current_user.username,
        "role": current_user.role,
        "user_id": current_user.id,
        "message": "使用装饰器和依赖混合鉴权"
    }


# ========== 装饰器鉴权对比 ==========

class DecoratorComparison:
    """
    装饰器方式 vs 依赖方式对比

    依赖方式（原有方式）:
    ---------------------
    @router.get("/posts")
    async def get_posts(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        pass

    优点:
    - FastAPI原生支持，自动生成文档
    - 类型提示清晰
    - 可以依赖多个参数

    缺点:
    - 每个函数都需要声明依赖参数
    - 代码稍显冗长

    装饰器方式（新增方式）:
    ---------------------
    @router.get("/posts")
    @require_auth
    async def get_posts(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        pass

    优点:
    - 代码更简洁，意图更明确
    - 权限要求一目了然
    - 支持自定义角色列表

    缺点:
    - 需要手动注入current_user
    - 仍然需要使用Depends注入其他依赖

    推荐使用:
    -----------
    - 简单场景：使用装饰器方式，代码更清晰
    - 复杂场景：使用依赖方式，更灵活
    - 两种方式可以混合使用
    """

    pass


# ========== 装饰器使用建议 ==========

"""
装饰器使用建议：

1. 需要登录的接口
   @require_auth
   async def my_endpoint(current_user: User = Depends(get_current_active_user)):
       pass

2. 需要版主/管理员权限的接口
   @require_moderator
   async def my_endpoint(current_user: User = Depends(get_current_active_user)):
       pass

3. 需要管理员权限的接口
   @require_admin
   async def my_endpoint(current_user: User = Depends(get_current_active_user)):
       pass

4. 自定义角色列表
   @auth_required(required_roles=["user", "vip"])
   async def my_endpoint(current_user: User = Depends(get_current_active_user)):
       pass

5. 公开接口（无需鉴权）
   async def my_endpoint():
       pass

注意事项：
- 装饰器只做权限验证，不注入参数
- 仍需使用Depends注入current_user、db等依赖
- 装饰器会自动抛出HTTPException，无需手动处理
- 装饰器支持async和sync函数
"""
