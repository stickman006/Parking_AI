from fastapi import HTTPException

import pytest

from app import models, schemas, security
from app.routers.auth import dang_ky
from app.main import _dam_bao_co_tai_khoan_quan_ly_mac_dinh


def test_dang_ky_can_quyen_quan_ly(seeded_db):
    db = seeded_db["db"]
    nhan_vien = models.NguoiDung(ho_ten="NV", tai_khoan="nv1", mat_khau_hash=security.hash_password("123456"),
                                  vai_tro=models.VaiTro.nhan_vien)
    db.add(nhan_vien)
    db.commit()

    with pytest.raises(HTTPException):
        dang_ky(schemas.NguoiDungCreate(ho_ten="X", tai_khoan="x1", mat_khau="123456", vai_tro=models.VaiTro.nhan_vien),
                db=db, _=security.require_quan_ly(nhan_vien))


def test_dang_ky_quan_ly_tao_duoc_tai_khoan(seeded_db):
    db = seeded_db["db"]
    quan_ly = models.NguoiDung(ho_ten="QL", tai_khoan="ql1", mat_khau_hash=security.hash_password("123456"),
                                vai_tro=models.VaiTro.quan_ly)
    db.add(quan_ly)
    db.commit()

    ket_qua = dang_ky(schemas.NguoiDungCreate(ho_ten="Nhan vien moi", tai_khoan="nv-moi", mat_khau="123456",
                                               vai_tro=models.VaiTro.nhan_vien),
                       db=db, _=security.require_quan_ly(quan_ly))
    assert ket_qua.tai_khoan == "nv-moi"


def test_khoi_dong_tu_tao_tai_khoan_quan_ly_mac_dinh(monkeypatch, tmp_path):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import app.database as dbmod
    import app.main as mainmod

    engine = create_engine(f"sqlite:///{tmp_path}/test.db")
    Session = sessionmaker(bind=engine)
    dbmod.Base.metadata.create_all(bind=engine)
    monkeypatch.setattr(mainmod, "SessionLocal", Session)
    monkeypatch.setattr(mainmod.models, "NguoiDung", models.NguoiDung)

    _dam_bao_co_tai_khoan_quan_ly_mac_dinh()

    db = Session()
    user = db.query(models.NguoiDung).filter(models.NguoiDung.tai_khoan == "quanly").first()
    assert user is not None
    assert user.vai_tro == models.VaiTro.quan_ly
    assert security.verify_password("123456", user.mat_khau_hash)

    # Gọi lần 2 không được tạo thêm tài khoản trùng
    _dam_bao_co_tai_khoan_quan_ly_mac_dinh()
    assert db.query(models.NguoiDung).count() == 1
    db.close()
