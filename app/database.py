# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

# 使用 SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./interviewpilot.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """FastAPI 依赖注入使用的生成器"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# init_db.py
def init_db():
    print("正在初始化数据库...")
    Base.metadata.create_all(bind=engine)
    print("数据库表结构创建完成。")

if __name__ == "__main__":
    init_db()