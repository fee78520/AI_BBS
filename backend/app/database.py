"""
BBS论坛系统 - 数据库配置
本文件负责：
1. 配置数据库连接
2. 创建数据库会话工厂
3. 提供数据库会话依赖
4. 初始化数据库（创建所有表）
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# ========== 数据库连接配置 ==========
# 从环境变量获取数据库URL，默认使用SQLite
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./bbs.db"  # 默认使用SQLite数据库文件
)

# 创建数据库引擎
# SQLite需要check_same_thread=False以允许多线程访问
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# 创建数据库会话工厂
# autocommit=False: 禁用自动提交
# autoflush=False: 禁用自动刷新
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建声明式基类（已废弃，仅用于兼容）
# 实际使用的Base来自app.models
Base = declarative_base()

# ========== 数据库会话依赖 ==========
def get_db():
    """
    获取数据库会话的依赖函数
    用于FastAPI的依赖注入，确保每个请求使用独立的数据库会话

    用法示例：
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()  # 创建新的数据库会话
    try:
        yield db  # 将会话传递给路由处理函数
    finally:
        db.close()  # 确保会话被正确关闭

# ========== 数据库初始化 ==========
def init_db():
    """
    初始化数据库
    创建所有定义的数据表，并创建默认超级管理员和默认板块

    该函数在应用启动时调用（main.py中的startup_event）
    """
    from app.models import Base, User, Category  # 导入模型
    from app.schemas import UserRole  # 导入枚举
    from app.auth import get_password_hash  # 导入密码哈希函数
    
    # 根据所有模型类创建对应的数据库表
    # 如果表已存在则跳过（不会删除现有数据）
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # ========== 创建默认超级管理员 ==========
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            # 从环境变量获取管理员密码
            admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
            admin_user = User(
                username="admin",
                email="admin@bbs.com",
                password_hash=get_password_hash(admin_password),
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True
            )
            db.add(admin_user)
            db.commit()
            print("默认超级管理员已创建: admin")
            print("【重要】请登录后立即修改默认密码！")
        
        # ========== 创建默认板块 ==========
        default_category = db.query(Category).filter(Category.name == "综合讨论").first()
        if not default_category:
            default_category = Category(
                name="综合讨论",
                description="综合讨论区，欢迎发表各类话题",
                sort_order=1
            )
            db.add(default_category)
            db.commit()
            print("默认板块已创建: 综合讨论")
            
    except Exception as e:
        print(f"初始化默认数据失败: {e}")
        db.rollback()
    finally:
        db.close()
