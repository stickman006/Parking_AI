import pytest
from fastapi import HTTPException

from app import crud, schemas, models


def test_ghi_nhan_xe_vao_tu_dong_gan_vi_tri(seeded_db):
    db = seeded_db["db"]
    khu_vuc = seeded_db["khu_vuc"]
    loai_xe = seeded_db["loai_xe"]

    luot = crud.ghi_nhan_xe_vao(db, schemas.XeVaoRequest(
        bien_so="29A-9999", loai_xe_id=loai_xe.id, khu_vuc_id=khu_vuc.id,
        hinh_thuc_gui=models.KhungGio.sang,
    ))
    assert luot.trang_thai == models.TrangThaiLuot.dang_gui
    assert luot.hinh_thuc_gui == models.KhungGio.sang

    vi_tri = db.get(models.ViTriDo, luot.vi_tri_id)
    assert vi_tri.trang_thai == models.TrangThaiViTri.da_do


def test_khong_the_vao_2_lan_khi_chua_ra(seeded_db):
    db = seeded_db["db"]
    khu_vuc = seeded_db["khu_vuc"]
    loai_xe = seeded_db["loai_xe"]

    crud.ghi_nhan_xe_vao(db, schemas.XeVaoRequest(bien_so="29A-1111", loai_xe_id=loai_xe.id, khu_vuc_id=khu_vuc.id, hinh_thuc_gui=models.KhungGio.sang))
    with pytest.raises(HTTPException):
        crud.ghi_nhan_xe_vao(db, schemas.XeVaoRequest(bien_so="29A-1111", loai_xe_id=loai_xe.id, khu_vuc_id=khu_vuc.id, hinh_thuc_gui=models.KhungGio.sang))


def test_het_cho_trong_bao_loi(seeded_db):
    db = seeded_db["db"]
    khu_vuc = seeded_db["khu_vuc"]
    loai_xe = seeded_db["loai_xe"]

    crud.ghi_nhan_xe_vao(db, schemas.XeVaoRequest(bien_so="29A-1001", loai_xe_id=loai_xe.id, khu_vuc_id=khu_vuc.id, hinh_thuc_gui=models.KhungGio.sang))
    crud.ghi_nhan_xe_vao(db, schemas.XeVaoRequest(bien_so="29A-1002", loai_xe_id=loai_xe.id, khu_vuc_id=khu_vuc.id, hinh_thuc_gui=models.KhungGio.sang))
    with pytest.raises(HTTPException):
        crud.ghi_nhan_xe_vao(db, schemas.XeVaoRequest(bien_so="29A-1003", loai_xe_id=loai_xe.id, khu_vuc_id=khu_vuc.id, hinh_thuc_gui=models.KhungGio.sang))


def test_ghi_nhan_xe_ra_tra_phong_vi_tri(seeded_db):
    db = seeded_db["db"]
    khu_vuc = seeded_db["khu_vuc"]
    loai_xe = seeded_db["loai_xe"]

    luot = crud.ghi_nhan_xe_vao(db, schemas.XeVaoRequest(bien_so="29A-2222", loai_xe_id=loai_xe.id, khu_vuc_id=khu_vuc.id, hinh_thuc_gui=models.KhungGio.sang))
    ra = crud.ghi_nhan_xe_ra(db, schemas.XeRaRequest(bien_so="29A-2222"))

    assert ra.trang_thai == models.TrangThaiLuot.hoan_tat
    assert ra.phi_thu is not None and ra.phi_thu >= 0

    vi_tri = db.get(models.ViTriDo, luot.vi_tri_id)
    assert vi_tri.trang_thai == models.TrangThaiViTri.trong


def test_xe_ra_co_the_doi_lai_hinh_thuc_gui(seeded_db):
    db = seeded_db["db"]
    khu_vuc = seeded_db["khu_vuc"]
    loai_xe = seeded_db["loai_xe"]

    crud.ghi_nhan_xe_vao(db, schemas.XeVaoRequest(bien_so="29A-3333", loai_xe_id=loai_xe.id, khu_vuc_id=khu_vuc.id, hinh_thuc_gui=models.KhungGio.sang))
    ra = crud.ghi_nhan_xe_ra(db, schemas.XeRaRequest(bien_so="29A-3333", hinh_thuc_gui=models.KhungGio.toi))
    assert ra.hinh_thuc_gui == models.KhungGio.toi


def test_xe_ra_khong_ton_tai_bao_loi(seeded_db):
    db = seeded_db["db"]
    with pytest.raises(HTTPException):
        crud.ghi_nhan_xe_ra(db, schemas.XeRaRequest(bien_so="29A-0000"))


def test_trang_thai_cho_trong(seeded_db):
    db = seeded_db["db"]
    khu_vuc = seeded_db["khu_vuc"]
    loai_xe = seeded_db["loai_xe"]

    crud.ghi_nhan_xe_vao(db, schemas.XeVaoRequest(bien_so="29A-4444", loai_xe_id=loai_xe.id, khu_vuc_id=khu_vuc.id, hinh_thuc_gui=models.KhungGio.sang))
    ket_qua = crud.trang_thai_cho_trong(db, khu_vuc.id)
    assert ket_qua[0]["so_cho_trong"] == 1
    assert ket_qua[0]["so_da_do"] == 1


def test_bien_so_khong_du_4_so_bao_loi():
    with pytest.raises(Exception):
        schemas.XeVaoRequest(bien_so="29A-12", loai_xe_id=1, khu_vuc_id=1, hinh_thuc_gui=models.KhungGio.sang)


def test_so_dien_thoai_khong_hop_le_bao_loi():
    with pytest.raises(Exception):
        schemas.XeVaoRequest(bien_so="29A-1234", loai_xe_id=1, khu_vuc_id=1,
                              hinh_thuc_gui=models.KhungGio.sang, so_dien_thoai="123456")


def test_so_dien_thoai_khong_bat_dau_bang_0_bao_loi():
    with pytest.raises(Exception):
        schemas.XeVaoRequest(bien_so="29A-1234", loai_xe_id=1, khu_vuc_id=1,
                              hinh_thuc_gui=models.KhungGio.sang, so_dien_thoai="1912345678")
