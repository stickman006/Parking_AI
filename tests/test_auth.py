from unittest.mock import patch, Mock

import pytest
from fastapi import HTTPException

from app import models, schemas, security
from app.routers.auth import dang_nhap_google


def _gia_lap_phan_hoi_google(payload: dict) -> Mock:
    resp = Mock()
    resp.status_code = 200
    resp.json.return_value = payload
    return resp


def test_dang_nhap_google_chua_cau_hinh_bao_loi(db_session, monkeypatch):
    monkeypatch.setattr(security, "GOOGLE_CLIENT_ID", "")
    with pytest.raises(HTTPException):
        dang_nhap_google(schemas.GoogleLoginRequest(id_token="bat-ky"), db=db_session)


def test_dang_nhap_google_tao_tai_khoan_moi_la_nhan_vien(db_session, monkeypatch):
    monkeypatch.setattr(security, "GOOGLE_CLIENT_ID", "test-client-id")
    payload = {"aud": "test-client-id", "sub": "google-sub-1", "email": "a@example.com",
               "email_verified": "true", "name": "Nguyen Van A"}
    with patch("app.security.requests.get", return_value=_gia_lap_phan_hoi_google(payload)):
        ket_qua = dang_nhap_google(schemas.GoogleLoginRequest(id_token="tok"), db=db_session)

    assert ket_qua.vai_tro == models.VaiTro.nhan_vien
    user = db_session.query(models.NguoiDung).filter(models.NguoiDung.google_sub == "google-sub-1").first()
    assert user is not None
    assert user.tai_khoan == "a@example.com"
    assert user.mat_khau_hash is None


def test_dang_nhap_google_lien_ket_tai_khoan_da_co_theo_email(db_session, monkeypatch):
    monkeypatch.setattr(security, "GOOGLE_CLIENT_ID", "test-client-id")
    # Quản lý đã tạo trước 1 tài khoản quan_ly với tai_khoan = email, chưa có google_sub
    co_san = models.NguoiDung(ho_ten="Sep truong", tai_khoan="boss@example.com",
                               mat_khau_hash=security.hash_password("123456"), vai_tro=models.VaiTro.quan_ly)
    db_session.add(co_san)
    db_session.commit()

    payload = {"aud": "test-client-id", "sub": "google-sub-2", "email": "boss@example.com",
               "email_verified": "true", "name": "Sep Truong"}
    with patch("app.security.requests.get", return_value=_gia_lap_phan_hoi_google(payload)):
        ket_qua = dang_nhap_google(schemas.GoogleLoginRequest(id_token="tok"), db=db_session)

    # Phải LIÊN KẾT vào tài khoản quan_ly có sẵn, không tạo tài khoản nhân viên mới
    assert ket_qua.vai_tro == models.VaiTro.quan_ly
    assert db_session.query(models.NguoiDung).filter(models.NguoiDung.tai_khoan == "boss@example.com").count() == 1


def test_dang_nhap_google_lan_sau_khop_theo_sub(db_session, monkeypatch):
    monkeypatch.setattr(security, "GOOGLE_CLIENT_ID", "test-client-id")
    payload = {"aud": "test-client-id", "sub": "google-sub-3", "email": "c@example.com",
               "email_verified": "true", "name": "Nguyen Van C"}
    with patch("app.security.requests.get", return_value=_gia_lap_phan_hoi_google(payload)):
        dang_nhap_google(schemas.GoogleLoginRequest(id_token="tok"), db=db_session)
        # đăng nhập lần 2 với cùng sub -> không tạo thêm tài khoản mới
        dang_nhap_google(schemas.GoogleLoginRequest(id_token="tok"), db=db_session)

    assert db_session.query(models.NguoiDung).filter(models.NguoiDung.google_sub == "google-sub-3").count() == 1


def test_dang_nhap_google_email_chua_xac_minh_bao_loi(db_session, monkeypatch):
    monkeypatch.setattr(security, "GOOGLE_CLIENT_ID", "test-client-id")
    payload = {"aud": "test-client-id", "sub": "google-sub-4", "email": "d@example.com",
               "email_verified": "false", "name": "D"}
    with patch("app.security.requests.get", return_value=_gia_lap_phan_hoi_google(payload)):
        with pytest.raises(HTTPException):
            dang_nhap_google(schemas.GoogleLoginRequest(id_token="tok"), db=db_session)
