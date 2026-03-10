from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
import os
import uuid
from pathlib import Path
from typing import Tuple
from datetime import datetime
from app.database import get_db
from app.models import User, Attachment
from app.auth import get_current_active_user
from app.schemas import AttachmentResponse

router = APIRouter()

# 允许的文件类型
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
ALLOWED_FILE_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt", ".zip", ".rar"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_FILE_SIZE = 50 * 1024 * 1024   # 50MB

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# 创建子目录
(UPLOAD_DIR / "images").mkdir(exist_ok=True)
(UPLOAD_DIR / "files").mkdir(exist_ok=True)

def get_file_extension(filename: str) -> str:
    """获取文件扩展名"""
    return Path(filename).suffix.lower()

def generate_unique_filename(original_filename: str) -> str:
    """生成唯一文件名"""
    ext = get_file_extension(original_filename)
    unique_name = f"{uuid.uuid4().hex}{ext}"
    return unique_name

async def save_upload_file(
    upload_file: UploadFile,
    destination: Path,
    max_size: int
) -> Tuple[str, int, str]:
    """保存上传的文件"""
    # 检查文件大小
    content = await upload_file.read()
    file_size = len(content)

    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件大小超过限制（最大 {max_size // 1024 // 1024}MB）"
        )

    # 保存文件
    unique_filename = generate_unique_filename(upload_file.filename)
    file_path = destination / unique_filename

    with open(file_path, "wb") as f:
        f.write(content)

    return unique_filename, file_size, upload_file.content_type

@router.post("/image", response_model=AttachmentResponse, status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(...),
    post_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """上传图片"""
    # 检查文件扩展名
    ext = get_file_extension(file.filename)
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的图片格式，允许的格式：{', '.join(ALLOWED_IMAGE_EXTENSIONS)}"
        )

    # 保存文件
    try:
        filename, file_size, content_type = await save_upload_file(
            file,
            UPLOAD_DIR / "images",
            MAX_IMAGE_SIZE
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件上传失败：{str(e)}"
        )

    # 创建附件记录
    attachment = Attachment(
        user_id=current_user.id,
        post_id=post_id,
        filename=filename,
        file_path=f"/uploads/images/{filename}",
        file_size=file_size,
        file_type=content_type
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)

    return attachment

@router.post("/file", response_model=AttachmentResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    post_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """上传文件"""
    # 检查文件扩展名
    ext = get_file_extension(file.filename)
    if ext not in ALLOWED_FILE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件格式，允许的格式：{', '.join(ALLOWED_FILE_EXTENSIONS)}"
        )

    # 保存文件
    try:
        filename, file_size, content_type = await save_upload_file(
            file,
            UPLOAD_DIR / "files",
            MAX_FILE_SIZE
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件上传失败：{str(e)}"
        )

    # 创建附件记录
    attachment = Attachment(
        user_id=current_user.id,
        post_id=post_id,
        filename=filename,
        file_path=f"/uploads/files/{filename}",
        file_size=file_size,
        file_type=content_type
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)

    return attachment

@router.delete("/{attachment_id}")
async def delete_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除附件"""
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="附件不存在"
        )

    # 检查权限
    if attachment.user_id != current_user.id and current_user.role not in ["moderator", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此附件"
        )

    # 删除物理文件
    file_path = Path(attachment.file_path.lstrip("/uploads/"))
    full_path = UPLOAD_DIR / file_path
    if full_path.exists():
        try:
            full_path.unlink()
        except Exception as e:
            print(f"删除文件失败：{e}")

    # 删除数据库记录
    db.delete(attachment)
    db.commit()

    return {"message": "附件已删除"}
