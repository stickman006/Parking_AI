"""
QL-04: Tính phí gửi xe.

Thiết kế mới: nhân viên chọn tường minh "hình thức/thời gian gửi xe" khi
ghi nhận xe vào (có thể xác nhận/đổi lại khi xe ra), thay vì hệ thống tự
suy đoán theo giờ đồng hồ như trước - đảm bảo tính phí chính xác theo
đúng bảng giá quản lý đã cấu hình cho hình thức đó.

Các hình thức gửi xe (KhungGio):
    sang           06:00 - 13:00   tính theo GIỜ thực tế đỗ
    chieu          13:00 - 18:00   tính theo GIỜ thực tế đỗ
    toi            18:00 - 06:00   tính theo GIỜ thực tế đỗ (qua nửa đêm)
    qua_dem        Gửi qua đêm     tính theo GIỜ thực tế đỗ
    thang          Gửi theo tháng          1 chu kỳ = 30 NGÀY
    qua_dem_thang  Gửi xe qua đêm theo tháng  1 chu kỳ = 30 NGÀY

Quy tắc tính:
- sang/chieu/toi/qua_dem: phí = số giờ thực đỗ (làm tròn lên, tối thiểu
  1 giờ) x đơn giá/giờ của hình thức đã chọn.
- thang/qua_dem_thang: phí = số chu kỳ 30 ngày (làm tròn lên, tối thiểu
  1 chu kỳ) x đơn giá/chu kỳ của hình thức đã chọn.
"""
import math
from datetime import datetime

from app.models import KhungGio

# Khoảng giờ tham khảo (0-24, "toi" bọc qua nửa đêm) - hiển thị cho người
# dùng biết mỗi nhãn ứng với khung giờ nào; KHÔNG dùng để tự suy đoán hình
# thức gửi xe nữa (nhân viên chọn tường minh).
KHUNG_GIO_KHOANG_GIO = {
    KhungGio.sang: (6, 13),
    KhungGio.chieu: (13, 18),
    KhungGio.toi: (18, 6),
}

# Các hình thức tính phí theo chu kỳ 30 ngày thay vì theo giờ.
HINH_THUC_THEO_THANG = {KhungGio.thang, KhungGio.qua_dem_thang}

SO_NGAY_MOI_CHU_KY = 30


def tinh_phi(thoi_gian_vao: datetime, thoi_gian_ra: datetime,
             hinh_thuc_gui: KhungGio, don_gia: float) -> float:
    """Tính phí gửi xe theo hình thức đã chọn và đơn giá tương ứng (lấy từ
    bảng giá theo loại xe + hình thức gửi)."""
    if thoi_gian_ra <= thoi_gian_vao:
        raise ValueError("Thời gian ra phải sau thời gian vào")

    if hinh_thuc_gui in HINH_THUC_THEO_THANG:
        so_ngay = (thoi_gian_ra - thoi_gian_vao).total_seconds() / 86400
        so_chu_ky = max(1, math.ceil(so_ngay / SO_NGAY_MOI_CHU_KY - 1e-9))
        return round(so_chu_ky * don_gia, 2)

    so_gio = (thoi_gian_ra - thoi_gian_vao).total_seconds() / 3600
    so_gio_lam_tron = max(1, math.ceil(so_gio - 1e-9))
    return round(so_gio_lam_tron * don_gia, 2)
