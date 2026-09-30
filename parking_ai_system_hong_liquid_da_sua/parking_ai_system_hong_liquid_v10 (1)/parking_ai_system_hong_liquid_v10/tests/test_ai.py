from datetime import datetime, timedelta

from app import crud, schemas, ai_data, ai_engine, models


def test_bao_cao_du_lieu_rong_khong_bia_so_lieu(seeded_db):
    db = seeded_db["db"]
    payload = ai_data.tong_hop_du_lieu_cho_ai(db, datetime(2020, 1, 1), datetime(2020, 1, 2))
    assert ai_data.du_lieu_rong(payload) is True

    bao_cao = ai_engine.sinh_bao_cao_luu_luong(payload)
    assert "Không đủ dữ liệu" in bao_cao


def test_hoi_dap_du_lieu_rong(seeded_db):
    db = seeded_db["db"]
    payload = ai_data.tong_hop_du_lieu_cho_ai(db, datetime(2020, 1, 1), datetime(2020, 1, 2))
    tra_loi = ai_engine.hoi_dap_quan_tri("thời gian nào đông nhất?", payload)
    assert "Không đủ dữ liệu" in tra_loi


def test_bao_cao_va_hoi_dap_grounded_tren_du_lieu_that(seeded_db):
    db = seeded_db["db"]
    khu_vuc = seeded_db["khu_vuc"]
    loai_xe = seeded_db["loai_xe"]

    # tạo 1 lượt gửi xe hoàn tất để có dữ liệu
    crud.ghi_nhan_xe_vao(db, schemas.XeVaoRequest(
        bien_so="29A-1001", loai_xe_id=loai_xe.id, khu_vuc_id=khu_vuc.id,
        hinh_thuc_gui=models.KhungGio.sang,
    ))
    crud.ghi_nhan_xe_ra(db, schemas.XeRaRequest(bien_so="29A-1001"))

    tu_ngay = datetime.utcnow() - timedelta(days=1)
    den_ngay = datetime.utcnow() + timedelta(days=1)
    payload = ai_data.tong_hop_du_lieu_cho_ai(db, tu_ngay, den_ngay, khu_vuc.id)

    assert ai_data.du_lieu_rong(payload) is False
    assert payload["luu_luong"]["tong_so_luot"] == 1
    assert payload["luu_luong"]["thoi_gian_dong_nhat"] == "sang"

    bao_cao = ai_engine.sinh_bao_cao_luu_luong(payload)
    assert "BÁO CÁO LƯU LƯỢNG" in bao_cao
    # số liệu trong báo cáo phải khớp với payload (grounded - không bịa số liệu)
    assert str(payload["luu_luong"]["tong_so_luot"]) in bao_cao

    tra_loi_doanh_thu = ai_engine.hoi_dap_quan_tri("doanh thu hôm nay bao nhiêu?", payload)
    assert "VNĐ" in tra_loi_doanh_thu

    tra_loi_thoi_gian = ai_engine.hoi_dap_quan_tri("thời gian nào đông nhất?", payload)
    assert "Sáng" in tra_loi_thoi_gian


def test_goi_y_nhan_su_du_lieu_rong(seeded_db):
    db = seeded_db["db"]
    payload = ai_data.tong_hop_du_lieu_cho_ai(db, datetime(2020, 1, 1), datetime(2020, 1, 2))
    goi_y = ai_engine.goi_y_bo_tri_nhan_su(payload)
    assert "Không đủ dữ liệu" in goi_y


def test_goi_y_nhan_su_uu_tien_hinh_thuc_gui_dong_nhat(seeded_db):
    db = seeded_db["db"]
    khu_vuc = seeded_db["khu_vuc"]
    loai_xe = seeded_db["loai_xe"]

    # 3 lượt "sáng", 1 lượt "chiều" -> "sáng" phải đông nhất
    for i in range(3):
        bs = f"29A-100{i}"
        crud.ghi_nhan_xe_vao(db, schemas.XeVaoRequest(bien_so=bs, loai_xe_id=loai_xe.id, khu_vuc_id=khu_vuc.id, hinh_thuc_gui=models.KhungGio.sang))
        crud.ghi_nhan_xe_ra(db, schemas.XeRaRequest(bien_so=bs))
    crud.ghi_nhan_xe_vao(db, schemas.XeVaoRequest(bien_so="29A-2001", loai_xe_id=loai_xe.id, khu_vuc_id=khu_vuc.id, hinh_thuc_gui=models.KhungGio.chieu))
    crud.ghi_nhan_xe_ra(db, schemas.XeRaRequest(bien_so="29A-2001"))

    tu_ngay = datetime.utcnow() - timedelta(hours=1)
    den_ngay = datetime.utcnow() + timedelta(hours=1)
    payload = ai_data.tong_hop_du_lieu_cho_ai(db, tu_ngay, den_ngay, khu_vuc.id)
    assert payload["luu_luong"]["thoi_gian_dong_nhat"] == "sang"

    goi_y = ai_engine.goi_y_bo_tri_nhan_su(payload)
    assert "GỢI Ý BỐ TRÍ NHÂN SỰ" in goi_y
    assert "Sáng" in goi_y
