"""
Mô hình dữ liệu (ORM) - tương ứng Bảng 2.3 (nghiệp vụ chính) và
Bảng 2.4 (dữ liệu tổng hợp phục vụ AI) trong báo cáo, mục 2.3.
"""
import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Enum, Text, Boolean
)
from sqlalchemy.orm import relationship

from app.database import Base


class VaiTro(str, enum.Enum):
    quan_ly = "quan_ly"
    nhan_vien = "nhan_vien"


class TrangThaiViTri(str, enum.Enum):
    trong = "trong"
    da_do = "da_do"


class TrangThaiLuot(str, enum.Enum):
    dang_gui = "dang_gui"
    hoan_tat = "hoan_tat"


class KhungGio(str, enum.Enum):
    """Hình thức / thời gian gửi xe - chọn tường minh khi ghi nhận xe vào
    (và có thể xác nhận lại khi xe ra) để tính đúng bảng giá áp dụng."""
    sang = "sang"                    # 06:00 - 13:00, tính theo giờ
    chieu = "chieu"                  # 13:00 - 18:00, tính theo giờ
    toi = "toi"                      # 18:00 - 06:00 (qua nửa đêm), tính theo giờ
    qua_dem = "qua_dem"              # Gửi qua đêm, tính theo giờ
    thang = "thang"                  # Gửi theo tháng, 1 chu kỳ = 30 ngày
    qua_dem_thang = "qua_dem_thang"  # Gửi xe qua đêm theo tháng, 1 chu kỳ = 30 ngày


# ---------------------------------------------------------------------------
# Nhóm bảng nghiệp vụ chính (Bảng 2.3)
# ---------------------------------------------------------------------------

class NguoiDung(Base):
    __tablename__ = "nguoi_dung"

    id = Column(Integer, primary_key=True, index=True)
    ho_ten = Column(String(150), nullable=False)
    tai_khoan = Column(String(100), unique=True, nullable=False, index=True)
    mat_khau_hash = Column(String(255), nullable=False)
    vai_tro = Column(Enum(VaiTro), nullable=False, default=VaiTro.nhan_vien)


class KhuVuc(Base):
    __tablename__ = "khu_vuc"

    id = Column(Integer, primary_key=True, index=True)
    ten_khu_vuc = Column(String(150), nullable=False)
    mo_ta = Column(String(255), nullable=True)
    tong_so_vi_tri = Column(Integer, nullable=False, default=0)

    vi_tri_list = relationship("ViTriDo", back_populates="khu_vuc", cascade="all, delete-orphan")


class LoaiXe(Base):
    __tablename__ = "loai_xe"

    id = Column(Integer, primary_key=True, index=True)
    ten_loai_xe = Column(String(100), nullable=False)  # xe máy / ô tô / xe điện


class ViTriDo(Base):
    __tablename__ = "vi_tri_do"

    id = Column(Integer, primary_key=True, index=True)
    khu_vuc_id = Column(Integer, ForeignKey("khu_vuc.id"), nullable=False)
    ma_vi_tri = Column(String(50), nullable=False)
    loai_xe_cho_phep = Column(Integer, ForeignKey("loai_xe.id"), nullable=True)
    trang_thai = Column(Enum(TrangThaiViTri), nullable=False, default=TrangThaiViTri.trong)

    khu_vuc = relationship("KhuVuc", back_populates="vi_tri_list")


class PhuongTien(Base):
    __tablename__ = "phuong_tien"

    id = Column(Integer, primary_key=True, index=True)
    bien_so = Column(String(30), unique=True, nullable=False, index=True)
    loai_xe_id = Column(Integer, ForeignKey("loai_xe.id"), nullable=False)
    chu_xe = Column(String(150), nullable=True)
    so_dien_thoai = Column(String(20), nullable=True)


class BangGia(Base):
    __tablename__ = "bang_gia"

    id = Column(Integer, primary_key=True, index=True)
    loai_xe_id = Column(Integer, ForeignKey("loai_xe.id"), nullable=False)
    khung_gio = Column(Enum(KhungGio), nullable=False)
    don_gia = Column(Float, nullable=False)  # đơn giá / giờ (VNĐ)


class LuotGuiXe(Base):
    __tablename__ = "luot_gui_xe"

    id = Column(Integer, primary_key=True, index=True)
    phuong_tien_id = Column(Integer, ForeignKey("phuong_tien.id"), nullable=False)
    vi_tri_id = Column(Integer, ForeignKey("vi_tri_do.id"), nullable=False)
    thoi_gian_vao = Column(DateTime, nullable=False, default=datetime.utcnow)
    thoi_gian_ra = Column(DateTime, nullable=True)
    phi_thu = Column(Float, nullable=True)
    trang_thai = Column(Enum(TrangThaiLuot), nullable=False, default=TrangThaiLuot.dang_gui)
    # Hình thức/thời gian gửi xe do nhân viên chọn khi ghi nhận xe vào (có
    # thể xác nhận/đổi lại khi xe ra) - quyết định đơn giá áp dụng để tính
    # phí chính xác, thay vì suy đoán tự động theo giờ đồng hồ.
    hinh_thuc_gui = Column(Enum(KhungGio), nullable=True)


# ---------------------------------------------------------------------------
# Dữ liệu tổng hợp phục vụ AI (Bảng 2.4) - ở đây triển khai lich_su_hoi_dap_ai
# làm bảng thật; các bảng/view thống kê còn lại (thong_ke_luu_luong,
# thong_ke_doanh_thu, ty_le_lap_day) được TÍNH TRỰC TIẾP bằng truy vấn tổng
# hợp trong app/ai_data.py thay vì vật lý hoá thành bảng, để luôn phản ánh
# đúng dữ liệu nghiệp vụ mới nhất.
# ---------------------------------------------------------------------------

class LichSuHoiDapAI(Base):
    __tablename__ = "lich_su_hoi_dap_ai"

    id = Column(Integer, primary_key=True, index=True)
    thoi_gian = Column(DateTime, nullable=False, default=datetime.utcnow)
    loai = Column(String(30), nullable=False)  # bao_cao / hoi_dap / goi_y_nhan_su
    cau_hoi = Column(Text, nullable=True)
    du_lieu_gui_kem = Column(Text, nullable=True)  # JSON string - phục vụ đối chiếu/kiểm thử
    cau_tra_loi = Column(Text, nullable=False)
