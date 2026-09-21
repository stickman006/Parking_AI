"""
2.3.3 / 3.3.1: Xây dựng pipeline tổng hợp dữ liệu đầu vào cho AI.

Các hàm ở đây KHÔNG gửi dữ liệu thô cho AI. Chúng truy vấn CSDL, tổng
hợp thành số liệu (dict/list các số), rồi mới được đưa vào phần user
prompt ở app/ai_engine.py. Điều này đúng với ràng buộc grounded
generation: AI chỉ nhận số liệu đã tính sẵn, không tự tính toán.
"""
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from app import models


def thong_ke_luu_luong(db: Session, tu_ngay: datetime, den_ngay: datetime,
                        khu_vuc_id: Optional[int] = None) -> dict:
    """thong_ke_luu_luong: số lượt xe vào/ra theo ngày và theo thời gian gửi
    xe (sáng/chiều/tối/qua đêm/theo tháng/qua đêm theo tháng)."""
    q = db.query(models.LuotGuiXe).filter(
        models.LuotGuiXe.thoi_gian_vao >= tu_ngay,
        models.LuotGuiXe.thoi_gian_vao < den_ngay,
    )
    if khu_vuc_id is not None:
        q = q.join(models.ViTriDo).filter(models.ViTriDo.khu_vuc_id == khu_vuc_id)

    luot_list = q.all()

    theo_ngay = defaultdict(lambda: {"vao": 0, "ra": 0})
    theo_hinh_thuc = defaultdict(int)  # hình thức gửi xe -> số lượt

    for luot in luot_list:
        ngay_key = luot.thoi_gian_vao.strftime("%Y-%m-%d")
        theo_ngay[ngay_key]["vao"] += 1
        if luot.hinh_thuc_gui is not None:
            theo_hinh_thuc[luot.hinh_thuc_gui.value] += 1
        if luot.thoi_gian_ra is not None and tu_ngay <= luot.thoi_gian_ra < den_ngay:
            ngay_ra_key = luot.thoi_gian_ra.strftime("%Y-%m-%d")
            theo_ngay[ngay_ra_key]["ra"] += 1

    tong_co_hinh_thuc = sum(theo_hinh_thuc.values())
    ty_le_theo_hinh_thuc = (
        {k: round(v / tong_co_hinh_thuc * 100, 1) for k, v in theo_hinh_thuc.items()}
        if tong_co_hinh_thuc else {}
    )
    thoi_gian_dong_nhat = max(theo_hinh_thuc.items(), key=lambda kv: kv[1])[0] if theo_hinh_thuc else None

    return {
        "tong_so_luot": len(luot_list),
        "theo_ngay": dict(sorted(theo_ngay.items())),
        "theo_hinh_thuc_gui": dict(theo_hinh_thuc),
        "ty_le_theo_hinh_thuc_gui": ty_le_theo_hinh_thuc,
        "thoi_gian_dong_nhat": thoi_gian_dong_nhat,
    }


def thong_ke_doanh_thu(db: Session, tu_ngay: datetime, den_ngay: datetime,
                        khu_vuc_id: Optional[int] = None) -> dict:
    """thong_ke_doanh_thu: tổng phí thu được theo ngày, theo loại xe."""
    q = db.query(models.LuotGuiXe).filter(
        models.LuotGuiXe.thoi_gian_ra.isnot(None),
        models.LuotGuiXe.thoi_gian_ra >= tu_ngay,
        models.LuotGuiXe.thoi_gian_ra < den_ngay,
        models.LuotGuiXe.trang_thai == models.TrangThaiLuot.hoan_tat,
    )
    if khu_vuc_id is not None:
        q = q.join(models.ViTriDo).filter(models.ViTriDo.khu_vuc_id == khu_vuc_id)

    luot_list = q.all()

    theo_ngay = defaultdict(float)
    theo_loai_xe = defaultdict(float)

    for luot in luot_list:
        ngay_key = luot.thoi_gian_ra.strftime("%Y-%m-%d")
        theo_ngay[ngay_key] += luot.phi_thu or 0.0
        pt = db.get(models.PhuongTien, luot.phuong_tien_id)
        if pt is not None:
            loai = db.get(models.LoaiXe, pt.loai_xe_id)
            ten_loai = loai.ten_loai_xe if loai else "không xác định"
            theo_loai_xe[ten_loai] += luot.phi_thu or 0.0

    return {
        "tong_doanh_thu": round(sum(theo_ngay.values()), 2),
        "theo_ngay": {k: round(v, 2) for k, v in sorted(theo_ngay.items())},
        "theo_loai_xe": {k: round(v, 2) for k, v in theo_loai_xe.items()},
    }


def ty_le_lap_day(db: Session, khu_vuc_id: Optional[int] = None) -> dict:
    """ty_le_lap_day: tỷ lệ vị trí đã đỗ/tổng vị trí theo khu vực (thời điểm hiện tại)."""
    q = db.query(models.KhuVuc)
    if khu_vuc_id is not None:
        q = q.filter(models.KhuVuc.id == khu_vuc_id)

    ket_qua = []
    for kv in q.all():
        tong = db.query(func.count(models.ViTriDo.id)).filter(models.ViTriDo.khu_vuc_id == kv.id).scalar() or 0
        da_do = db.query(func.count(models.ViTriDo.id)).filter(
            models.ViTriDo.khu_vuc_id == kv.id,
            models.ViTriDo.trang_thai == models.TrangThaiViTri.da_do,
        ).scalar() or 0
        ty_le = round(da_do / tong, 3) if tong > 0 else 0.0
        ket_qua.append({
            "khu_vuc": kv.ten_khu_vuc,
            "tong_vi_tri": tong,
            "da_do": da_do,
            "ty_le": ty_le,
        })
    return {"theo_khu_vuc": ket_qua}


def tong_hop_du_lieu_cho_ai(db: Session, tu_ngay: datetime, den_ngay: datetime,
                             khu_vuc_id: Optional[int] = None) -> dict:
    """Gộp cả 3 nhóm số liệu thành một payload duy nhất để đưa vào prompt."""
    return {
        "khoang_thoi_gian": {"tu_ngay": tu_ngay.isoformat(), "den_ngay": den_ngay.isoformat()},
        "luu_luong": thong_ke_luu_luong(db, tu_ngay, den_ngay, khu_vuc_id),
        "doanh_thu": thong_ke_doanh_thu(db, tu_ngay, den_ngay, khu_vuc_id),
        "lap_day": ty_le_lap_day(db, khu_vuc_id),
    }


def du_lieu_rong(payload: dict) -> bool:
    """Kiểm tra dữ liệu tổng hợp có rỗng hay không (phục vụ 3.4.3 - test dữ liệu rỗng)."""
    luu_luong = payload.get("luu_luong", {})
    return luu_luong.get("tong_so_luot", 0) == 0
