# Hệ thống quản lý bãi đỗ xe có tích hợp AI

Chương trình Python (FastAPI + SQLAlchemy) cài đặt các chức năng nghiệp
vụ (QL-01 → QL-06, QL-08) và 3 chức năng AI (AI-01, AI-02, AI-03) theo
đúng bản báo cáo đề tài (Nhóm 04, đề tài 19). Mặc định dùng SQLite (chạy
ngay không cần cài CSDL); có thể trỏ sang PostgreSQL (VD: Supabase) chỉ
bằng 1 biến môi trường.

## 1. Cài đặt

```bash
cd parking_ai_system
python3 -m venv .venv && source .venv/bin/activate   # (tuỳ chọn)
pip install -r requirements.txt
```

## 2. Tạo dữ liệu mẫu (khuyến nghị để demo ngay)

```bash
python3 -m app.seed
```

Tạo sẵn:
- Tài khoản Quản lý: `quanly` / `123456`
- Tài khoản Nhân viên: `nhanvien` / `123456`
- 2 khu vực, 15 vị trí đỗ, 3 loại xe, bảng giá đầy đủ 6 hình thức gửi xe
  (sáng/chiều/tối/qua đêm/theo tháng/qua đêm theo tháng)
- ~70-90 lượt gửi xe giả lập trong 7 ngày gần nhất (đủ dữ liệu để AI phân tích)

## 3. Chạy chương trình

```bash
uvicorn app.main:app --reload --port 8000
```

Mở trình duyệt tại: **http://127.0.0.1:8000**
- Tài liệu API (Swagger UI): **http://127.0.0.1:8000/docs**

## 4. Cấu hình AI Engine thật (tuỳ chọn, có lựa chọn MIỄN PHÍ)

Mặc định hệ thống dùng bộ sinh báo cáo/nhận xét nội bộ (grounded, chạy
offline, hoàn toàn miễn phí, không cần API key hay Internet) - đủ để
chấm bài / demo ngay không cần cấu hình gì thêm.

Nếu muốn câu trả lời do một LLM thật sinh ra, đặt MỘT trong các biến môi
trường sau trước khi chạy (hệ thống tự dò theo thứ tự Anthropic → OpenAI
→ Groq, không có thì tự rơi về bộ sinh nội bộ):

```bash
export ANTHROPIC_API_KEY="sk-ant-..."   # Claude (trả phí)
# hoặc
export OPENAI_API_KEY="sk-..."          # GPT (trả phí)
# hoặc — LỰA CHỌN MIỄN PHÍ:
export GROQ_API_KEY="gsk_..."           # Groq (có free tier, đăng ký tại console.groq.com)
```

Groq là lựa chọn AI Engine **miễn phí** khuyến nghị: tạo tài khoản tại
https://console.groq.com, vào mục "API Keys" để lấy `GROQ_API_KEY` (không
cần thẻ thanh toán ở gói free tier).

## 5. Chạy kiểm thử (mục 3.4 của báo cáo)

```bash
pytest tests/ -v
```

Bao gồm:
- `test_fee.py`: tính phí theo hình thức gửi xe (theo giờ / theo chu kỳ 30 ngày) (3.4.1)
- `test_nghiep_vu.py`: vào/ra, hết chỗ trống, validate biển số/SĐT, cập nhật trạng thái chỗ trống (3.4.1, 3.4.2)
- `test_ai.py`: xử lý dữ liệu rỗng, tính grounded (không bịa số liệu) của 3 chức năng AI (3.4.3)

## 6. Cấu trúc thư mục

```
app/
  database.py     - kết nối CSDL (SQLite mặc định; đổi DATABASE_URL để dùng PostgreSQL/Supabase)
  models.py       - ORM: nguoi_dung, khu_vuc, vi_tri_do, loai_xe, phuong_tien,
                    luot_gui_xe (có hinh_thuc_gui), bang_gia, lich_su_hoi_dap_ai
  schemas.py      - Pydantic schema + validate biển số (đúng 4 số) và SĐT (10 số, bắt đầu 0)
  security.py     - đăng nhập, phân quyền (QL-01)
  fee.py          - logic tính phí theo hình thức gửi xe đã chọn (QL-04)
  crud.py         - nghiệp vụ danh mục (kể cả tạo vị trí hàng loạt), vào/ra, chỗ trống, tra cứu
  ai_data.py      - pipeline tổng hợp dữ liệu cho AI (thong_ke_luu_luong theo
                    hình thức gửi xe, thong_ke_doanh_thu, ty_le_lap_day)
  ai_engine.py    - prompt engineering + gọi AI Engine (Anthropic/OpenAI/Groq) hoặc bộ sinh nội bộ
  seed.py         - tạo dữ liệu mẫu
  routers/        - các API endpoint (auth, danh_muc, nghiep_vu, thong_ke, ai)
static/           - giao diện web (index.html + app.js) cho các nhóm màn hình (2.5)
tests/            - bộ kiểm thử pytest (3.4)
```

## 7. Đổi hệ quản trị CSDL sang PostgreSQL/Supabase (mục 1.2.3)

Đặt biến môi trường `DATABASE_URL` trước khi chạy, ví dụ:

```bash
export DATABASE_URL="postgresql://postgres:MAT_KHAU@db.xxxxxxxxxxxx.supabase.co:5432/postgres"
```

Không cần sửa code gì thêm - `psycopg2-binary` đã có sẵn trong
`requirements.txt`. Lần chạy đầu tiên, các bảng sẽ tự được tạo
(`Base.metadata.create_all`); chạy `python3 -m app.seed` một lần để có
dữ liệu mẫu trên CSDL mới.

---

## 8. Triển khai lên GitHub + Render + Supabase (miễn phí)

### 8.1. Đẩy code lên GitHub

```bash
cd parking_ai_system
git init
git add .
git commit -m "Hệ thống quản lý bãi đỗ xe có tích hợp AI"
git branch -M main
git remote add origin https://github.com/<tai-khoan-github>/<ten-repo>.git
git push -u origin main
```

(Tạo repo rỗng trên https://github.com/new trước, KHÔNG tick "Add a
README" để tránh xung đột khi push.)

### 8.2. Tạo CSDL trên Supabase (miễn phí)

1. Tạo project mới tại https://supabase.com (gói Free).
2. Vào **Project Settings → Database → Connection string**, chọn tab
   **URI**, copy chuỗi dạng:
   `postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxxxxxxxx.supabase.co:5432/postgres`
3. Thay `[YOUR-PASSWORD]` bằng mật khẩu database bạn đã đặt lúc tạo project.
   Đây chính là giá trị sẽ điền vào biến môi trường `DATABASE_URL` ở bước dưới.

### 8.3. Triển khai lên Render (miễn phí)

1. Đăng nhập https://render.com bằng tài khoản GitHub.
2. **New + → Web Service**, chọn repo vừa đẩy lên GitHub.
3. Render sẽ tự nhận cấu hình từ `render.yaml` (build/start command).
   Nếu tạo thủ công, điền:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1`
4. Ở mục **Environment**, thêm các biến:
   - `DATABASE_URL` = chuỗi kết nối Supabase ở bước 8.2
   - `GROQ_API_KEY` = API key miễn phí lấy ở console.groq.com (tuỳ chọn - bỏ
     qua nếu muốn dùng bộ AI nội bộ miễn phí có sẵn, không cần key)
5. Bấm **Create Web Service**. Sau khi build xong, Render cấp 1 URL dạng
   `https://ten-app.onrender.com` - đây chính là link truy cập hệ thống.
6. Chạy tạo dữ liệu mẫu trên CSDL Supabase (chỉ cần 1 lần, chạy từ máy cá
   nhân với cùng `DATABASE_URL`):
   ```bash
   export DATABASE_URL="postgresql://postgres:...@db.xxxx.supabase.co:5432/postgres"
   python3 -m app.seed
   ```

**Lưu ý:** gói Render Free sẽ "ngủ" sau ~15 phút không có truy cập (lần
truy cập kế tiếp sẽ mất khoảng 30-60 giây để khởi động lại) và hệ thống
lưu phiên đăng nhập trong bộ nhớ (`_ACTIVE_TOKENS` ở `security.py`) nên
mỗi lần Render khởi động lại, người dùng cần đăng nhập lại - đây là giới
hạn hợp lý cho bản đồ án/demo, không phải lỗi.
