from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import SystemSetting, User
from app.schemas import SystemSettingUpdate, SystemSettingResponse
from app.auth import get_current_active_user, require_admin

router = APIRouter()

@router.get("/", response_model=List[SystemSettingResponse])
async def get_system_settings(
    db: Session = Depends(get_db)
):
    """获取系统设置"""
    settings = db.query(SystemSetting).all()
    return [SystemSettingResponse.model_validate(s).model_dump() for s in settings]

@router.get("/{key}", response_model=SystemSettingResponse)
async def get_system_setting(
    key: str,
    db: Session = Depends(get_db)
):
    """获取单个系统设置"""
    setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="设置不存在"
        )
    return SystemSettingResponse.model_validate(setting).model_dump()

@router.put("/{key}", response_model=SystemSettingResponse)
@require_admin
async def update_system_setting(
    key: str,
    setting_update: SystemSettingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新系统设置"""
    setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="设置不存在"
        )

    setting.value = setting_update.value
    db.commit()
    db.refresh(setting)

    return SystemSettingResponse.model_validate(setting).model_dump()

@router.post("/init-defaults")
@require_admin
async def init_default_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """初始化默认系统设置"""
    default_settings = [
        {"key": "site_name", "value": "我的BBS论坛", "description": "网站名称"},
        {"key": "site_description", "value": "一个优秀的论坛系统", "description": "网站描述"},
        {"key": "site_keywords", "value": "论坛,BBS,社区", "description": "网站关键词"},
        {"key": "allow_register", "value": "true", "description": "是否允许新用户注册"},
        {"key": "require_email_verify", "value": "false", "description": "是否需要邮箱验证"},
        {"key": "default_user_group", "value": "normal", "description": "默认用户组"},
        {"key": "post_require_review", "value": "false", "description": "发帖是否需要审核"},
        {"key": "post_min_length", "value": "10", "description": "帖子最小字数"},
        {"key": "post_max_length", "value": "50000", "description": "帖子最大字数"},
        {"key": "comment_require_review", "value": "false", "description": "评论是否需要审核"},
        {"key": "comment_min_length", "value": "1", "description": "评论最小字数"},
        {"key": "comment_max_length", "value": "5000", "description": "评论最大字数"},
        {"key": "points_per_post", "value": "5", "description": "发帖获得积分"},
        {"key": "points_per_comment", "value": "1", "description": "评论获得积分"},
        {"key": "points_per_like", "value": "1", "description": "被点赞获得积分"},
        {"key": "allow_image_upload", "value": "true", "description": "是否允许上传图片"},
        {"key": "max_image_size", "value": "5", "description": "图片最大大小(MB)"},
        {"key": "allowed_image_types", "value": "jpg,jpeg,png,gif,webp", "description": "允许的图片类型"},
    ]

    created_count = 0
    for setting_data in default_settings:
        existing = db.query(SystemSetting).filter(
            SystemSetting.key == setting_data["key"]
        ).first()

        if not existing:
            setting = SystemSetting(**setting_data)
            db.add(setting)
            created_count += 1

    db.commit()

    return {"message": f"已初始化 {created_count} 个默认设置"}
