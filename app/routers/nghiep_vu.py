from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models, schemas, crud, security
from app.database import get_db

router = APIRouter(prefix="/api", tags=["Nghiệp vụ vào/ra, chỗ trống, tra cứu (QL-03..06)"])


# ----- QL-03 + QL-04: vào / ra + tính phí -----
@router.post("/xe-vao", response_model=schemas.LuotGuiXeOut)
def xe_vao(du_lieu: schemas.XeVaoRequest, db: Session = Depends(get_db),
           _: models.NguoiDung = Depends(security.get_current_user)):
    return crud.ghi_nhan_xe_vao(db, du_lieu)


@router.post("/xe-ra", response_model=schemas.LuotGuiXeOut)
def xe_ra(du_lieu: schemas.XeRaRequest, db: Session = Depends(get_db),
          _: models.NguoiDung = Depends(security.get_current_user)):
    return crud.ghi_nhan_xe_ra(db, du_lieu)


# ----- QL-05: chỗ trống -----
@router.get("/cho-trong")
def cho_trong(khu_vuc_id: Optional[int] = None, db: Session = Depends(get_db)):
    return crud.trang_thai_cho_trong(db, khu_vuc_id)


# ----- QL-06: tra cứu (kết hợp bất kỳ tiêu chí nào: biển số, tên, sđt, loại xe, khu vực, trạng thái, ngày) -----
@router.get("/tra-cuu", response_model=List[schemas.TraCuuKetQuaItem])
def tra_cuu(bien_so: Optional[str] = None, chu_xe: Optional[str] = None,
            so_dien_thoai: Optional[str] = None, loai_xe_id: Optional[int] = None,
            khu_vuc_id: Optional[int] = None, trang_thai: Optional[models.TrangThaiLuot] = None,
            tu_ngay: Optional[datetime] = None, den_ngay: Optional[datetime] = None,
            db: Session = Depends(get_db)):
    tham_so = schemas.TraCuuLuotXeParams(
        bien_so=bien_so, chu_xe=chu_xe, so_dien_thoai=so_dien_thoai, loai_xe_id=loai_xe_id,
        khu_vuc_id=khu_vuc_id, trang_thai=trang_thai, tu_ngay=tu_ngay, den_ngay=den_ngay,
    )
    return crud.tra_cuu_luot_xe(db, tham_so)


# ----- Danh sách phương tiện (hỗ trợ tra cứu/QL-02 phụ trợ) -----
@router.get("/phuong-tien", response_model=List[schemas.PhuongTienOut])
def danh_sach_phuong_tien(bien_so: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(models.PhuongTien)
    if bien_so:
        q = q.filter(models.PhuongTien.bien_so.ilike(f"%{bien_so}%"))
    return q.all()
