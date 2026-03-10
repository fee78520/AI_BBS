"""
重置数据库脚本 - 删除所有数据并重新初始化
执行方法: python -m scripts.reset_database
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, init_db

def reset_database():
    """重置数据库"""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'bbs.db')

    if os.path.exists(db_path):
        print(f"正在删除数据库文件: {db_path}")
        try:
            os.remove(db_path)
            print("数据库文件已删除")
        except Exception as e:
            print(f"删除数据库文件失败: {e}")
            print("请手动删除 bbs.db 文件后重试")
            return False

    print("\n正在初始化数据库...")
    try:
        init_db()
        print("\n✅ 数据库重置成功！")
        print("\n默认管理员账号:")
        print("  用户名: admin")
        print("  密码: ")
        print("\n⚠️  请登录后立即修改默认密码！")
        return True
    except Exception as e:
        print(f"\n❌ 初始化数据库失败: {e}")
        return False

if __name__ == "__main__":
    reset_database()
