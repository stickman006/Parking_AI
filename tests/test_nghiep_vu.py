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


def test_ghi_nhan_xe_vao_cap_nhat_thong_tin_phuong_tien_da_co(seeded_db):
    db = seeded_db["db"]
    khu_vuc = seeded_db["khu_vuc"]
    loai_xe = seeded_db["loai_xe"]

    crud.ghi_nhan_xe_vao(db, schemas.XeVaoRequest(
        bien_so="29A-8899", loai_xe_id=loai_xe.id, khu_vuc_id=khu_vuc.id,
        hinh_thuc_gui=models.KhungGio.sang, chu_xe="Nguyen Van A", so_dien_thoai="0911111111",
    ))
    crud.ghi_nhan_xe_ra(db, schemas.XeRaRequest(bien_so="29A-8899"))

    loai_xe_2 = models.LoaiXe(ten_loai_xe="Xe điện")
    db.add(loai_xe_2)
    vi_tri_bat_ky = db.query(models.ViTriDo).filter(models.ViTriDo.khu_vuc_id == khu_vuc.id).first()
    db.commit()

    # Lần vào sau: đổi loại xe + chủ xe + SĐT -> thông tin phương tiện phải
    # được cập nhật lại (không giữ mãi dữ liệu cũ của lần đăng ký đầu).
    crud.ghi_nhan_xe_vao(db, schemas.XeVaoRequest(
        bien_so="29A-8899", loai_xe_id=loai_xe_2.id, khu_vuc_id=khu_vuc.id,
        vi_tri_id=vi_tri_bat_ky.id, hinh_thuc_gui=models.KhungGio.sang,
        chu_xe="Tran Thi B", so_dien_thoai="0922222222",
    ))

    pt = db.query(models.PhuongTien).filter(models.PhuongTien.bien_so == "29A-8899").first()
    assert pt.loai_xe_id == loai_xe_2.id
    assert pt.chu_xe == "Tran Thi B"
    assert pt.so_dien_thoai == "0922222222"


def test_ghi_nhan_xe_vao_khong_ghi_de_khi_khong_nhap_lai(seeded_db):
    db = seeded_db["db"]
    khu_vuc = seeded_db["khu_vuc"]
    loai_xe = seeded_db["loai_xe"]

    crud.ghi_nhan_xe_vao(db, schemas.XeVaoRequest(
        bien_so="29A-9900", loai_xe_id=loai_xe.id, khu_vuc_id=khu_vuc.id,
        hinh_thuc_gui=models.KhungGio.sang, chu_xe="Nguyen Van C", so_dien_thoai="0933333333",
    ))
    crud.ghi_nhan_xe_ra(db, schemas.XeRaRequest(bien_so="29A-9900"))

    # Lần vào sau: không nhập lại chủ xe/SĐT -> phải giữ nguyên dữ liệu cũ,
    # không bị xoá/ghi đè thành rỗng.
    crud.ghi_nhan_xe_vao(db, schemas.XeVaoRequest(
        bien_so="29A-9900", khu_vuc_id=khu_vuc.id, hinh_thuc_gui=models.KhungGio.sang,
    ))

    pt = db.query(models.PhuongTien).filter(models.PhuongTien.bien_so == "29A-9900").first()
    assert pt.loai_xe_id == loai_xe.id
    assert pt.chu_xe == "Nguyen Van C"
    assert pt.so_dien_thoai == "0933333333"


def test_xe_ra_mat_ve_thieu_thong_tin_chung_minh_bao_loi():
    with pytest.raises(Exception):
        schemas.XeRaRequest(bien_so="29A-1234", mat_ve=True)


def test_xe_ra_mat_ve_cong_them_phu_phi(seeded_db):
    db = seeded_db["db"]
    khu_vuc = seeded_db["khu_vuc"]
    loai_xe = seeded_db["loai_xe"]

    crud.ghi_nhan_xe_vao(db, schemas.XeVaoRequest(bien_so="29A-5555", loai_xe_id=loai_xe.id, khu_vuc_id=khu_vuc.id, hinh_thuc_gui=models.KhungGio.sang))
    ra_binh_thuong = crud.ghi_nhan_xe_ra(db, schemas.XeRaRequest(bien_so="29A-5555"))

    crud.ghi_nhan_xe_vao(db, schemas.XeVaoRequest(bien_so="29A-6666", loai_xe_id=loai_xe.id, khu_vuc_id=khu_vuc.id, hinh_thuc_gui=models.KhungGio.sang))
    ra_mat_ve = crud.ghi_nhan_xe_ra(db, schemas.XeRaRequest(
        bien_so="29A-6666", mat_ve=True, thong_tin_chung_minh="CCCD 001234567890",
    ))

    assert ra_mat_ve.mat_ve is True
    assert ra_mat_ve.phi_thu == ra_binh_thuong.phi_thu + 10000
