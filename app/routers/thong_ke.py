from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import ai_data, security, models
from app.database import get_db

router = APIRouter(prefix="/api/thong-ke", tags=["Thống kê, báo cáo (QL-08)"])


@router.get("/luu-luong")
def luu_luong(tu_ngay: datetime, den_ngay: datetime, khu_vuc_id: Optional[int] = None,
              db: Session = Depends(get_db)):
    return ai_data.thong_ke_luu_luong(db, tu_ngay, den_ngay, khu_vuc_id)


@router.get("/doanh-thu")
def doanh_thu(tu_ngay: datetime, den_ngay: datetime, khu_vuc_id: Optional[int] = None,
              db: Session = Depends(get_db)):
    return ai_data.thong_ke_doanh_thu(db, tu_ngay, den_ngay, khu_vuc_id)


@router.get("/lap-day")
def lap_day(khu_vuc_id: Optional[int] = None, db: Session = Depends(get_db)):
    return ai_data.ty_le_lap_day(db, khu_vuc_id)
