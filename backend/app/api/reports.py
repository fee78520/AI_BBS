from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.database import get_db
from app.models import Report, User, Notification, Post, Comment
from app.schemas import ReportCreate, ReportResponse, PaginatedResponse, UserResponse, HandleAction
from app.auth import get_current_active_user, require_auth, require_moderator

router = APIRouter()

@router.post("/", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
@require_auth
async def create_report(
    report: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建举报"""
    # 至少需要提供帖子或评论ID
    if not report.post_id and not report.comment_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="必须提供帖子ID或评论ID"
        )

    # 检查是否已经举报过
    existing = db.query(Report).filter(
        Report.reporter_id == current_user.id,
        Report.post_id == report.post_id,
        Report.comment_id == report.comment_id,
        Report.status == "pending"
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已经举报过该内容，请勿重复举报"
        )

    # 创建举报
    db_report = Report(
        reporter_id=current_user.id,
        **report.model_dump()
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)

    # 加载关联数据
    reporter = db.query(User).filter(User.id == db_report.reporter_id).first()

    # 发送通知给管理员
    from app.schemas import NotificationType
    content_type = "帖子" if report.post_id else "评论"
    notification = Notification(
        user_id=current_user.id,  # 通知举报人
        notification_type=NotificationType.REPORT,
        title=f"您的举报已提交",
        content=f"您对{content_type}的举报已提交，我们会尽快处理。举报原因：{report.reason}",
        related_id=db_report.id
    )
    db.add(notification)
    db.commit()

    return {
        **ReportResponse.model_validate(db_report).model_dump(),
        "reporter": UserResponse.model_validate(reporter).model_dump() if reporter else None,
        "handler": None
    }

@router.get("/", response_model=PaginatedResponse)
@require_moderator
async def get_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取举报列表（管理员/版主）"""
    from sqlalchemy import desc

    query = db.query(Report)

    if status:
        query = query.filter(Report.status == status)

    query = query.order_by(desc(Report.created_at))

    total = query.count()
    reports = query.offset((page - 1) * page_size).limit(page_size).all()

    # 加载关联数据
    items = []
    for report in reports:
        reporter = db.query(User).filter(User.id == report.reporter_id).first()
        handler = db.query(User).filter(User.id == report.handler_id).first() if report.handler_id else None
        items.append({
            **ReportResponse.model_validate(report).model_dump(),
            "reporter": UserResponse.model_validate(reporter).model_dump() if reporter else None,
            "handler": UserResponse.model_validate(handler).model_dump() if handler else None
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

@router.get("/{report_id}", response_model=ReportResponse)
@require_moderator
async def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取举报详情"""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="举报不存在"
        )

    # 加载关联数据
    reporter = db.query(User).filter(User.id == report.reporter_id).first()
    handler = db.query(User).filter(User.id == report.handler_id).first() if report.handler_id else None

    return {
        **ReportResponse.model_validate(report).model_dump(),
        "reporter": UserResponse.model_validate(reporter).model_dump() if reporter else None,
        "handler": UserResponse.model_validate(handler).model_dump() if handler else None
    }

@router.put("/{report_id}/handle")
@require_moderator
async def handle_report(
    report_id: int,
    action: HandleAction = Body(...),
    handler_note: str = Body(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """处理举报 - 支持：隐藏内容/删除内容/驳回举报/忽略举报"""
    from app.schemas import NotificationType

    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="举报不存在"
        )

    # 执行相应的操作
    content_type = "帖子" if report.post_id else "评论"
    action_text = ""

    if action == HandleAction.HIDE:
        # 隐藏内容
        report.status = "approved"
        action_text = "隐藏"
        if report.post_id:
            post = db.query(Post).filter(Post.id == report.post_id).first()
            if post:
                post.is_hidden = True
        elif report.comment_id:
            comment = db.query(Comment).filter(Comment.id == report.comment_id).first()
            if comment:
                comment.is_hidden = True

    elif action == HandleAction.DELETE:
        # 删除内容（软删除）
        report.status = "approved"
        action_text = "删除"
        if report.post_id:
            post = db.query(Post).filter(Post.id == report.post_id).first()
            if post:
                post.is_deleted = True
                post.status = "deleted"
        elif report.comment_id:
            comment = db.query(Comment).filter(Comment.id == report.comment_id).first()
            if comment:
                comment.is_deleted = True

    elif action == HandleAction.REJECT:
        # 驳回举报
        report.status = "rejected"
        action_text = "驳回"

    elif action == HandleAction.IGNORE:
        # 忽略举报
        report.status = "ignored"
        action_text = "忽略"

    report.handler_id = current_user.id
    report.handler_note = handler_note
    report.handled_at = datetime.utcnow()

    # 发送通知给举报人
    notification = Notification(
        user_id=report.reporter_id,
        notification_type=NotificationType.REPORT,
        title=f"您的举报已处理",
        content=f"您对{content_type}的举报已{action_text}。处理备注：{handler_note or '无'}",
        related_id=report.id
    )
    db.add(notification)

    db.commit()

    return {"message": f"举报已处理，操作：{action_text}"}
