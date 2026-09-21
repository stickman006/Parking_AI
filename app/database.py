"""
Cấu hình kết nối cơ sở dữ liệu. Mặc định dùng SQLite cho phát triển/chấm
bài cục bộ; khi triển khai (Render/Supabase...), đặt biến môi trường
DATABASE_URL trỏ tới CSDL PostgreSQL của Supabase để dùng ngay mà không
cần sửa code (theo mục 1.2.3 của đề tài).
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./parking.db")

# Supabase (và một số nhà cung cấp Postgres khác) đôi khi cấp chuỗi kết nối
# bắt đầu bằng "postgres://" - SQLAlchemy hiện chỉ nhận "postgresql://".
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency FastAPI: mở phiên làm việc DB cho mỗi request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
