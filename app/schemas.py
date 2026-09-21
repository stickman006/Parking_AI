import re
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, field_validator

from app.models import VaiTro, TrangThaiViTri, TrangThaiLuot, KhungGio


# Biển số: 2 số (mã tỉnh) + 1-2 chữ (seri) + ĐÚNG 4 số, dấu . - khoảng trắng
# đều được chấp nhận khi nhập (sẽ bị bỏ qua lúc kiểm tra định dạng), ví dụ
# hợp lệ: "30A-1234", "30A1234", "30 A1 1234".
_BIEN_SO_RE = re.compile(r"^\d{2}[A-Z]{1,2}\d{4}$")
# Số điện thoại: đúng 10 số, bắt đầu bằng số 0.
_SDT_RE = re.compile(r"^0\d{9}$")


def _chuan_hoa_bien_so(v: str) -> str:
    if not re.fullmatch(_BIEN_SO_RE, re.sub(r"[\s\-\.]", "", v.upper())):
        raise ValueError("Biển số không hợp lệ - cần đúng 4 số (VD: 30A-1234)")
    return v


def _chuan_hoa_sdt(v: Optional[str]) -> Optional[str]:
    if v is None or v == "":
        return v
    if not _SDT_RE.fullmatch(v):
        raise ValueError("Số điện thoại phải gồm đúng 10 số và bắt đầu bằng số 0")
    return v


# ---------- Auth ----------
class NguoiDungCreate(BaseModel):
    ho_ten: str
    tai_khoan: str
    mat_khau: str
    vai_tro: VaiTro = VaiTro.nhan_vien


class NguoiDungOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ho_ten: str
    tai_khoan: str
    vai_tro: VaiTro


class LoginRequest(BaseModel):
    tai_khoan: str
    mat_khau: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    vai_tro: VaiTro
    ho_ten: str


# ---------- Danh mục ----------
class KhuVucCreate(BaseModel):
    ten_khu_vuc: str
    mo_ta: Optional[str] = None


class KhuVucOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ten_khu_vuc: str
    mo_ta: Optional[str] = None
    tong_so_vi_tri: int


class LoaiXeCreate(BaseModel):
    ten_loai_xe: str


class LoaiXeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ten_loai_xe: str


class ViTriDoCreate(BaseModel):
    khu_vuc_id: int
    ma_vi_tri: str
    loai_xe_cho_phep: Optional[int] = None


class ViTriDoUpdate(BaseModel):
    ma_vi_tri: str
    loai_xe_cho_phep: Optional[int] = None


class ViTriDoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    khu_vuc_id: int
    ma_vi_tri: str
    loai_xe_cho_phep: Optional[int] = None
    trang_thai: TrangThaiViTri


class ViTriHangLoatCreate(BaseModel):
    khu_vuc_id: int
    tien_to: str          # chữ cái đầu, ví dụ "A" -> A1, A2, ... An
    so_luong: int         # 10 / 50 / 100
    loai_xe_cho_phep: Optional[int] = None

    @field_validator("so_luong")
    @classmethod
    def _kt_so_luong(cls, v: int) -> int:
        if v <= 0 or v > 500:
            raise ValueError("Số lượng vị trí cần tạo phải trong khoảng 1-500")
        return v

    @field_validator("tien_to")
    @classmethod
    def _kt_tien_to(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Cần nhập chữ cái đầu cho vị trí (VD: A)")
        return v.strip()


class ViTriHangLoatOut(BaseModel):
    so_luong_da_tao: int
    da_tao: List[str]
    bi_trung: List[str]


class BangGiaCreate(BaseModel):
    loai_xe_id: int
    khung_gio: KhungGio
    don_gia: float


class BangGiaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    loai_xe_id: int
    khung_gio: KhungGio
    don_gia: float


# ---------- Phương tiện ----------
class PhuongTienCreate(BaseModel):
    bien_so: str
    loai_xe_id: int
    chu_xe: Optional[str] = None
    so_dien_thoai: Optional[str] = None

    @field_validator("bien_so")
    @classmethod
    def _kt_bien_so(cls, v: str) -> str:
        return _chuan_hoa_bien_so(v)

    @field_validator("so_dien_thoai")
    @classmethod
    def _kt_sdt(cls, v: Optional[str]) -> Optional[str]:
        return _chuan_hoa_sdt(v)


class PhuongTienOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    bien_so: str
    loai_xe_id: int
    chu_xe: Optional[str] = None
    so_dien_thoai: Optional[str] = None


# ---------- Ghi nhận vào / ra ----------
class XeVaoRequest(BaseModel):
    bien_so: str
    loai_xe_id: Optional[int] = None  # bắt buộc nếu xe chưa từng đăng ký
    khu_vuc_id: int
    vi_tri_id: Optional[int] = None   # nếu None -> hệ thống tự gợi ý vị trí trống
    chu_xe: Optional[str] = None
    so_dien_thoai: Optional[str] = None
    # Thời gian gửi xe (sáng/chiều/tối/qua đêm/theo tháng/qua đêm theo
    # tháng) - bắt buộc chọn để tính đúng bảng giá áp dụng khi xe ra.
    hinh_thuc_gui: KhungGio

    @field_validator("bien_so")
    @classmethod
    def _kt_bien_so(cls, v: str) -> str:
        return _chuan_hoa_bien_so(v)

    @field_validator("so_dien_thoai")
    @classmethod
    def _kt_sdt(cls, v: Optional[str]) -> Optional[str]:
        return _chuan_hoa_sdt(v)


class XeRaRequest(BaseModel):
    bien_so: Optional[str] = None
    luot_gui_xe_id: Optional[int] = None
    # Cho phép xác nhận/đổi lại hình thức gửi xe ngay tại thời điểm xe ra
    # (nếu để trống, hệ thống dùng hình thức đã chọn lúc xe vào).
    hinh_thuc_gui: Optional[KhungGio] = None


class LuotGuiXeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    phuong_tien_id: int
    vi_tri_id: int
    thoi_gian_vao: datetime
    thoi_gian_ra: Optional[datetime] = None
    phi_thu: Optional[float] = None
    trang_thai: TrangThaiLuot
    hinh_thuc_gui: Optional[KhungGio] = None


class TraCuuLuotXeParams(BaseModel):
    bien_so: Optional[str] = None
    chu_xe: Optional[str] = None
    so_dien_thoai: Optional[str] = None
    loai_xe_id: Optional[int] = None
    khu_vuc_id: Optional[int] = None
    trang_thai: Optional[TrangThaiLuot] = None
    tu_ngay: Optional[datetime] = None
    den_ngay: Optional[datetime] = None


class TraCuuKetQuaItem(BaseModel):
    id: int
    bien_so: str
    chu_xe: Optional[str] = None
    so_dien_thoai: Optional[str] = None
    ten_loai_xe: Optional[str] = None
    ten_khu_vuc: Optional[str] = None
    ma_vi_tri: Optional[str] = None
    thoi_gian_vao: datetime
    thoi_gian_ra: Optional[datetime] = None
    phi_thu: Optional[float] = None
    trang_thai: TrangThaiLuot
    hinh_thuc_gui: Optional[KhungGio] = None


# ---------- Thống kê ----------
class ThongKeLuuLuongItem(BaseModel):
    nhan: str          # nhãn thời gian (ngày / khung giờ)
    so_luot_vao: int
    so_luot_ra: int


class ThongKeDoanhThuItem(BaseModel):
    nhan: str
    doanh_thu: float


class TyLeLapDayItem(BaseModel):
    khu_vuc: str
    tong_vi_tri: int
    da_do: int
    ty_le: float


# ---------- AI ----------
class BaoCaoLuuLuongRequest(BaseModel):
    tu_ngay: datetime
    den_ngay: datetime
    khu_vuc_id: Optional[int] = None


class HoiDapRequest(BaseModel):
    cau_hoi: str
    tu_ngay: Optional[datetime] = None
    den_ngay: Optional[datetime] = None


class GoiYNhanSuRequest(BaseModel):
    tu_ngay: datetime
    den_ngay: datetime


class AITraLoiOut(BaseModel):
    cau_tra_loi: str
    du_lieu_dung: dict


class LichSuHoiDapOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    thoi_gian: datetime
    loai: str
    cau_hoi: Optional[str] = None
    cau_tra_loi: str
