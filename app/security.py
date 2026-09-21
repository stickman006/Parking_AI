"""
QL-01: Đăng nhập, phân quyền.
Đồ án mức Cơ bản -> dùng token ngẫu nhiên lưu trong bộ nhớ (đủ để demo
phân quyền Quản lý / Nhân viên) thay vì triển khai đầy đủ OAuth2/JWT.
"""
import secrets
from typing import Optional

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


def hash_password(mat_khau: str) -> str:
    return pwd_context.hash(mat_khau)


def verify_password(mat_khau: str, mat_khau_hash: str) -> bool:
    return pwd_context.verify(mat_khau, mat_khau_hash)


def create_token(nguoi_dung_id: int) -> str:
    token = secrets.token_hex(24)
    _ACTIVE_TOKENS[token] = nguoi_dung_id
    return token


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
