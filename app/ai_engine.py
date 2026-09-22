"""
3.3: Cài đặt và tích hợp AI.

Lớp trừu tượng AI Engine: mặc định dùng một bộ sinh văn bản "grounded"
nội bộ (không cần API key, chạy offline - phù hợp để giáo viên chấm bài
mà không cần cấu hình API key). Nếu biến môi trường ANTHROPIC_API_KEY
(hoặc OPENAI_API_KEY) được cấu hình, hệ thống sẽ gọi API AI Engine thật
theo đúng kiến trúc ở mục 2.4.1/2.4.3 (Backend đóng vai trò orchestrator,
tổng hợp dữ liệu -> xây dựng prompt -> gọi AI Engine -> xử lý kết quả).

Ràng buộc bắt buộc (2.1.2 / 1.3.2): AI chỉ được nhận xét trên dữ liệu
được truyền vào prompt (grounded generation), KHÔNG được tự sinh số
liệu; và phải xử lý phù hợp khi dữ liệu rỗng/không đủ (1.3.2, 3.4.3).
"""
import json
import os
from typing import Optional

import requests

SYSTEM_PROMPT = (
    "Bạn là một trợ lý AI quản lý bãi đỗ xe thông minh, thân thiện và chuyên nghiệp.\n"
    "HƯỚNG DẪN TRẢ LỜI:\n"
    "1. Nếu người dùng chào hỏi hoặc xã giao (vd: 'chào bạn', 'hi', 'bạn là ai'), hãy đáp lại thân thiện, lịch sự và giới thiệu ngắn gọn bạn có thể giúp gì cho họ trong việc quản lý bãi xe.\n"
    "2. Khi phân tích, trả lời câu hỏi chuyên môn: Hãy dùng dữ liệu JSON được cung cấp để đưa ra câu trả lời chính xác, rõ ràng, trực diện vào ý người dùng hỏi. Không bịa đặt số liệu không có trong JSON.\n"
    "3. Trình bày ngắn gọn, văn phong tự nhiên, dễ đọc bằng tiếng Việt."
)

THONG_BAO_KHONG_DU_DU_LIEU = (
    "Không đủ dữ liệu trong khoảng thời gian được yêu cầu để AI phân tích. "
    "Vui lòng kiểm tra lại khoảng thời gian hoặc chờ hệ thống ghi nhận thêm "
    "lượt gửi xe trước khi yêu cầu báo cáo/gợi ý."
)


class AIEngineError(Exception):
    pass


def _goi_ai_engine_that(system_prompt: str, user_prompt: str) -> Optional[str]:
    """
    Gọi AI Engine thật qua API nếu có cấu hình API key. Trả về None nếu
    không có API key nào (để rơi về bộ sinh nội bộ - vẫn hoạt động đầy đủ,
    hoàn toàn MIỄN PHÍ, không cần Internet), raise AIEngineError nếu có
    key nhưng lệnh gọi thất bại/timeout (2.4.3: xử lý lỗi AI Engine).

    Thứ tự ưu tiên: ANTHROPIC_API_KEY -> OPENAI_API_KEY -> GROQ_API_KEY.
    GROQ_API_KEY dùng cho Groq (https://console.groq.com) - nhà cung cấp
    có API MIỄN PHÍ (free tier), tương thích định dạng OpenAI, phù hợp khi
    muốn có câu trả lời do LLM thật sinh ra mà không tốn phí.
    """
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")

    try:
        if anthropic_key:
            resp = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": anthropic_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-6",
                    "max_tokens": 700,
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": user_prompt}],
                },
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")

        if openai_key:
            resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "max_tokens": 700,
                },
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

        gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GROQ_API_KEY")
        if gemini_key:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={gemini_key}"
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": f"{system_prompt}\n\nYêu cầu: {user_prompt}"}]
                    }
                ]
            }
            resp = requests.post(url, json=payload, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    except requests.RequestException as exc:
        raise AIEngineError(f"Lỗi khi gọi AI Engine: {exc}") from exc

    return None  # không có API key nào được cấu hình -> dùng bộ sinh nội bộ (miễn phí)


# ---------------------------------------------------------------------------
# AI-01: Sinh báo cáo lưu lượng
# ---------------------------------------------------------------------------

def sinh_bao_cao_luu_luong(du_lieu: dict) -> str:
    from app.ai_data import du_lieu_rong

    if du_lieu_rong(du_lieu):
        return THONG_BAO_KHONG_DU_DU_LIEU

    user_prompt = (
        "Dưới đây là dữ liệu vận hành bãi đỗ xe đã tổng hợp (JSON). Hãy sinh "
        "một báo cáo lưu lượng ngắn gọn: (1) tổng số lượt xe, (2) xu hướng "
        "theo ngày, (3) thời gian gửi xe đông nhất, (4) doanh thu tổng hợp.\n\n"
        f"parking_stats = {json.dumps(du_lieu, ensure_ascii=False)}"
    )

    try:
        ket_qua = _goi_ai_engine_that(SYSTEM_PROMPT, user_prompt)
    except AIEngineError as exc:
        return f"[AI Engine tạm thời không phản hồi] {exc}. Số liệu thô: {json.dumps(du_lieu, ensure_ascii=False)}"

    if ket_qua:
        return ket_qua

    return _bao_cao_luu_luong_noi_bo(du_lieu)


NHAN_HINH_THUC_GUI = {
    "sang": "Sáng (6h-13h)",
    "chieu": "Chiều (13h-18h)",
    "toi": "Tối (18h-6h)",
    "qua_dem": "Gửi qua đêm",
    "thang": "Gửi theo tháng",
    "qua_dem_thang": "Gửi xe qua đêm theo tháng",
}


def _bao_cao_luu_luong_noi_bo(du_lieu: dict) -> str:
    """Bộ sinh báo cáo nội bộ (grounded, không cần API key)."""
    ll = du_lieu["luu_luong"]
    dt = du_lieu["doanh_thu"]
    ld = du_lieu["lap_day"]

    dong_ngay = ", ".join(f"{ngay}: {sl['vao']} lượt vào" for ngay, sl in ll["theo_ngay"].items())
    thoi_gian_dong_nhat = ll.get("thoi_gian_dong_nhat")
    thoi_gian_dong_nhat_str = NHAN_HINH_THUC_GUI.get(thoi_gian_dong_nhat, thoi_gian_dong_nhat) if thoi_gian_dong_nhat else "chưa xác định"

    lap_day_str = "; ".join(
        f"{kv['khu_vuc']}: {kv['da_do']}/{kv['tong_vi_tri']} ({kv['ty_le']*100:.0f}%)"
        for kv in ld["theo_khu_vuc"]
    ) or "chưa có dữ liệu khu vực"

    return (
        f"BÁO CÁO LƯU LƯỢNG\n"
        f"- Tổng số lượt xe trong khoảng thời gian: {ll['tong_so_luot']}.\n"
        f"- Lưu lượng theo ngày: {dong_ngay or 'không có dữ liệu'}.\n"
        f"- Thời gian gửi xe đông nhất trong khoảng thời gian: {thoi_gian_dong_nhat_str}.\n"
        f"- Tổng doanh thu: {dt['tong_doanh_thu']:,.0f} VNĐ.\n"
        f"- Tỷ lệ lấp đầy theo khu vực (hiện tại): {lap_day_str}.\n"
        f"(Báo cáo được sinh trực tiếp từ số liệu tổng hợp, không sử dụng dữ liệu ngoài phạm vi được cung cấp.)"
    )


# ---------------------------------------------------------------------------
# AI-02: Hỏi đáp quản trị (Q&A)
# ---------------------------------------------------------------------------

def hoi_dap_quan_tri(cau_hoi: str, du_lieu: dict) -> str:
    from app.ai_data import du_lieu_rong

    if du_lieu_rong(du_lieu):
        return THONG_BAO_KHONG_DU_DU_LIEU

    user_prompt = (
        f"Câu hỏi của quản lý: \"{cau_hoi}\"\n\n"
        "Hãy trả lời câu hỏi trên CHỈ dựa vào dữ liệu JSON dưới đây, không "
        "bịa thêm số liệu. Nếu dữ liệu không đủ để trả lời chính xác, hãy "
        "nói rõ điều đó.\n\n"
        f"parking_stats = {json.dumps(du_lieu, ensure_ascii=False)}"
    )

    try:
        ket_qua = _goi_ai_engine_that(SYSTEM_PROMPT, user_prompt)
    except AIEngineError as exc:
        return f"[AI Engine tạm thời không phản hồi] {exc}"

    if ket_qua:
        return ket_qua

    return _hoi_dap_noi_bo(cau_hoi, du_lieu)


def _hoi_dap_noi_bo(cau_hoi: str, du_lieu: dict) -> str:
    """Bộ hỏi-đáp nội bộ dựa trên từ khoá + số liệu tổng hợp (grounded)."""
    ll = du_lieu["luu_luong"]
    dt = du_lieu["doanh_thu"]
    ld = du_lieu["lap_day"]
    cau_hoi_lower = cau_hoi.lower()

    if any(tu in cau_hoi_lower for tu in ["đông nhất", "cao điểm", "giờ nào", "khung giờ", "thời gian nào", "hình thức"]):
        hinh_thuc = ll.get("thoi_gian_dong_nhat")
        if hinh_thuc is None:
            return "Chưa có đủ dữ liệu lượt xe để xác định thời gian gửi xe đông nhất."
        nhan = NHAN_HINH_THUC_GUI.get(hinh_thuc, hinh_thuc)
        so_luot = ll["theo_hinh_thuc_gui"].get(hinh_thuc, 0)
        ty_le = ll["ty_le_theo_hinh_thuc_gui"].get(hinh_thuc, 0)
        return f"Thời gian gửi xe đông nhất trong khoảng thời gian được yêu cầu là \"{nhan}\", với {so_luot} lượt xe ({ty_le}% tổng số lượt)."

    if any(tu in cau_hoi_lower for tu in ["doanh thu", "thu được", "tiền"]):
        return f"Tổng doanh thu trong khoảng thời gian được yêu cầu là {dt['tong_doanh_thu']:,.0f} VNĐ."

    if any(tu in cau_hoi_lower for tu in ["lấp đầy", "chỗ trống", "còn trống", "đầy chưa"]):
        if not ld["theo_khu_vuc"]:
            return "Chưa có dữ liệu khu vực để xác định tỷ lệ lấp đầy."
        parts = [f"{kv['khu_vuc']} đang lấp đầy {kv['ty_le']*100:.0f}% ({kv['da_do']}/{kv['tong_vi_tri']} vị trí)" for kv in ld["theo_khu_vuc"]]
        return "; ".join(parts) + "."

    if any(tu in cau_hoi_lower for tu in ["tổng số lượt", "bao nhiêu lượt", "bao nhiêu xe"]):
        return f"Tổng số lượt xe trong khoảng thời gian được yêu cầu là {ll['tong_so_luot']} lượt."

    return (
        "Dựa trên dữ liệu hiện có: tổng số lượt xe là "
        f"{ll['tong_so_luot']}, tổng doanh thu là {dt['tong_doanh_thu']:,.0f} VNĐ. "
        "Vui lòng đặt câu hỏi cụ thể hơn (ví dụ về khung giờ, doanh thu, hoặc tỷ lệ lấp đầy) để nhận câu trả lời chi tiết hơn."
    )


# ---------------------------------------------------------------------------
# AI-03: Gợi ý bố trí nhân sự
# ---------------------------------------------------------------------------

def goi_y_bo_tri_nhan_su(du_lieu: dict) -> str:
    from app.ai_data import du_lieu_rong

    if du_lieu_rong(du_lieu):
        return THONG_BAO_KHONG_DU_DU_LIEU

    user_prompt = (
        "Dựa trên số liệu lưu lượng theo thời gian gửi xe dưới đây, hãy đề "
        "xuất số lượng và thời điểm bố trí nhân viên trực bãi xe hợp lý, "
        "trình bày theo từng hình thức gửi xe (sáng/chiều/tối/qua đêm/theo "
        "tháng).\n\n"
        f"parking_stats = {json.dumps(du_lieu, ensure_ascii=False)}"
    )

    try:
        ket_qua = _goi_ai_engine_that(SYSTEM_PROMPT, user_prompt)
    except AIEngineError as exc:
        return f"[AI Engine tạm thời không phản hồi] {exc}"

    if ket_qua:
        return ket_qua

    return _goi_y_nhan_su_noi_bo(du_lieu)


def _goi_y_nhan_su_noi_bo(du_lieu: dict) -> str:
    theo_hinh_thuc = du_lieu["luu_luong"]["theo_hinh_thuc_gui"]
    if not theo_hinh_thuc:
        return "Chưa có dữ liệu lưu lượng theo thời gian gửi xe để đưa ra gợi ý bố trí nhân sự."

    max_luot = max(theo_hinh_thuc.values()) or 1
    goi_y = []
    for hinh_thuc, so_luot in sorted(theo_hinh_thuc.items(), key=lambda kv: -kv[1]):
        nhan = NHAN_HINH_THUC_GUI.get(hinh_thuc, hinh_thuc)
        ty_le = so_luot / max_luot
        if ty_le >= 0.75:
            so_nv = 3
        elif ty_le >= 0.4:
            so_nv = 2
        else:
            so_nv = 1
        goi_y.append(f"{nhan}: {so_luot} lượt xe -> đề xuất bố trí {so_nv} nhân viên trực.")

    return "GỢI Ý BỐ TRÍ NHÂN SỰ\n" + "\n".join(goi_y) + (
        "\n(Gợi ý dựa trên tỷ lệ lưu lượng tương đối giữa các thời gian gửi xe, "
        "quản lý có thể điều chỉnh theo thực tế nhân sự hiện có.)"
    )
