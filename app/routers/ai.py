import json
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import ai_data, ai_engine, models, schemas, security
from app.database import get_db

router = APIRouter(prefix="/api/ai", tags=["Tích hợp AI (AI-01, AI-02, AI-03)"])


def _luu_lich_su(db: Session, loai: str, cau_hoi: str | None, du_lieu: dict, cau_tra_loi: str) -> models.LichSuHoiDapAI:
    ban_ghi = models.LichSuHoiDapAI(
        loai=loai,
        cau_hoi=cau_hoi,
        du_lieu_gui_kem=json.dumps(du_lieu, ensure_ascii=False),
        cau_tra_loi=cau_tra_loi,
    )
    db.add(ban_ghi)
    db.commit()
    db.refresh(ban_ghi)
    return ban_ghi


# ----- AI-01: Sinh báo cáo lưu lượng -----
@router.post("/bao-cao-luu-luong", response_model=schemas.AITraLoiOut)
def bao_cao_luu_luong(du_lieu: schemas.BaoCaoLuuLuongRequest, db: Session = Depends(get_db),
                       _: models.NguoiDung = Depends(security.get_current_user)):
    payload = ai_data.tong_hop_du_lieu_cho_ai(db, du_lieu.tu_ngay, du_lieu.den_ngay, du_lieu.khu_vuc_id)
    cau_tra_loi = ai_engine.sinh_bao_cao_luu_luong(payload)
    _luu_lich_su(db, "bao_cao", None, payload, cau_tra_loi)
    return schemas.AITraLoiOut(cau_tra_loi=cau_tra_loi, du_lieu_dung=payload)


# ----- AI-02: Hỏi đáp quản trị -----
@router.post("/hoi-dap", response_model=schemas.AITraLoiOut)
def hoi_dap(du_lieu: schemas.HoiDapRequest, db: Session = Depends(get_db),
            _: models.NguoiDung = Depends(security.get_current_user)):
    from datetime import datetime, timedelta
    tu_ngay = du_lieu.tu_ngay or (datetime.utcnow() - timedelta(days=7))
    den_ngay = du_lieu.den_ngay or datetime.utcnow()

    payload = ai_data.tong_hop_du_lieu_cho_ai(db, tu_ngay, den_ngay)
    cau_tra_loi = ai_engine.hoi_dap_quan_tri(du_lieu.cau_hoi, payload)
    _luu_lich_su(db, "hoi_dap", du_lieu.cau_hoi, payload, cau_tra_loi)
    return schemas.AITraLoiOut(cau_tra_loi=cau_tra_loi, du_lieu_dung=payload)


# ----- AI-03: Gợi ý bố trí nhân sự -----
@router.post("/goi-y-nhan-su", response_model=schemas.AITraLoiOut)
def goi_y_nhan_su(du_lieu: schemas.GoiYNhanSuRequest, db: Session = Depends(get_db),
                   _: models.NguoiDung = Depends(security.get_current_user)):
    payload = ai_data.tong_hop_du_lieu_cho_ai(db, du_lieu.tu_ngay, du_lieu.den_ngay)
    cau_tra_loi = ai_engine.goi_y_bo_tri_nhan_su(payload)
    _luu_lich_su(db, "goi_y_nhan_su", None, payload, cau_tra_loi)
    return schemas.AITraLoiOut(cau_tra_loi=cau_tra_loi, du_lieu_dung=payload)


# ----- Lịch sử hỏi đáp AI (phục vụ đối chiếu, kiểm thử - Bảng 2.4) -----
@router.get("/lich-su", response_model=List[schemas.LichSuHoiDapOut])
def lich_su(db: Session = Depends(get_db)):
    return db.query(models.LichSuHoiDapAI).order_by(models.LichSuHoiDapAI.thoi_gian.desc()).limit(100).all()
