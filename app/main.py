from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.routers import auth, danh_muc, nghiep_vu, thong_ke, ai

Base.metadata.create_all(bind=engine)

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
