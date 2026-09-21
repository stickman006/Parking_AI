"""
Script tạo dữ liệu mẫu: 1 tài khoản quản lý, 1 nhân viên, khu vực/vị trí,
loại xe, bảng giá và một số lượt gửi xe trong 7 ngày gần đây để có thể
demo ngay các chức năng thống kê và AI mà không cần nhập tay.

Chạy: python -m app.seed
"""
import random
from datetime import datetime, timedelta

from app.database import Base, engine, SessionLocal
from app import models, security, fee

random.seed(42)


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(models.NguoiDung).first():
            print("Dữ liệu đã tồn tại - bỏ qua seed. Xoá file parking.db nếu muốn seed lại.")
            return

        # Người dùng
        quan_ly = models.NguoiDung(
            ho_ten="Tô Văn Thịnh", tai_khoan="quanly",
            mat_khau_hash=security.hash_password("123456"),
            vai_tro=models.VaiTro.quan_ly,
        )
        nhan_vien = models.NguoiDung(
            ho_ten="Đồng Minh Duy", tai_khoan="nhanvien",
            mat_khau_hash=security.hash_password("123456"),
            vai_tro=models.VaiTro.nhan_vien,
        )
        db.add_all([quan_ly, nhan_vien])

        # Loại xe
        xe_may = models.LoaiXe(ten_loai_xe="Xe máy")
        o_to = models.LoaiXe(ten_loai_xe="Ô tô")
        xe_dien = models.LoaiXe(ten_loai_xe="Xe điện")
        db.add_all([xe_may, o_to, xe_dien])
        db.flush()

        # Khu vực + vị trí
        khu_a = models.KhuVuc(ten_khu_vuc="Khu A - Tầng hầm 1", mo_ta="Dành cho xe máy", tong_so_vi_tri=0)
        khu_b = models.KhuVuc(ten_khu_vuc="Khu B - Sân trước", mo_ta="Dành cho ô tô", tong_so_vi_tri=0)
        db.add_all([khu_a, khu_b])
        db.flush()

        for i in range(1, 11):
            db.add(models.ViTriDo(khu_vuc_id=khu_a.id, ma_vi_tri=f"A-{i:02d}", loai_xe_cho_phep=xe_may.id))
            khu_a.tong_so_vi_tri += 1
        for i in range(1, 6):
            db.add(models.ViTriDo(khu_vuc_id=khu_b.id, ma_vi_tri=f"B-{i:02d}", loai_xe_cho_phep=o_to.id))
            khu_b.tong_so_vi_tri += 1

        # Bảng giá: sáng/chiều/tối tính theo giờ; gửi qua đêm cũng theo
        # giờ (đơn giá cao hơn); gửi theo tháng / qua đêm theo tháng tính
        # theo chu kỳ 30 ngày (đơn giá trọn gói).
        db.add_all([
            models.BangGia(loai_xe_id=xe_may.id, khung_gio=models.KhungGio.sang, don_gia=3000),
            models.BangGia(loai_xe_id=xe_may.id, khung_gio=models.KhungGio.chieu, don_gia=3000),
            models.BangGia(loai_xe_id=xe_may.id, khung_gio=models.KhungGio.toi, don_gia=4000),
            models.BangGia(loai_xe_id=xe_may.id, khung_gio=models.KhungGio.qua_dem, don_gia=5000),
            models.BangGia(loai_xe_id=xe_may.id, khung_gio=models.KhungGio.thang, don_gia=150000),
            models.BangGia(loai_xe_id=xe_may.id, khung_gio=models.KhungGio.qua_dem_thang, don_gia=200000),
            models.BangGia(loai_xe_id=o_to.id, khung_gio=models.KhungGio.sang, don_gia=15000),
            models.BangGia(loai_xe_id=o_to.id, khung_gio=models.KhungGio.chieu, don_gia=15000),
            models.BangGia(loai_xe_id=o_to.id, khung_gio=models.KhungGio.toi, don_gia=20000),
            models.BangGia(loai_xe_id=o_to.id, khung_gio=models.KhungGio.qua_dem, don_gia=25000),
            models.BangGia(loai_xe_id=o_to.id, khung_gio=models.KhungGio.thang, don_gia=800000),
            models.BangGia(loai_xe_id=o_to.id, khung_gio=models.KhungGio.qua_dem_thang, don_gia=1000000),
        ])
        db.commit()

        # Phương tiện + lượt gửi xe mẫu trong 7 ngày gần đây
        # Biển số theo đúng quy tắc: 2 số + 1 chữ + đúng 4 số, ví dụ 29A-1000.
        vi_tri_a = db.query(models.ViTriDo).filter(models.ViTriDo.khu_vuc_id == khu_a.id).all()
        bien_so_mau = [f"29A-{1000+i}" for i in range(8)]
        phuong_tien_list = []
        for bs in bien_so_mau:
            pt = models.PhuongTien(bien_so=bs, loai_xe_id=xe_may.id, chu_xe="Khách vãng lai",
                                    so_dien_thoai="09" + f"{random.randint(0, 99999999):08d}")
            db.add(pt)
            phuong_tien_list.append(pt)
        db.commit()

        # Đơn giá theo hình thức gửi (xe máy) dùng để tính phí demo.
        don_gia_xe_may = {
            models.KhungGio.sang: 3000, models.KhungGio.chieu: 3000,
            models.KhungGio.toi: 4000, models.KhungGio.qua_dem: 5000,
        }

        def hinh_thuc_theo_gio(gio: int) -> models.KhungGio:
            if 6 <= gio < 13:
                return models.KhungGio.sang
            if 13 <= gio < 18:
                return models.KhungGio.chieu
            return models.KhungGio.toi

        now = datetime.utcnow()
        gio_cao_diem = [7, 8, 11, 12, 17, 18]  # giờ cao điểm giả lập
        for ngay_truoc in range(7, 0, -1):
            ngay = now - timedelta(days=ngay_truoc)
            so_luot_trong_ngay = random.randint(6, 14)
            for _ in range(so_luot_trong_ngay):
                gio = random.choice(gio_cao_diem) if random.random() < 0.6 else random.randint(6, 21)
                vao = ngay.replace(hour=gio, minute=random.randint(0, 59), second=0, microsecond=0)
                thoi_luong_phut = random.randint(20, 240)
                ra = vao + timedelta(minutes=thoi_luong_phut)
                pt = random.choice(phuong_tien_list)
                vi_tri = random.choice(vi_tri_a)

                hinh_thuc = hinh_thuc_theo_gio(gio)
                phi = fee.tinh_phi(vao, ra, hinh_thuc, don_gia_xe_may[hinh_thuc])

                luot = models.LuotGuiXe(
                    phuong_tien_id=pt.id, vi_tri_id=vi_tri.id,
                    thoi_gian_vao=vao, thoi_gian_ra=ra, phi_thu=phi,
                    trang_thai=models.TrangThaiLuot.hoan_tat,
                    hinh_thuc_gui=hinh_thuc,
                )
                db.add(luot)
        db.commit()
        print("Đã tạo dữ liệu mẫu thành công.")
        print("Tài khoản Quản lý: quanly / 123456")
        print("Tài khoản Nhân viên: nhanvien / 123456")
    finally:
        db.close()


if __name__ == "__main__":
    run()
