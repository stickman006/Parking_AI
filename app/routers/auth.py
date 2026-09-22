from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas, security
from app.database import get_db

router = APIRouter(prefix="/api/auth", tags=["Đăng nhập / Phân quyền (QL-01)"])


@router.get("/config", response_model=schemas.AuthConfigOut)
def cau_hinh_dang_nhap():
    """Thông tin công khai để giao diện biết có nên hiện nút 'Đăng nhập
    bằng Google' hay không (client_id không phải bí mật)."""
    return schemas.AuthConfigOut(google_client_id=security.GOOGLE_CLIENT_ID)


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


@router.post("/google", response_model=schemas.TokenResponse)
def dang_nhap_google(du_lieu: schemas.GoogleLoginRequest, db: Session = Depends(get_db)):
    """Đăng nhập/tự tạo tài khoản bằng Google. Ưu tiên khớp theo google_sub
    (ổn định, không đổi); nếu chưa từng đăng nhập Google, thử khớp theo
    email với tài khoản đã có sẵn (VD: được Quản lý tạo trước với tai_khoan
    là email) để LIÊN KẾT thay vì tạo trùng; nếu vẫn không có, tự tạo tài
    khoản mới với vai trò mặc định Nhân viên."""
    thong_tin = security.xac_thuc_google_id_token(du_lieu.id_token)

    user = db.query(models.NguoiDung).filter(models.NguoiDung.google_sub == thong_tin["sub"]).first()
    if user is None and thong_tin["email"]:
        user = db.query(models.NguoiDung).filter(models.NguoiDung.tai_khoan == thong_tin["email"]).first()

    if user is None:
        user = models.NguoiDung(
            ho_ten=thong_tin["ten"],
            tai_khoan=thong_tin["email"],
            mat_khau_hash=None,
            vai_tro=models.VaiTro.nhan_vien,
            google_sub=thong_tin["sub"],
        )
        db.add(user)
    elif user.google_sub != thong_tin["sub"]:
        user.google_sub = thong_tin["sub"]  # liên kết tài khoản có sẵn với Google

    db.commit()
    db.refresh(user)

    token = security.create_token(user.id)
    return schemas.TokenResponse(access_token=token, vai_tro=user.vai_tro, ho_ten=user.ho_ten)


@router.get("/toi", response_model=schemas.NguoiDungOut)
def thong_tin_ca_nhan(user: models.NguoiDung = Depends(security.get_current_user)):
    return user
