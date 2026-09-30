"""
Các hàm nghiệp vụ chính: QL-02 (danh mục), QL-03 (vào/ra), QL-04 (tính
phí - dùng app/fee.py), QL-05 (chỗ trống), QL-06 (tra cứu), QL-07 (vé
tháng).
"""
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas, fee


# ---------------------------------------------------------------------------
# QL-02: Danh mục khu vực / vị trí / loại xe
# ---------------------------------------------------------------------------

def tao_khu_vuc(db: Session, du_lieu: schemas.KhuVucCreate) -> models.KhuVuc:
    kv = models.KhuVuc(ten_khu_vuc=du_lieu.ten_khu_vuc, mo_ta=du_lieu.mo_ta, tong_so_vi_tri=0)
    db.add(kv)
    db.commit()
    db.refresh(kv)
    return kv


def cap_nhat_khu_vuc(db: Session, khu_vuc_id: int, du_lieu: schemas.KhuVucCreate) -> models.KhuVuc:
    kv = db.get(models.KhuVuc, khu_vuc_id)
    if kv is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Khu vực không tồn tại")
    kv.ten_khu_vuc = du_lieu.ten_khu_vuc
    kv.mo_ta = du_lieu.mo_ta
    db.commit()
    db.refresh(kv)
    return kv


def xoa_khu_vuc(db: Session, khu_vuc_id: int) -> None:
    kv = db.get(models.KhuVuc, khu_vuc_id)
    if kv is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Khu vực không tồn tại")
    if kv.tong_so_vi_tri > 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Hãy xoá hết vị trí đỗ trong khu vực này trước khi xoá khu vực")
    db.delete(kv)
    db.commit()


def tao_loai_xe(db: Session, du_lieu: schemas.LoaiXeCreate) -> models.LoaiXe:
    lx = models.LoaiXe(ten_loai_xe=du_lieu.ten_loai_xe)
    db.add(lx)
    db.commit()
    db.refresh(lx)
    return lx


def cap_nhat_loai_xe(db: Session, loai_xe_id: int, du_lieu: schemas.LoaiXeCreate) -> models.LoaiXe:
    lx = db.get(models.LoaiXe, loai_xe_id)
    if lx is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Loại xe không tồn tại")
    lx.ten_loai_xe = du_lieu.ten_loai_xe
    db.commit()
    db.refresh(lx)
    return lx


def xoa_loai_xe(db: Session, loai_xe_id: int) -> None:
    lx = db.get(models.LoaiXe, loai_xe_id)
    if lx is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Loại xe không tồn tại")
    dang_dung = db.query(models.PhuongTien).filter(models.PhuongTien.loai_xe_id == loai_xe_id).first()
    if dang_dung is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Loại xe đang được dùng bởi phương tiện, không thể xoá")
    db.query(models.BangGia).filter(models.BangGia.loai_xe_id == loai_xe_id).delete()
    db.delete(lx)
    db.commit()


def tao_vi_tri(db: Session, du_lieu: schemas.ViTriDoCreate) -> models.ViTriDo:
    kv = db.get(models.KhuVuc, du_lieu.khu_vuc_id)
    if kv is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Khu vực không tồn tại")
    vt = models.ViTriDo(
        khu_vuc_id=du_lieu.khu_vuc_id,
        ma_vi_tri=du_lieu.ma_vi_tri,
        loai_xe_cho_phep=du_lieu.loai_xe_cho_phep,
        trang_thai=models.TrangThaiViTri.trong,
    )
    db.add(vt)
    kv.tong_so_vi_tri += 1
    db.commit()
    db.refresh(vt)
    return vt


def tao_vi_tri_hang_loat(db: Session, du_lieu: schemas.ViTriHangLoatCreate) -> dict:
    """Tạo hàng loạt vị trí theo chữ cái đầu: A1, A2, ..., An. Bỏ qua (không
    tạo) những mã đã tồn tại sẵn trong cùng khu vực để không bị trùng tên."""
    kv = db.get(models.KhuVuc, du_lieu.khu_vuc_id)
    if kv is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Khu vực không tồn tại")

    da_ton_tai = {
        v.ma_vi_tri.strip().upper()
        for v in db.query(models.ViTriDo).filter(models.ViTriDo.khu_vuc_id == du_lieu.khu_vuc_id).all()
    }

    da_tao: list[str] = []
    bi_trung: list[str] = []
    for i in range(1, du_lieu.so_luong + 1):
        ma = f"{du_lieu.tien_to}{i}"
        if ma.upper() in da_ton_tai:
            bi_trung.append(ma)
            continue
        vt = models.ViTriDo(
            khu_vuc_id=du_lieu.khu_vuc_id,
            ma_vi_tri=ma,
            loai_xe_cho_phep=du_lieu.loai_xe_cho_phep,
            trang_thai=models.TrangThaiViTri.trong,
        )
        db.add(vt)
        kv.tong_so_vi_tri += 1
        da_tao.append(ma)
        da_ton_tai.add(ma.upper())

    db.commit()
    return {"so_luong_da_tao": len(da_tao), "da_tao": da_tao, "bi_trung": bi_trung}


def cap_nhat_vi_tri(db: Session, vi_tri_id: int, du_lieu: schemas.ViTriDoUpdate) -> models.ViTriDo:
    vt = db.get(models.ViTriDo, vi_tri_id)
    if vt is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Vị trí không tồn tại")
    vt.ma_vi_tri = du_lieu.ma_vi_tri
    vt.loai_xe_cho_phep = du_lieu.loai_xe_cho_phep
    db.commit()
    db.refresh(vt)
    return vt


def xoa_vi_tri(db: Session, vi_tri_id: int) -> None:
    vt = db.get(models.ViTriDo, vi_tri_id)
    if vt is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Vị trí không tồn tại")
    if vt.trang_thai == models.TrangThaiViTri.da_do:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Không thể xoá vị trí đang có xe đỗ")
    kv = db.get(models.KhuVuc, vt.khu_vuc_id)
    if kv:
        kv.tong_so_vi_tri = max(0, kv.tong_so_vi_tri - 1)
    db.delete(vt)
    db.commit()


def tao_bang_gia(db: Session, du_lieu: schemas.BangGiaCreate) -> models.BangGia:
    bg = models.BangGia(loai_xe_id=du_lieu.loai_xe_id, khung_gio=du_lieu.khung_gio, don_gia=du_lieu.don_gia)
    db.add(bg)
    db.commit()
    db.refresh(bg)
    return bg


def cap_nhat_bang_gia(db: Session, bang_gia_id: int, du_lieu: schemas.BangGiaCreate) -> models.BangGia:
    bg = db.get(models.BangGia, bang_gia_id)
    if bg is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Bảng giá không tồn tại")
    bg.loai_xe_id = du_lieu.loai_xe_id
    bg.khung_gio = du_lieu.khung_gio
    bg.don_gia = du_lieu.don_gia
    db.commit()
    db.refresh(bg)
    return bg


def xoa_bang_gia(db: Session, bang_gia_id: int) -> None:
    bg = db.get(models.BangGia, bang_gia_id)
    if bg is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Bảng giá không tồn tại")
    db.delete(bg)
    db.commit()


def lay_don_gia_theo_loai_xe(db: Session, loai_xe_id: int) -> dict:
    rows = db.query(models.BangGia).filter(models.BangGia.loai_xe_id == loai_xe_id).all()
    return {row.khung_gio: row.don_gia for row in rows}


# ---------------------------------------------------------------------------
# QL-05: Chỗ trống
# ---------------------------------------------------------------------------

def goi_y_vi_tri_trong(db: Session, khu_vuc_id: int, loai_xe_id: Optional[int] = None) -> Optional[models.ViTriDo]:
    q = db.query(models.ViTriDo).filter(
        models.ViTriDo.khu_vuc_id == khu_vuc_id,
        models.ViTriDo.trang_thai == models.TrangThaiViTri.trong,
    )
    if loai_xe_id is not None:
        q = q.filter(
            (models.ViTriDo.loai_xe_cho_phep == loai_xe_id) | (models.ViTriDo.loai_xe_cho_phep.is_(None))
        )
    return q.first()


def trang_thai_cho_trong(db: Session, khu_vuc_id: Optional[int] = None) -> list[dict]:
    q = db.query(models.KhuVuc)
    if khu_vuc_id is not None:
        q = q.filter(models.KhuVuc.id == khu_vuc_id)

    # Với các vị trí đã có xe đỗ, tra thêm lượt gửi đang mở (dang_gui) tương
    # ứng để hiển thị chi tiết: biển số, loại xe, giờ vào, đã đỗ bao lâu -
    # phục vụ mục "Xem chỗ trống" chi tiết hơn trên giao diện.
    luot_dang_gui = (
        db.query(models.LuotGuiXe)
        .filter(models.LuotGuiXe.trang_thai == models.TrangThaiLuot.dang_gui)
        .all()
    )
    luot_theo_vi_tri = {l.vi_tri_id: l for l in luot_dang_gui}
    if luot_theo_vi_tri:
        pt_map = {
            p.id: p
            for p in db.query(models.PhuongTien)
            .filter(models.PhuongTien.id.in_({l.phuong_tien_id for l in luot_theo_vi_tri.values()}))
            .all()
        }
        loai_xe_map = {lx.id: lx.ten_loai_xe for lx in db.query(models.LoaiXe).all()}
    else:
        pt_map, loai_xe_map = {}, {}

    now = datetime.utcnow()
    ket_qua = []
    for kv in q.all():
        vi_tri_list = db.query(models.ViTriDo).filter(models.ViTriDo.khu_vuc_id == kv.id).all()
        trong = sum(1 for v in vi_tri_list if v.trang_thai == models.TrangThaiViTri.trong)

        vi_tri_chi_tiet = []
        for v in vi_tri_list:
            item = {"id": v.id, "ma_vi_tri": v.ma_vi_tri, "trang_thai": v.trang_thai.value, "xe_dang_do": None}
            luot = luot_theo_vi_tri.get(v.id)
            if luot is not None:
                pt = pt_map.get(luot.phuong_tien_id)
                so_phut_da_do = int((now - luot.thoi_gian_vao).total_seconds() // 60)
                item["xe_dang_do"] = {
                    "luot_gui_id": luot.id,
                    "bien_so": pt.bien_so if pt else None,
                    "ten_loai_xe": loai_xe_map.get(pt.loai_xe_id) if pt else None,
                    "chu_xe": pt.chu_xe if pt else None,
                    "thoi_gian_vao": luot.thoi_gian_vao.isoformat(),
                    "so_phut_da_do": max(so_phut_da_do, 0),
                }
            vi_tri_chi_tiet.append(item)

        ket_qua.append({
            "khu_vuc_id": kv.id,
            "ten_khu_vuc": kv.ten_khu_vuc,
            "tong_so_vi_tri": kv.tong_so_vi_tri,
            "so_cho_trong": trong,
            "so_da_do": kv.tong_so_vi_tri - trong,
            "vi_tri": vi_tri_chi_tiet,
        })
    return ket_qua


# ---------------------------------------------------------------------------
# QL-03 + QL-04: Ghi nhận xe vào / ra + tính phí
# ---------------------------------------------------------------------------

def _lay_hoac_tao_phuong_tien(db: Session, bien_so: str, loai_xe_id: Optional[int],
                               chu_xe: Optional[str], so_dien_thoai: Optional[str]) -> models.PhuongTien:
    pt = db.query(models.PhuongTien).filter(models.PhuongTien.bien_so == bien_so).first()
    if pt is not None:
        # Xe đã có trong hệ thống nhưng thông tin có thể đã thay đổi (đổi
        # chủ xe, đổi SĐT, hoặc nhân viên từng nhập sai loại xe ở lần đăng
        # ký đầu tiên) - cập nhật lại theo dữ liệu mới nhất mỗi lần ghi
        # nhận xe vào, để tính phí và tra cứu luôn đúng thay vì giữ mãi
        # thông tin cũ. Chỉ cập nhật khi có giá trị mới VÀ khác giá trị cũ.
        thay_doi = False
        if loai_xe_id is not None and loai_xe_id != pt.loai_xe_id:
            pt.loai_xe_id = loai_xe_id
            thay_doi = True
        if chu_xe and chu_xe != pt.chu_xe:
            pt.chu_xe = chu_xe
            thay_doi = True
        if so_dien_thoai and so_dien_thoai != pt.so_dien_thoai:
            pt.so_dien_thoai = so_dien_thoai
            thay_doi = True
        if thay_doi:
            db.commit()
            db.refresh(pt)
        return pt
    if loai_xe_id is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Xe chưa từng đăng ký - cần cung cấp loai_xe_id")
    pt = models.PhuongTien(bien_so=bien_so, loai_xe_id=loai_xe_id, chu_xe=chu_xe, so_dien_thoai=so_dien_thoai)
    db.add(pt)
    db.commit()
    db.refresh(pt)
    return pt


def ghi_nhan_xe_vao(db: Session, du_lieu: schemas.XeVaoRequest) -> models.LuotGuiXe:
    pt = _lay_hoac_tao_phuong_tien(db, du_lieu.bien_so, du_lieu.loai_xe_id, du_lieu.chu_xe, du_lieu.so_dien_thoai)

    # Không cho phép 1 xe có 2 lượt gửi đang mở cùng lúc
    dang_gui = db.query(models.LuotGuiXe).filter(
        models.LuotGuiXe.phuong_tien_id == pt.id,
        models.LuotGuiXe.trang_thai == models.TrangThaiLuot.dang_gui,
    ).first()
    if dang_gui is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Xe {du_lieu.bien_so} đang có lượt gửi chưa hoàn tất (id={dang_gui.id})")

    if du_lieu.vi_tri_id is not None:
        vi_tri = db.get(models.ViTriDo, du_lieu.vi_tri_id)
        if vi_tri is None or vi_tri.trang_thai != models.TrangThaiViTri.trong:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Vị trí không hợp lệ hoặc đã có xe đỗ")
    else:
        vi_tri = goi_y_vi_tri_trong(db, du_lieu.khu_vuc_id, pt.loai_xe_id)
        if vi_tri is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Khu vực đã hết chỗ trống phù hợp")

    luot = models.LuotGuiXe(
        phuong_tien_id=pt.id,
        vi_tri_id=vi_tri.id,
        thoi_gian_vao=datetime.utcnow(),
        trang_thai=models.TrangThaiLuot.dang_gui,
        hinh_thuc_gui=du_lieu.hinh_thuc_gui,
    )
    vi_tri.trang_thai = models.TrangThaiViTri.da_do
    db.add(luot)
    db.commit()
    db.refresh(luot)
    return luot


def ghi_nhan_xe_ra(db: Session, du_lieu: schemas.XeRaRequest) -> models.LuotGuiXe:
    luot: Optional[models.LuotGuiXe] = None
    if du_lieu.luot_gui_xe_id is not None:
        luot = db.get(models.LuotGuiXe, du_lieu.luot_gui_xe_id)
    elif du_lieu.bien_so is not None:
        pt = db.query(models.PhuongTien).filter(models.PhuongTien.bien_so == du_lieu.bien_so).first()
        if pt is not None:
            luot = db.query(models.LuotGuiXe).filter(
                models.LuotGuiXe.phuong_tien_id == pt.id,
                models.LuotGuiXe.trang_thai == models.TrangThaiLuot.dang_gui,
            ).first()

    if luot is None or luot.trang_thai != models.TrangThaiLuot.dang_gui:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy lượt gửi xe đang mở tương ứng")

    thoi_gian_ra = datetime.utcnow()
    pt = db.get(models.PhuongTien, luot.phuong_tien_id)

    # Cho phép xác nhận/đổi lại hình thức gửi xe ngay lúc xe ra; nếu không
    # chọn lại thì dùng đúng hình thức đã chọn lúc xe vào.
    hinh_thuc = du_lieu.hinh_thuc_gui or luot.hinh_thuc_gui
    if hinh_thuc is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Chưa chọn thời gian gửi xe (sáng/chiều/tối/qua đêm/theo tháng)")

    gia_row = db.query(models.BangGia).filter(
        models.BangGia.loai_xe_id == pt.loai_xe_id,
        models.BangGia.khung_gio == hinh_thuc,
    ).first()
    if gia_row is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Chưa cấu hình bảng giá cho loại xe và thời gian gửi đã chọn")

    phi = fee.tinh_phi(luot.thoi_gian_vao, thoi_gian_ra, hinh_thuc, gia_row.don_gia)
    if du_lieu.mat_ve:
        phi += fee.PHI_PHU_MAT_VE

    luot.thoi_gian_ra = thoi_gian_ra
    luot.phi_thu = phi
    luot.hinh_thuc_gui = hinh_thuc
    luot.mat_ve = du_lieu.mat_ve
    luot.thong_tin_chung_minh = du_lieu.thong_tin_chung_minh
    luot.trang_thai = models.TrangThaiLuot.hoan_tat

    vi_tri = db.get(models.ViTriDo, luot.vi_tri_id)
    if vi_tri:
        vi_tri.trang_thai = models.TrangThaiViTri.trong

    db.commit()
    db.refresh(luot)
    return luot


# ---------------------------------------------------------------------------
# QL-06: Tra cứu lượt gửi xe
# ---------------------------------------------------------------------------

def tra_cuu_luot_xe(db: Session, tham_so: schemas.TraCuuLuotXeParams) -> list[dict]:
    """
    Tra cứu linh hoạt: có thể kết hợp bất kỳ tiêu chí nào (biển số, tên chủ xe,
    số điện thoại, loại xe, khu vực, trạng thái, khoảng ngày). Các tiêu chí
    được kết hợp theo kiểu AND - càng cung cấp nhiều thông tin, kết quả trả về
    càng thu hẹp và chính xác hơn.
    """
    q = (
        db.query(models.LuotGuiXe, models.PhuongTien, models.ViTriDo, models.KhuVuc, models.LoaiXe)
        .join(models.PhuongTien, models.LuotGuiXe.phuong_tien_id == models.PhuongTien.id)
        .join(models.ViTriDo, models.LuotGuiXe.vi_tri_id == models.ViTriDo.id)
        .join(models.KhuVuc, models.ViTriDo.khu_vuc_id == models.KhuVuc.id)
        .join(models.LoaiXe, models.PhuongTien.loai_xe_id == models.LoaiXe.id)
    )
    if tham_so.bien_so:
        q = q.filter(models.PhuongTien.bien_so.ilike(f"%{tham_so.bien_so}%"))
    if tham_so.chu_xe:
        q = q.filter(models.PhuongTien.chu_xe.ilike(f"%{tham_so.chu_xe}%"))
    if tham_so.so_dien_thoai:
        q = q.filter(models.PhuongTien.so_dien_thoai.ilike(f"%{tham_so.so_dien_thoai}%"))
    if tham_so.loai_xe_id:
        q = q.filter(models.PhuongTien.loai_xe_id == tham_so.loai_xe_id)
    if tham_so.khu_vuc_id:
        q = q.filter(models.ViTriDo.khu_vuc_id == tham_so.khu_vuc_id)
    if tham_so.trang_thai:
        q = q.filter(models.LuotGuiXe.trang_thai == tham_so.trang_thai)
    if tham_so.tu_ngay:
        q = q.filter(models.LuotGuiXe.thoi_gian_vao >= tham_so.tu_ngay)
    if tham_so.den_ngay:
        q = q.filter(models.LuotGuiXe.thoi_gian_vao <= tham_so.den_ngay)

    rows = q.order_by(models.LuotGuiXe.thoi_gian_vao.desc()).limit(500).all()
    return [
        {
            "id": luot.id,
            "bien_so": pt.bien_so,
            "chu_xe": pt.chu_xe,
            "so_dien_thoai": pt.so_dien_thoai,
            "ten_loai_xe": lx.ten_loai_xe,
            "ten_khu_vuc": kv.ten_khu_vuc,
            "ma_vi_tri": vt.ma_vi_tri,
            "thoi_gian_vao": luot.thoi_gian_vao,
            "thoi_gian_ra": luot.thoi_gian_ra,
            "phi_thu": luot.phi_thu,
            "trang_thai": luot.trang_thai,
            "hinh_thuc_gui": luot.hinh_thuc_gui,
            "mat_ve": luot.mat_ve,
        }
        for luot, pt, vt, kv, lx in rows
    ]
