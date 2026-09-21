from datetime import datetime

import pytest

from app.models import KhungGio
from app.fee import tinh_phi


def test_phi_theo_gio_lam_tron_len():
    vao = datetime(2026, 1, 1, 8, 0)
    ra = datetime(2026, 1, 1, 10, 30)  # 2.5h -> làm tròn lên 3h
    phi = tinh_phi(vao, ra, KhungGio.sang, 3000)
    assert phi == 3 * 3000


def test_phi_toi_thieu_1_gio_khi_gui_ngan():
    vao = datetime(2026, 1, 1, 8, 0)
    ra = datetime(2026, 1, 1, 8, 10)  # 10 phút -> tối thiểu 1 giờ
    phi = tinh_phi(vao, ra, KhungGio.chieu, 3000)
    assert phi == 1 * 3000


def test_phi_qua_dem_tinh_theo_gio():
    vao = datetime(2026, 1, 1, 23, 0)
    ra = datetime(2026, 1, 2, 2, 0)  # 3 giờ
    phi = tinh_phi(vao, ra, KhungGio.qua_dem, 5000)
    assert phi == 3 * 5000


def test_phi_gui_theo_thang_duoi_30_ngay_tinh_1_chu_ky():
    vao = datetime(2026, 1, 1, 8, 0)
    ra = datetime(2026, 1, 20, 8, 0)  # 19 ngày -> vẫn 1 chu kỳ 30 ngày
    phi = tinh_phi(vao, ra, KhungGio.thang, 150000)
    assert phi == 150000


def test_phi_gui_theo_thang_qua_30_ngay_tinh_2_chu_ky():
    vao = datetime(2026, 1, 1, 8, 0)
    ra = datetime(2026, 2, 5, 8, 0)  # 35 ngày -> làm tròn lên 2 chu kỳ
    phi = tinh_phi(vao, ra, KhungGio.thang, 150000)
    assert phi == 2 * 150000


def test_phi_qua_dem_theo_thang_tinh_theo_chu_ky_30_ngay():
    vao = datetime(2026, 1, 1, 8, 0)
    ra = datetime(2026, 1, 31, 8, 0)  # đúng 30 ngày -> 1 chu kỳ
    phi = tinh_phi(vao, ra, KhungGio.qua_dem_thang, 200000)
    assert phi == 200000


def test_thoi_gian_ra_truoc_vao_bao_loi():
    with pytest.raises(ValueError):
        tinh_phi(datetime(2026, 1, 1, 10, 0), datetime(2026, 1, 1, 9, 0), KhungGio.sang, 3000)
