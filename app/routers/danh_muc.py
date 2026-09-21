from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models, schemas, crud, security
from app.database import get_db

router = APIRouter(prefix="/api/danh-muc", tags=["Quản lý danh mục (QL-02)"])


# ----- Khu vực -----
@router.post("/khu-vuc", response_model=schemas.KhuVucOut)
def them_khu_vuc(du_lieu: schemas.KhuVucCreate, db: Session = Depends(get_db),
                  _: models.NguoiDung = Depends(security.require_quan_ly)):
    return crud.tao_khu_vuc(db, du_lieu)


@router.get("/khu-vuc", response_model=List[schemas.KhuVucOut])
def danh_sach_khu_vuc(db: Session = Depends(get_db)):
    return db.query(models.KhuVuc).all()


@router.put("/khu-vuc/{khu_vuc_id}", response_model=schemas.KhuVucOut)
def sua_khu_vuc(khu_vuc_id: int, du_lieu: schemas.KhuVucCreate, db: Session = Depends(get_db),
                 _: models.NguoiDung = Depends(security.require_quan_ly)):
    return crud.cap_nhat_khu_vuc(db, khu_vuc_id, du_lieu)


@router.delete("/khu-vuc/{khu_vuc_id}")
def xoa_khu_vuc(khu_vuc_id: int, db: Session = Depends(get_db),
                 _: models.NguoiDung = Depends(security.require_quan_ly)):
    crud.xoa_khu_vuc(db, khu_vuc_id)
    return {"thong_bao": "Đã xoá khu vực"}


# ----- Loại xe -----
@router.post("/loai-xe", response_model=schemas.LoaiXeOut)
def them_loai_xe(du_lieu: schemas.LoaiXeCreate, db: Session = Depends(get_db),
                  _: models.NguoiDung = Depends(security.require_quan_ly)):
    return crud.tao_loai_xe(db, du_lieu)


@router.get("/loai-xe", response_model=List[schemas.LoaiXeOut])
def danh_sach_loai_xe(db: Session = Depends(get_db)):
    return db.query(models.LoaiXe).all()


@router.put("/loai-xe/{loai_xe_id}", response_model=schemas.LoaiXeOut)
def sua_loai_xe(loai_xe_id: int, du_lieu: schemas.LoaiXeCreate, db: Session = Depends(get_db),
                 _: models.NguoiDung = Depends(security.require_quan_ly)):
    return crud.cap_nhat_loai_xe(db, loai_xe_id, du_lieu)


@router.delete("/loai-xe/{loai_xe_id}")
def xoa_loai_xe(loai_xe_id: int, db: Session = Depends(get_db),
                 _: models.NguoiDung = Depends(security.require_quan_ly)):
    crud.xoa_loai_xe(db, loai_xe_id)
    return {"thong_bao": "Đã xoá loại xe"}


# ----- Vị trí đỗ -----
@router.post("/vi-tri", response_model=schemas.ViTriDoOut)
def them_vi_tri(du_lieu: schemas.ViTriDoCreate, db: Session = Depends(get_db),
                 _: models.NguoiDung = Depends(security.require_quan_ly)):
    return crud.tao_vi_tri(db, du_lieu)


@router.post("/vi-tri/hang-loat", response_model=schemas.ViTriHangLoatOut)
def them_vi_tri_hang_loat(du_lieu: schemas.ViTriHangLoatCreate, db: Session = Depends(get_db),
                           _: models.NguoiDung = Depends(security.require_quan_ly)):
    """Tạo nhanh 10/50/100 vị trí theo chữ cái đầu (VD: A -> A1, A2, ..., An),
    tự động bỏ qua các mã đã tồn tại để không tạo trùng tên vị trí."""
    return crud.tao_vi_tri_hang_loat(db, du_lieu)


@router.get("/vi-tri", response_model=List[schemas.ViTriDoOut])
def danh_sach_vi_tri(khu_vuc_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(models.ViTriDo)
    if khu_vuc_id is not None:
        q = q.filter(models.ViTriDo.khu_vuc_id == khu_vuc_id)
    return q.all()


@router.put("/vi-tri/{vi_tri_id}", response_model=schemas.ViTriDoOut)
def sua_vi_tri(vi_tri_id: int, du_lieu: schemas.ViTriDoUpdate, db: Session = Depends(get_db),
                _: models.NguoiDung = Depends(security.require_quan_ly)):
    return crud.cap_nhat_vi_tri(db, vi_tri_id, du_lieu)


@router.delete("/vi-tri/{vi_tri_id}")
def xoa_vi_tri(vi_tri_id: int, db: Session = Depends(get_db),
                _: models.NguoiDung = Depends(security.require_quan_ly)):
    crud.xoa_vi_tri(db, vi_tri_id)
    return {"thong_bao": "Đã xoá vị trí"}


# ----- Bảng giá -----
@router.post("/bang-gia", response_model=schemas.BangGiaOut)
def them_bang_gia(du_lieu: schemas.BangGiaCreate, db: Session = Depends(get_db),
                   _: models.NguoiDung = Depends(security.require_quan_ly)):
    return crud.tao_bang_gia(db, du_lieu)


@router.get("/bang-gia", response_model=List[schemas.BangGiaOut])
def danh_sach_bang_gia(loai_xe_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(models.BangGia)
    if loai_xe_id is not None:
        q = q.filter(models.BangGia.loai_xe_id == loai_xe_id)
    return q.all()


@router.put("/bang-gia/{bang_gia_id}", response_model=schemas.BangGiaOut)
def sua_bang_gia(bang_gia_id: int, du_lieu: schemas.BangGiaCreate, db: Session = Depends(get_db),
                  _: models.NguoiDung = Depends(security.require_quan_ly)):
    return crud.cap_nhat_bang_gia(db, bang_gia_id, du_lieu)


@router.delete("/bang-gia/{bang_gia_id}")
def xoa_bang_gia(bang_gia_id: int, db: Session = Depends(get_db),
                  _: models.NguoiDung = Depends(security.require_quan_ly)):
    crud.xoa_bang_gia(db, bang_gia_id)
    return {"thong_bao": "Đã xoá bảng giá"}
