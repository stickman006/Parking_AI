import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app import models


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def seeded_db(db_session):
    """DB tối thiểu: 1 khu vực, 2 vị trí, 1 loại xe, bảng giá đầy đủ 6 hình thức gửi xe."""
    db = db_session
    loai_xe = models.LoaiXe(ten_loai_xe="Xe máy")
    db.add(loai_xe)
    db.flush()

    khu_vuc = models.KhuVuc(ten_khu_vuc="Khu A", tong_so_vi_tri=0)
    db.add(khu_vuc)
    db.flush()

    for ma in ["A-01", "A-02"]:
        db.add(models.ViTriDo(khu_vuc_id=khu_vuc.id, ma_vi_tri=ma, loai_xe_cho_phep=loai_xe.id))
        khu_vuc.tong_so_vi_tri += 1

    for khung, gia in [
        (models.KhungGio.sang, 3000), (models.KhungGio.chieu, 3000),
        (models.KhungGio.toi, 4000), (models.KhungGio.qua_dem, 5000),
        (models.KhungGio.thang, 150000), (models.KhungGio.qua_dem_thang, 200000),
    ]:
        db.add(models.BangGia(loai_xe_id=loai_xe.id, khung_gio=khung, don_gia=gia))

    db.commit()
    return {"db": db, "khu_vuc": khu_vuc, "loai_xe": loai_xe}
