from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas, security
from app.database import get_db

router = APIRouter(prefix="/api/auth", tags=["Đăng nhập / Phân quyền (QL-01)"])


@router.post("/dang-ky", response_model=schemas.NguoiDungOut)
def dang_ky(du_lieu: schemas.NguoiDungCreate, db: Session = Depends(get_db)):
    ton_tai = db.query(models.NguoiDung).filter(models.NguoiDung.tai_khoan == du_lieu.tai_khoan).first()
    if ton_tai:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Tài khoản đã tồn tại")
    user = models.NguoiDung(
        ho_ten=du_lieu.ho_ten,
        tai_khoan=du_lieu.tai_khoan,
        mat_khau_hash=security.hash_password(du_lieu.mat_khau),
        vai_tro=du_lieu.vai_tro,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/dang-nhap", response_model=schemas.TokenResponse)
def dang_nhap(du_lieu: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.NguoiDung).filter(models.NguoiDung.tai_khoan == du_lieu.tai_khoan).first()
    if user is None or not security.verify_password(du_lieu.mat_khau, user.mat_khau_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sai tài khoản hoặc mật khẩu")
    token = security.create_token(user.id)
    return schemas.TokenResponse(access_token=token, vai_tro=user.vai_tro, ho_ten=user.ho_ten)


@router.get("/toi", response_model=schemas.NguoiDungOut)
def thong_tin_ca_nhan(user: models.NguoiDung = Depends(security.get_current_user)):
    return user
