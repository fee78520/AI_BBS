"""
清理数据库中的无效通知类型
执行方法: python scripts/fix_notifications.py
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, SessionLocal
from app.models import Notification
from app.schemas import NotificationType

def fix_invalid_notifications():
    """清理无效的通知类型"""
    db = SessionLocal()
    try:
        # 获取所有有效的通知类型值
        valid_types = [t.value for t in NotificationType]
        print(f"有效的通知类型: {valid_types}")

        # 查询所有通知
        all_notifications = db.query(Notification).all()
        print(f"\n总通知数: {len(all_notifications)}")

        # 查找无效的通知
        invalid_notifications = [
            n for n in all_notifications
            if n.notification_type not in valid_types
        ]

        print(f"无效通知数: {len(invalid_notifications)}")

        if invalid_notifications:
            print("\n无效通知列表:")
            for n in invalid_notifications:
                print(f"  ID: {n.id}, Type: {n.notification_type}, Title: {n.title}")

            # 删除无效通知
            for n in invalid_notifications:
                db.delete(n)

            db.commit()
            print(f"\n已删除 {len(invalid_notifications)} 条无效通知")
        else:
            print("\n没有发现无效通知")

        # 统计各类型通知数量
        print("\n各类型通知统计:")
        for t in NotificationType:
            count = db.query(Notification).filter(
                Notification.notification_type == t.value
            ).count()
            print(f"  {t.name} ({t.value}): {count}")

    except Exception as e:
        print(f"\n错误: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_invalid_notifications()
