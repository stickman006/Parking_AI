from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app import ai_data, excel_report, security, models
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


@router.get("/xuat-excel")
def xuat_excel(tu_ngay: datetime, den_ngay: datetime, khu_vuc_id: Optional[int] = None,
                db: Session = Depends(get_db), _: models.NguoiDung = Depends(security.require_quan_ly)):
    """Xuất báo cáo lưu lượng/doanh thu/chi tiết lượt gửi xe ra file Excel
    (.xlsx), dùng đúng số liệu đã hiển thị ở màn hình Thống kê."""
    buffer = excel_report.tao_bao_cao_excel(db, tu_ngay, den_ngay, khu_vuc_id)
    ten_file = f"bao-cao-bai-do-xe_{tu_ngay:%Y%m%d}_{den_ngay:%Y%m%d}.xlsx"
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{ten_file}"'},
    )
