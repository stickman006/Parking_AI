"""
QL-01: Đăng nhập, phân quyền.
Đồ án mức Cơ bản -> dùng token ngẫu nhiên lưu trong bộ nhớ (đủ để demo
phân quyền Quản lý / Nhân viên) thay vì triển khai đầy đủ OAuth2/JWT.
Ngoài đăng nhập tài khoản/mật khẩu, hỗ trợ thêm đăng nhập bằng Google
(xem xac_thuc_google_id_token bên dưới).
"""
import os
import secrets
from typing import Optional

import requests
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.database import get_db
from app import models

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)

# token -> nguoi_dung_id (bộ nhớ trong tiến trình; đủ dùng cho đồ án demo)
_ACTIVE_TOKENS: dict[str, int] = {}

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
_GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"


def hash_password(mat_khau: str) -> str:
    return pwd_context.hash(mat_khau)


def verify_password(mat_khau: str, mat_khau_hash: Optional[str]) -> bool:
    if not mat_khau_hash:
        return False  # tài khoản chỉ đăng nhập bằng Google, không có mật khẩu
    return pwd_context.verify(mat_khau, mat_khau_hash)


def create_token(nguoi_dung_id: int) -> str:
    token = secrets.token_hex(24)
    _ACTIVE_TOKENS[token] = nguoi_dung_id
    return token


def xac_thuc_google_id_token(id_token: str) -> dict:
    """Xác thực ID token do Google Identity Services (phía trình duyệt) trả
    về, dùng endpoint tokeninfo chính thức của Google (đơn giản, không cần
    thêm thư viện ngoài) - trả về {sub, email, ten} nếu hợp lệ, raise
    HTTPException nếu token giả/hết hạn/không đúng ứng dụng."""
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Server chưa cấu hình đăng nhập Google (thiếu GOOGLE_CLIENT_ID)")
    try:
        resp = requests.get(_GOOGLE_TOKENINFO_URL, params={"id_token": id_token}, timeout=10)
    except requests.RequestException:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Không thể xác thực với Google lúc này, vui lòng thử lại")

    if resp.status_code != 200:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token Google không hợp lệ hoặc đã hết hạn")

    payload = resp.json()
    if payload.get("aud") != GOOGLE_CLIENT_ID:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token Google không thuộc ứng dụng này")
    if payload.get("email_verified") not in ("true", True):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email Google chưa được xác minh")

    return {
        "sub": payload.get("sub"),
        "email": payload.get("email"),
        "ten": payload.get("name") or payload.get("email"),
    }


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> models.NguoiDung:
    if credentials is None or credentials.credentials not in _ACTIVE_TOKENS:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Chưa đăng nhập hoặc token không hợp lệ")
    user_id = _ACTIVE_TOKENS[credentials.credentials]
    user = db.get(models.NguoiDung, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Người dùng không tồn tại")
    return user


def require_quan_ly(user: models.NguoiDung = Depends(get_current_user)) -> models.NguoiDung:
    if user.vai_tro != models.VaiTro.quan_ly:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chỉ Quản lý mới có quyền thực hiện thao tác này")
    return user
