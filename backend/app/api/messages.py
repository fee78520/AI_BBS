from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_
from typing import List
from app.database import get_db
from app.models import Message, User
from app.schemas import MessageCreate, MessageResponse, PaginatedResponse, UserResponse, ConversationResponse
from app.auth import get_current_active_user

router = APIRouter()


@router.get("/unread-count")
async def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取私信未读总数"""
    count = db.query(Message).filter(
        Message.receiver_id == current_user.id,
        Message.is_read == False
    ).count()
    
    return {"count": count}


@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取对话列表 - 按用户分组显示最近一条消息
    
    返回每个对话的：
    - 对方用户信息
    - 最新一条消息
    - 未读消息数量
    """
    # 获取所有与我相关的消息（发送或接收）
    messages = db.query(Message).filter(
        or_(
            Message.sender_id == current_user.id,
            Message.receiver_id == current_user.id
        )
    ).order_by(desc(Message.created_at)).all()
    
    # 按对话用户分组
    conversations = {}  # key: 对方用户ID, value: ConversationResponse
    
    for msg in messages:
        # 确定对话对方
        other_user_id = msg.receiver_id if msg.sender_id == current_user.id else msg.sender_id
        
        if other_user_id not in conversations:
            # 获取对方用户信息
            other_user = db.query(User).filter(User.id == other_user_id).first()
            
            # 统计未读数（对方发给我的未读消息）
            unread_count = db.query(Message).filter(
                Message.sender_id == other_user_id,
                Message.receiver_id == current_user.id,
                Message.is_read == False
            ).count()
            
            conversations[other_user_id] = {
                "user_id": other_user_id,
                "user": UserResponse.model_validate(other_user) if other_user else None,
                "last_message": {
                    **MessageResponse.model_validate(msg).model_dump(),
                    "sender": None,
                    "receiver": None
                },
                "unread_count": unread_count,
                "updated_at": msg.created_at
            }
    
    # 按最新消息时间排序
    result = list(conversations.values())
    result.sort(key=lambda x: x["updated_at"], reverse=True)
    
    return result


@router.get("/conversations/{user_id}", response_model=PaginatedResponse)
async def get_conversation_messages(
    user_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取与某用户的对话详情（消息历史）
    
    同时自动将对方发来的消息标记为已读
    """
    # 检查对方用户是否存在
    other_user = db.query(User).filter(User.id == user_id).first()
    if not other_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 获取双方的所有消息
    query = db.query(Message).filter(
        or_(
            and_(Message.sender_id == current_user.id, Message.receiver_id == user_id),
            and_(Message.sender_id == user_id, Message.receiver_id == current_user.id)
        )
    ).order_by(desc(Message.created_at))
    
    total = query.count()
    messages = query.offset((page - 1) * page_size).limit(page_size).all()
    
    # 自动标记已读（对方发给我的消息）
    db.query(Message).filter(
        Message.sender_id == user_id,
        Message.receiver_id == current_user.id,
        Message.is_read == False
    ).update({"is_read": True})
    db.commit()
    
    # 构建响应
    items = []
    for msg in messages:
        items.append({
            **MessageResponse.model_validate(msg).model_dump(),
            "sender": UserResponse.model_validate(msg.sender) if msg.sender else None,
            "receiver": UserResponse.model_validate(msg.receiver) if msg.receiver else None
        })
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.put("/conversations/{user_id}/read")
async def mark_conversation_as_read(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """标记与某用户的对话为已读"""
    # 标记所有对方发来的未读消息
    count = db.query(Message).filter(
        Message.sender_id == user_id,
        Message.receiver_id == current_user.id,
        Message.is_read == False
    ).update({"is_read": True})
    
    db.commit()
    
    return {"message": f"已将 {count} 条消息标记为已读"}


@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    message: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """发送私信"""
    # 不能发给自己
    if message.receiver_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能给自己发送私信"
        )

    # 检查接收者是否存在
    receiver = db.query(User).filter(User.id == message.receiver_id).first()
    if not receiver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="接收者不存在"
        )

    # 验证至少有内容或图片
    if not message.content and not message.images:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="消息内容或图片不能为空"
        )

    # 创建私信
    db_message = Message(
        sender_id=current_user.id,
        receiver_id=message.receiver_id,
        content=message.content,
        images=message.images
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)

    # 加载关联数据
    sender = db.query(User).filter(User.id == db_message.sender_id).first()
    receiver = db.query(User).filter(User.id == db_message.receiver_id).first()

    return {
        **MessageResponse.model_validate(db_message).model_dump(),
        "sender": UserResponse.model_validate(sender).model_dump() if sender else None,
        "receiver": UserResponse.model_validate(receiver).model_dump() if receiver else None
    }

@router.get("/inbox", response_model=PaginatedResponse)
async def get_inbox(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取收件箱"""
    from sqlalchemy import desc

    query = db.query(Message).filter(
        Message.receiver_id == current_user.id
    )

    if unread_only:
        query = query.filter(Message.is_read == False)

    query = query.order_by(desc(Message.created_at))

    total = query.count()
    messages = query.offset((page - 1) * page_size).limit(page_size).all()

    # 加载关联数据
    items = []
    for message in messages:
        sender = db.query(User).filter(User.id == message.sender_id).first()
        items.append({
            **MessageResponse.model_validate(message).model_dump(),
            "sender": UserResponse.model_validate(sender).model_dump() if sender else None,
            "receiver": None
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

@router.get("/sent", response_model=PaginatedResponse)
async def get_sent_messages(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取已发送消息"""
    from sqlalchemy import desc

    query = db.query(Message).filter(
        Message.sender_id == current_user.id
    ).order_by(desc(Message.created_at))

    total = query.count()
    messages = query.offset((page - 1) * page_size).limit(page_size).all()

    # 加载关联数据
    items = []
    for message in messages:
        receiver = db.query(User).filter(User.id == message.receiver_id).first()
        items.append({
            **MessageResponse.model_validate(message).model_dump(),
            "sender": None,
            "receiver": UserResponse.model_validate(receiver).model_dump() if receiver else None
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

@router.get("/{message_id}", response_model=MessageResponse)
async def get_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取消息详情"""
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="消息不存在"
        )

    # 检查权限
    if message.sender_id != current_user.id and message.receiver_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权查看此消息"
        )

    # 标记为已读（如果是接收者）
    if message.receiver_id == current_user.id:
        message.is_read = True
        db.commit()

    # 加载关联数据
    sender = db.query(User).filter(User.id == message.sender_id).first()
    receiver = db.query(User).filter(User.id == message.receiver_id).first()

    return {
        **MessageResponse.model_validate(message).model_dump(),
        "sender": UserResponse.model_validate(sender).model_dump() if sender else None,
        "receiver": UserResponse.model_validate(receiver).model_dump() if receiver else None
    }

@router.put("/{message_id}/read")
async def mark_as_read(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """标记消息为已读"""
    message = db.query(Message).filter(
        Message.id == message_id,
        Message.receiver_id == current_user.id
    ).first()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="消息不存在"
        )

    message.is_read = True
    db.commit()

    return {"message": "已标记为已读"}

@router.post("/read-all")
async def mark_all_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """标记所有消息为已读"""
    messages = db.query(Message).filter(
        Message.receiver_id == current_user.id,
        Message.is_read == False
    ).all()

    count = len(messages)
    for message in messages:
        message.is_read = True

    db.commit()

    return {"message": f"已将 {count} 条消息标记为已读"}

@router.delete("/{message_id}")
async def delete_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除消息"""
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="消息不存在"
        )

    # 检查权限
    if message.sender_id != current_user.id and message.receiver_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此消息"
        )

    db.delete(message)
    db.commit()

    return {"message": "消息已删除"}
