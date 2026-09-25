import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine, SessionLocal
from app import models, security
from app.routers import auth, danh_muc, nghiep_vu, thong_ke, ai

Base.metadata.create_all(bind=engine)


def _dam_bao_co_tai_khoan_quan_ly_mac_dinh() -> None:
    """Đăng nhập chỉ có thể tạo tài khoản khi ĐÃ đăng nhập bằng quyền Quản
    lý (xem routers/auth.py) - nên hệ thống cần sẵn ÍT NHẤT 1 tài khoản
    Quản lý ngay từ đầu để có thể đăng nhập lần đầu tiên. Nếu CSDL chưa có
    người dùng nào, tự tạo 1 tài khoản Quản lý mặc định (có thể đổi qua
    biến môi trường ADMIN_USERNAME/ADMIN_PASSWORD, hoặc đổi mật khẩu trong
    hệ thống sau khi đăng nhập)."""
    db = SessionLocal()
    try:
        if db.query(models.NguoiDung).first() is not None:
            return
        tai_khoan = os.getenv("ADMIN_USERNAME", "quanly")
        mat_khau = os.getenv("ADMIN_PASSWORD", "123456")
        db.add(models.NguoiDung(
            ho_ten="Quản trị hệ thống",
            tai_khoan=tai_khoan,
            mat_khau_hash=security.hash_password(mat_khau),
            vai_tro=models.VaiTro.quan_ly,
        ))
        db.commit()
        print(f"[parking-ai] Đã tạo tài khoản Quản lý mặc định: {tai_khoan} / {mat_khau} "
              f"(nên đổi mật khẩu sau khi đăng nhập lần đầu).")
    finally:
        db.close()


_dam_bao_co_tai_khoan_quan_ly_mac_dinh()

app = FastAPI(
    title="Hệ thống quản lý bãi đỗ xe có tích hợp AI",
    description="Đề tài: Hệ thống quản lý bãi đỗ xe có tích hợp AI (Nhóm 04)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(danh_muc.router)
app.include_router(nghiep_vu.router)
app.include_router(thong_ke.router)
app.include_router(ai.router)

app.mount("/", StaticFiles(directory="static", html=True), name="static")
