const API = "";
let TOKEN = localStorage.getItem("token") || "";
let VAI_TRO = localStorage.getItem("vai_tro") || "";
let HO_TEN = localStorage.getItem("ho_ten") || "";

function authHeaders(extra = {}) {
  return TOKEN ? { ...extra, Authorization: "Bearer " + TOKEN } : extra;
}

async function apiFetch(path, options = {}) {
  const res = await fetch(API + path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(options.headers || {}),
    },
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || "Lỗi không xác định");
  return data;
}

function showMsg(elId, text, ok = true) {
  const el = document.getElementById(elId);
  el.className = "msg " + (ok ? "ok" : "bad");
  el.textContent = text;
}

// ---------- Đăng nhập ----------
async function dangNhap() {
  const tai_khoan = document.getElementById("li-user").value.trim();
  const mat_khau = document.getElementById("li-pass").value;
  try {
    const data = await apiFetch("/api/auth/dang-nhap", {
      method: "POST",
      body: JSON.stringify({ tai_khoan, mat_khau }),
    });
    TOKEN = data.access_token; VAI_TRO = data.vai_tro; HO_TEN = data.ho_ten;
    localStorage.setItem("token", TOKEN);
    localStorage.setItem("vai_tro", VAI_TRO);
    localStorage.setItem("ho_ten", HO_TEN);
    initApp();
  } catch (e) {
    showMsg("li-msg", e.message, false);
  }
}

function dangXuat() {
  localStorage.clear();
  location.reload();
}

function showLoginPanel(panelId) {
  document.querySelectorAll(".auth-panel").forEach(p => p.classList.add("hidden"));
  document.getElementById(panelId).classList.remove("hidden");
  document.querySelectorAll(".login-tab").forEach(b => b.classList.remove("active"));
  document.getElementById(panelId === "login-panel" ? "login-tab-btn" : "register-tab-btn").classList.add("active");
}

async function dangKyTaiKhoan(mode = "register") {
  const prefix = mode === "register" ? "reg" : "acc";
  const ho_ten = document.getElementById(`${prefix}-name`).value.trim();
  const tai_khoan = document.getElementById(`${prefix}-user`).value.trim();
  const mat_khau = document.getElementById(`${prefix}-pass`).value;
  const vai_tro = document.getElementById(`${prefix}-role`).value;
  const pass2 = mode === "register" ? document.getElementById("reg-pass2").value : null;
  const msgId = mode === "register" ? "reg-msg" : "msg-taikhoan";
  if (!ho_ten || !tai_khoan || !mat_khau) return showMsg(msgId, "Vui lòng nhập đủ thông tin.", false);
  if (mode === "register" && mat_khau !== pass2) return showMsg(msgId, "Mật khẩu nhập lại không khớp.", false);
  try {
    await apiFetch("/api/auth/dang-ky", { method: "POST", body: JSON.stringify({ ho_ten, tai_khoan, mat_khau, vai_tro }) });
    showMsg(msgId, `Đã tạo tài khoản ${tai_khoan}.`);
    [prefix === "reg" ? "reg-name" : "acc-name", prefix === "reg" ? "reg-user" : "acc-user", prefix === "reg" ? "reg-pass" : "acc-pass"].forEach(id => { const e = document.getElementById(id); if (e) e.value = ""; });
    if (mode === "register") document.getElementById("reg-pass2").value = "";
  } catch (e) {
    showMsg(msgId, e.message, false);
  }
}

function setActiveNav(button) {
  document.querySelectorAll("#nav-home-slot button[data-nav], #nav-tabs button[data-nav]").forEach(b => b.classList.remove("active"));
  if (button) button.classList.add("active");
}

// Icon con trỏ chuột lấp lánh, gợi ý người dùng bấm vào nhóm "Trợ lý AI"
// từ trang chủ. Chỉ hiện khi: đang ở trang chủ + là quản lý + người dùng
// chưa từng tương tác với nhóm đó (ghi nhớ trong localStorage để không làm phiền mãi).
function taoConTroGoiY() {
  const wrap = document.createElement("span");
  wrap.className = "nav-hint-pointer";
  wrap.setAttribute("aria-hidden", "true");
  wrap.innerHTML =
    '<svg class="hint-cursor" viewBox="0 0 24 24"><path d="M4 2 L4 20.5 L8.7 16.2 L11.6 22.3 L14.6 20.9 L11.7 14.7 L18 14 Z"/></svg>' +
    '<span class="hint-spark s1">✦</span><span class="hint-spark s2">✧</span>';
  return wrap;
}

function batTatGoiYTroLyAI(hienThi) {
  document.body.classList.toggle("hint-ai-active", !!hienThi);
}

function danhDauDaXemGoiY() {
  try { localStorage.setItem("hint_ai_dismissed", "1"); } catch (_) {}
  batTatGoiYTroLyAI(false);
}

function toggleNavGroup(headingEl, listEl) {
  const dangMo = headingEl.getAttribute("aria-expanded") !== "false";
  headingEl.setAttribute("aria-expanded", String(!dangMo));
  listEl.classList.toggle("collapsed", dangMo);
}

// Header (PARKING AI) giờ cố định trên cùng, cột chức năng cố định bên trái
// nối liền ngay dưới header - đo chiều cao thật của header để 2 khối luôn
// khít nhau, không lệch dù nội dung header đổi dòng ở màn hình nhỏ.
function capNhatChieuCaoHeader() {
  const header = document.querySelector("#app > header");
  if (header) document.documentElement.style.setProperty("--header-h", header.offsetHeight + "px");
}
window.addEventListener("resize", capNhatChieuCaoHeader);

function buildNav() {
  const homeSlot = document.getElementById("nav-home-slot");
  const nav = document.getElementById("nav-tabs");
  homeSlot.innerHTML = "";
  nav.innerHTML = "";
  // Nút "Trang chủ" nằm ở phần cố định riêng (nav-home-slot), tách khỏi
  // #nav-tabs - nhờ vậy chỉ phần từ "Nghiệp vụ" trở xuống mới cuộn được,
  // còn tiêu đề + nút Trang chủ luôn cố định phía trên.
  const home = document.createElement("button");
  home.className = "nav-home active";
  home.dataset.nav = "home";
  home.innerHTML = "<span class='nav-icon'>⌂</span><span>Trang chủ</span>";
  home.onclick = () => showTab("tab-home", home);
  homeSlot.appendChild(home);

  // Mỗi nhóm chức năng có tiêu đề bấm được để ẩn/hiện các chức năng con
  // (mũi tên chữ V xoay khi thu gọn), tránh cột chức năng quá dài.
  const addGroup = (title, items, parentId, opts = {}) => {
    const group = document.createElement("div");
    group.className = "nav-group";

    const heading = document.createElement("button");
    heading.type = "button";
    heading.className = "nav-group-title";
    heading.setAttribute("aria-expanded", "true");
    heading.innerHTML = `<span class="nav-group-label">${title}</span><span class="nav-chevron">▾</span>`;

    const listOuter = document.createElement("div");
    listOuter.className = "nav-group-list";
    const listInner = document.createElement("div");
    listInner.className = "nav-group-list-inner";
    listOuter.appendChild(listInner);

    heading.onclick = () => {
      toggleNavGroup(heading, listOuter);
      if (opts.hint) danhDauDaXemGoiY();
    };
    group.appendChild(heading);

    items.forEach(([label, cardId]) => {
      const btn = document.createElement("button");
      btn.className = "nav-child";
      btn.dataset.nav = cardId;
      const labelSpan = document.createElement("span");
      labelSpan.textContent = label;
      btn.appendChild(labelSpan);
      btn.onclick = () => {
        showSub(parentId, cardId, btn);
        if (opts.hint) danhDauDaXemGoiY();
      };
      listInner.appendChild(btn);
    });
    group.appendChild(listOuter);
    nav.appendChild(group);
  };

  addGroup("Nghiệp vụ", [["Ghi nhận xe vào", "card-xevao"], ["Ghi nhận xe ra / tính phí", "card-xera"], ["Xem chỗ trống", "card-chotrong"], ["Tra cứu lượt gửi", "card-tracuu"]], "tab-nghiepvu");
  if (VAI_TRO === "quan_ly") {
    addGroup("Quản trị & thống kê", [["Danh mục vận hành", "card-danhmuc"], ["Lưu lượng & doanh thu", "card-thongke"]], "tab-quantri");
    addGroup("Trợ lý AI", [["Báo cáo lưu lượng", "card-aibaocao"], ["Hỏi đáp quản trị", "card-aihoidap"], ["Gợi ý bố trí nhân sự", "card-ainhansu"], ["Lịch sử hỏi đáp", "card-ailichsu"]], "tab-ai", { hint: true });
    addGroup("Tài khoản", [["Tạo quản lý / nhân viên", "card-taikhoan"]], "tab-taikhoan");
    gomIconGoiYVaoTrangChu();
    if (!localStorage.getItem("hint_ai_dismissed")) batTatGoiYTroLyAI(true);
  }
}

// Icon gợi ý được gắn ngay trên nút "Trợ lý AI" ở trang chủ (không nằm
// trong cột chức năng), vì icon này chỉ có ý nghĩa khi người dùng đang ở
// trang chủ và đang nhìn thấy các lối tắt (quick actions).
function gomIconGoiYVaoTrangChu() {
  const nutTrangChu = document.getElementById("qa-trolyai");
  if (!nutTrangChu || nutTrangChu.querySelector(".nav-hint-pointer")) return;
  nutTrangChu.appendChild(taoConTroGoiY());
  nutTrangChu.addEventListener("click", danhDauDaXemGoiY);
}

function animatePage(page) {
  page.classList.remove("page-enter");
  void page.offsetWidth;
  page.classList.add("page-enter");
  page.querySelectorAll(":scope > .card").forEach((card, i) => {
    card.style.setProperty("--stagger", `${i * 55}ms`);
    card.classList.remove("card-rise");
    void card.offsetWidth;
    card.classList.add("card-rise");
  });
}

function initApp() {
  document.getElementById("login-box").classList.add("hidden");
  document.getElementById("app").classList.remove("hidden");
  document.getElementById("whoami").textContent = `${HO_TEN} (${VAI_TRO === "quan_ly" ? "Quản lý" : "Nhân viên"})`;
  buildNav();
  showTab("tab-home", document.querySelector("#nav-home-slot .nav-home"), false);
  taiDanhMuc();
  taiChoTrong();
  taiTongQuanTrangChu();
  loadHomeImage();
  requestAnimationFrame(capNhatChieuCaoHeader);
}

function showTab(id, btnEl, animate = true) {
  document.querySelectorAll(".tabpage").forEach(el => el.classList.add("hidden"));
  const page = document.getElementById(id);
  if (!page) return;
  page.classList.remove("hidden");
  setActiveNav(btnEl);
  if (animate) animatePage(page);
  // Icon gợi ý (mũi tên lấp lánh) chỉ có ý nghĩa khi đang ở trang chủ.
  document.body.classList.toggle("home-active", id === "tab-home");
  if (id === "tab-home") taiTongQuanTrangChu();
}

function showSub(parentId, cardId, btnEl) {
  const page = document.getElementById(parentId);
  if (!page) return;
  document.querySelectorAll(".tabpage").forEach(el => el.classList.add("hidden"));
  page.classList.remove("hidden");
  setActiveNav(btnEl);
  document.body.classList.remove("home-active");
  // Chỉ hiện đúng 1 chức năng con được chọn, ẩn các chức năng con khác cùng nhóm
  // (tiêu đề nhóm ".page-intro" vẫn hiện để giữ ngữ cảnh đang ở mục nào).
  page.querySelectorAll(".subpage-card").forEach(c => {
    c.classList.toggle("hidden", c.id !== cardId);
  });
  animatePage(page);
  window.scrollTo({ top: 0, behavior: "smooth" });
  // Tải dữ liệu chi tiết ngay khi mở mục con tương ứng.
  if (cardId === "card-chotrong") taiChoTrong();
}

function handleHomeImage(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  if (!file.type.startsWith("image/")) return;
  const reader = new FileReader();
  reader.onload = e => {
    const dataUrl = e.target.result;
    try { localStorage.setItem("parking_home_image", dataUrl); } catch (_) {}
    applyHomeImage(dataUrl);
  };
  reader.readAsDataURL(file);
}

function applyHomeImage(dataUrl) {
  const wrap = document.querySelector(".hero-media");
  const img = document.getElementById("home-image");
  if (!wrap || !img) return;
  if (dataUrl) { img.src = dataUrl; wrap.classList.add("has-image"); }
  else { wrap.classList.remove("has-image"); img.removeAttribute("src"); }
}

function loadHomeImage() {
  applyHomeImage(localStorage.getItem("parking_home_image") || "");
}

async function taiTongQuanTrangChu() {
  const view = document.getElementById("home-occupancy");
  const noticeView = document.getElementById("home-notices");
  try {
    const data = await apiFetch("/api/cho-trong");
    if (view) {
      view.innerHTML = data.length ? data.slice(0, 5).map(kv => `<div class="dashboard-item"><div><b>${kv.ten_khu_vuc}</b><small>${kv.tong_so_vi_tri} vị trí</small></div><strong>${kv.so_cho_trong} chỗ trống</strong></div>`).join("") : "<div class='muted'>Chưa có dữ liệu khu vực.</div>";
    }
    if (noticeView) noticeView.innerHTML = xayThongBaoTrangChu(data).join("") || "<div class='muted'>Chưa có thông báo nào.</div>";
  } catch (_) {
    if (view) view.innerHTML = "<div class='muted'>Chưa tải được dữ liệu tổng quan.</div>";
    if (noticeView) noticeView.innerHTML = `<div class="notice"><span class="notice-dot warn"></span><div><b>Không tải được dữ liệu</b><small>Kiểm tra kết nối rồi thử lại.</small></div></div>`;
  }
}

// Sinh thông báo "phù hợp" dựa trên dữ liệu chỗ trống thật thay vì nội dung
// tĩnh: cảnh báo khu vực sắp hết chỗ, và trạng thái chung của hệ thống.
function xayThongBaoTrangChu(data) {
  const notices = [];
  const tongTrong = data.reduce((s, kv) => s + kv.so_cho_trong, 0);
  const tongViTri = data.reduce((s, kv) => s + kv.tong_so_vi_tri, 0);
  notices.push(`<div class="notice"><span class="notice-dot ok"></span><div><b>Hệ thống hoạt động</b><small>${tongTrong}/${tongViTri} vị trí còn trống trên toàn bãi.</small></div></div>`);

  data.forEach(kv => {
    if (kv.tong_so_vi_tri === 0) return;
    const tyLe = kv.so_cho_trong / kv.tong_so_vi_tri;
    if (tyLe === 0) {
      notices.push(`<div class="notice"><span class="notice-dot warn"></span><div><b>${escapeHtml(kv.ten_khu_vuc)} đã hết chỗ</b><small>Cân nhắc điều tiết xe sang khu vực khác.</small></div></div>`);
    } else if (tyLe <= 0.2) {
      notices.push(`<div class="notice"><span class="notice-dot warn"></span><div><b>${escapeHtml(kv.ten_khu_vuc)} sắp hết chỗ</b><small>Chỉ còn ${kv.so_cho_trong}/${kv.tong_so_vi_tri} vị trí trống.</small></div></div>`);
    }
  });

  notices.push(`<div class="notice"><span class="notice-dot"></span><div><b>Báo cáo định kỳ</b><small>Có thể sinh báo cáo lưu lượng bằng AI trong mục Trợ lý AI.</small></div></div>`);
  return notices.slice(0, 5);
}

function formatPhutDaDo(phut) {
  if (phut == null) return "-";
  const gio = Math.floor(phut / 60), du = phut % 60;
  return gio > 0 ? `${gio} giờ ${du} phút` : `${du} phút`;
}

function formatThoiGian(iso) {
  if (!iso) return "-";
  try {
    return new Date(iso).toLocaleString("vi-VN", { hour: "2-digit", minute: "2-digit", day: "2-digit", month: "2-digit" });
  } catch (_) { return iso; }
}

// ---------- Danh mục ----------
let _khuVucCache = [], _loaiXeCache = [];

async function taiDanhMuc() {
  try {
    const [khuVuc, loaiXe, viTri, bangGia] = await Promise.all([
      apiFetch("/api/danh-muc/khu-vuc"),
      apiFetch("/api/danh-muc/loai-xe"),
      apiFetch("/api/danh-muc/vi-tri"),
      apiFetch("/api/danh-muc/bang-gia"),
    ]);
    _khuVucCache = khuVuc; _loaiXeCache = loaiXe;

    fillSelect("in-khuvuc", khuVuc, "id", "ten_khu_vuc");
    fillSelect("dm-vitri-khuvuc", khuVuc, "id", "ten_khu_vuc");
    fillSelect("in-loaixe", loaiXe, "id", "ten_loai_xe");
    fillSelect("dm-gia-loaixe", loaiXe, "id", "ten_loai_xe");
    fillSelectWithPlaceholder("tc-khuvuc", khuVuc, "id", "ten_khu_vuc", "— Mọi khu vực —");
    fillSelectWithPlaceholder("tc-loaixe", loaiXe, "id", "ten_loai_xe", "— Mọi loại xe —");
    dienSelectHinhThucGui("in-hinhthuc", null);
    dienSelectHinhThucGui("out-hinhthuc", "— Giữ nguyên hình thức lúc gửi xe —");
    dienSelectHinhThucGui("dm-gia-khung", null);
    if (khuVuc.length) taiViTriTrong();

    renderKhuVucList(khuVuc);
    renderLoaiXeList(loaiXe);
    renderViTriList(viTri, khuVuc, loaiXe);
    renderBangGiaList(bangGia, loaiXe);
  } catch (e) { console.error(e); }
}

function fillSelect(id, items, valueKey, labelKey) {
  const el = document.getElementById(id);
  if (!el) return;
  const giaTriDangChon = el.value;
  el.innerHTML = items.map(it => `<option value="${it[valueKey]}">${it[labelKey]}</option>`).join("");
  // Giữ nguyên lựa chọn cũ sau khi làm mới danh sách (nếu vẫn còn tồn tại),
  // tránh việc select bị nhảy về mục đầu tiên mỗi khi thêm vị trí/bảng giá mới.
  if (giaTriDangChon && items.some(it => String(it[valueKey]) === giaTriDangChon)) {
    el.value = giaTriDangChon;
  }
}

function fillSelectWithPlaceholder(id, items, valueKey, labelKey, placeholder) {
  const el = document.getElementById(id);
  if (!el) return;
  el.innerHTML = `<option value="">${placeholder}</option>` + items.map(it => `<option value="${it[valueKey]}">${escapeHtml(it[labelKey])}</option>`).join("");
}

const KHUNG_GIO_LABEL = {
  sang: "Sáng (6h-13h)",
  chieu: "Chiều (13h-18h)",
  toi: "Tối (18h-6h)",
  qua_dem: "Gửi qua đêm",
  thang: "Gửi theo tháng (30 ngày)",
  qua_dem_thang: "Gửi xe qua đêm theo tháng (30 ngày)",
};

// Điền các select "thời gian gửi xe" (xe vào, xe ra, bảng giá) bằng danh
// sách cố định KHUNG_GIO_LABEL - không cần gọi API vì đây là tập cố định.
function dienSelectHinhThucGui(id, coPlaceholder) {
  const el = document.getElementById(id);
  if (!el) return;
  const giaTriDangChon = el.value;
  const options = Object.entries(KHUNG_GIO_LABEL).map(([k, label]) => `<option value="${k}">${label}</option>`).join("");
  el.innerHTML = (coPlaceholder ? `<option value="">${coPlaceholder}</option>` : "") + options;
  if (giaTriDangChon) el.value = giaTriDangChon;
}

// ----- Khu vực: sửa / xoá -----
function renderKhuVucList(items) {
  const el = document.getElementById("list-khuvuc");
  if (!el) return;
  el.innerHTML = items.map(kv => `
    <div class="manage-row" data-id="${kv.id}">
      <input class="mr-ten" value="${escapeHtml(kv.ten_khu_vuc)}" placeholder="Tên khu vực">
      <input class="mr-mota" value="${escapeHtml(kv.mo_ta || "")}" placeholder="Mô tả (tuỳ chọn)">
      <div class="manage-row-actions">
        <button class="btn secondary" onclick="suaKhuVuc(${kv.id}, this)">Lưu</button>
        <button class="btn danger" onclick="xoaKhuVuc(${kv.id})">Xoá</button>
      </div>
    </div>`).join("") || "<p class='muted'>Chưa có khu vực nào.</p>";
}
async function suaKhuVuc(id, btnEl) {
  const row = btnEl.closest(".manage-row");
  const ten_khu_vuc = row.querySelector(".mr-ten").value.trim();
  const mo_ta = row.querySelector(".mr-mota").value.trim() || null;
  if (!ten_khu_vuc) return showMsg("msg-danhmuc", "Tên khu vực không được để trống.", false);
  try {
    await apiFetch(`/api/danh-muc/khu-vuc/${id}`, { method: "PUT", body: JSON.stringify({ ten_khu_vuc, mo_ta }) });
    showMsg("msg-danhmuc", "Đã cập nhật khu vực."); taiDanhMuc(); taiChoTrong();
  } catch (e) { showMsg("msg-danhmuc", e.message, false); }
}
async function xoaKhuVuc(id) {
  if (!confirm("Xoá khu vực này? Cần xoá hết vị trí đỗ bên trong trước.")) return;
  try {
    await apiFetch(`/api/danh-muc/khu-vuc/${id}`, { method: "DELETE" });
    showMsg("msg-danhmuc", "Đã xoá khu vực."); taiDanhMuc(); taiChoTrong();
  } catch (e) { showMsg("msg-danhmuc", e.message, false); }
}

// ----- Loại xe: sửa / xoá -----
function renderLoaiXeList(items) {
  const el = document.getElementById("list-loaixe");
  if (!el) return;
  el.innerHTML = items.map(lx => `
    <div class="manage-row" data-id="${lx.id}" style="grid-template-columns:1fr auto">
      <input class="mr-ten" value="${escapeHtml(lx.ten_loai_xe)}" placeholder="Tên loại xe">
      <div class="manage-row-actions">
        <button class="btn secondary" onclick="suaLoaiXe(${lx.id}, this)">Lưu</button>
        <button class="btn danger" onclick="xoaLoaiXe(${lx.id})">Xoá</button>
      </div>
    </div>`).join("") || "<p class='muted'>Chưa có loại xe nào.</p>";
}
async function suaLoaiXe(id, btnEl) {
  const row = btnEl.closest(".manage-row");
  const ten_loai_xe = row.querySelector(".mr-ten").value.trim();
  if (!ten_loai_xe) return showMsg("msg-danhmuc", "Tên loại xe không được để trống.", false);
  try {
    await apiFetch(`/api/danh-muc/loai-xe/${id}`, { method: "PUT", body: JSON.stringify({ ten_loai_xe }) });
    showMsg("msg-danhmuc", "Đã cập nhật loại xe."); taiDanhMuc();
  } catch (e) { showMsg("msg-danhmuc", e.message, false); }
}
async function xoaLoaiXe(id) {
  if (!confirm("Xoá loại xe này?")) return;
  try {
    await apiFetch(`/api/danh-muc/loai-xe/${id}`, { method: "DELETE" });
    showMsg("msg-danhmuc", "Đã xoá loại xe."); taiDanhMuc();
  } catch (e) { showMsg("msg-danhmuc", e.message, false); }
}

// ----- Vị trí đỗ: sửa / xoá -----
function renderViTriList(items, khuVuc, loaiXe) {
  const el = document.getElementById("list-vitri");
  if (!el) return;
  const tenKhuVuc = id => khuVuc.find(k => k.id === id)?.ten_khu_vuc || `#${id}`;
  const optionsLoaiXe = current => `<option value="">— Mọi loại xe —</option>` + loaiXe.map(lx => `<option value="${lx.id}" ${current === lx.id ? "selected" : ""}>${escapeHtml(lx.ten_loai_xe)}</option>`).join("");
  el.innerHTML = items.map(vt => `
    <div class="manage-row" data-id="${vt.id}" style="grid-template-columns:.8fr 1fr 1fr auto">
      <span class="muted">${escapeHtml(tenKhuVuc(vt.khu_vuc_id))} <span class="badge ${vt.trang_thai}">${vt.trang_thai === "trong" ? "Trống" : "Đã đỗ"}</span></span>
      <input class="mr-ma" value="${escapeHtml(vt.ma_vi_tri)}" placeholder="Mã vị trí">
      <select class="mr-loaixe">${optionsLoaiXe(vt.loai_xe_cho_phep)}</select>
      <div class="manage-row-actions">
        <button class="btn secondary" onclick="suaViTri(${vt.id}, this)">Lưu</button>
        <button class="btn danger" onclick="xoaViTriDanhMuc(${vt.id})">Xoá</button>
      </div>
    </div>`).join("") || "<p class='muted'>Chưa có vị trí nào.</p>";
}
async function suaViTri(id, btnEl) {
  const row = btnEl.closest(".manage-row");
  const ma_vi_tri = row.querySelector(".mr-ma").value.trim();
  const loaiXeVal = row.querySelector(".mr-loaixe").value;
  if (!ma_vi_tri) return showMsg("msg-danhmuc", "Mã vị trí không được để trống.", false);
  try {
    await apiFetch(`/api/danh-muc/vi-tri/${id}`, { method: "PUT", body: JSON.stringify({ ma_vi_tri, loai_xe_cho_phep: loaiXeVal ? Number(loaiXeVal) : null }) });
    showMsg("msg-danhmuc", "Đã cập nhật vị trí."); taiDanhMuc(); taiChoTrong();
  } catch (e) { showMsg("msg-danhmuc", e.message, false); }
}
async function xoaViTriDanhMuc(id) {
  if (!confirm("Xoá vị trí đỗ này?")) return;
  try {
    await apiFetch(`/api/danh-muc/vi-tri/${id}`, { method: "DELETE" });
    showMsg("msg-danhmuc", "Đã xoá vị trí."); taiDanhMuc(); taiChoTrong();
  } catch (e) { showMsg("msg-danhmuc", e.message, false); }
}

// ----- Bảng giá: sửa / xoá -----
function renderBangGiaList(items, loaiXe) {
  const el = document.getElementById("list-banggia");
  if (!el) return;
  const optionsLoaiXe = current => loaiXe.map(lx => `<option value="${lx.id}" ${current === lx.id ? "selected" : ""}>${escapeHtml(lx.ten_loai_xe)}</option>`).join("");
  const optionsKhung = current => Object.entries(KHUNG_GIO_LABEL).map(([k, label]) => `<option value="${k}" ${current === k ? "selected" : ""}>${label}</option>`).join("");
  el.innerHTML = items.map(bg => `
    <div class="manage-row" data-id="${bg.id}" style="grid-template-columns:1fr 1fr 1fr auto">
      <select class="mr-loaixe">${optionsLoaiXe(bg.loai_xe_id)}</select>
      <select class="mr-khung">${optionsKhung(bg.khung_gio)}</select>
      <input class="mr-gia" type="number" value="${bg.don_gia}" placeholder="Đơn giá">
      <div class="manage-row-actions">
        <button class="btn secondary" onclick="suaBangGia(${bg.id}, this)">Lưu</button>
        <button class="btn danger" onclick="xoaBangGiaDanhMuc(${bg.id})">Xoá</button>
      </div>
    </div>`).join("") || "<p class='muted'>Chưa có bảng giá nào.</p>";
}
async function suaBangGia(id, btnEl) {
  const row = btnEl.closest(".manage-row");
  const loai_xe_id = Number(row.querySelector(".mr-loaixe").value);
  const khung_gio = row.querySelector(".mr-khung").value;
  const don_gia = Number(row.querySelector(".mr-gia").value);
  try {
    await apiFetch(`/api/danh-muc/bang-gia/${id}`, { method: "PUT", body: JSON.stringify({ loai_xe_id, khung_gio, don_gia }) });
    showMsg("msg-danhmuc", "Đã cập nhật bảng giá."); taiDanhMuc();
  } catch (e) { showMsg("msg-danhmuc", e.message, false); }
}
async function xoaBangGiaDanhMuc(id) {
  if (!confirm("Xoá bảng giá này?")) return;
  try {
    await apiFetch(`/api/danh-muc/bang-gia/${id}`, { method: "DELETE" });
    showMsg("msg-danhmuc", "Đã xoá bảng giá."); taiDanhMuc();
  } catch (e) { showMsg("msg-danhmuc", e.message, false); }
}

async function taiViTriTrong() {
  const khuVucId = document.getElementById("in-khuvuc").value;
  if (!khuVucId) return;
  const viTri = await apiFetch(`/api/danh-muc/vi-tri?khu_vuc_id=${khuVucId}`);
  const trong = viTri.filter(v => v.trang_thai === "trong");
  fillSelect("in-vitri", trong, "id", "ma_vi_tri");
}

async function themKhuVuc() {
  try {
    await apiFetch("/api/danh-muc/khu-vuc", { method: "POST", body: JSON.stringify({ ten_khu_vuc: document.getElementById("dm-khuvuc-ten").value }) });
    showMsg("msg-danhmuc", "Đã thêm khu vực."); taiDanhMuc();
  } catch (e) { showMsg("msg-danhmuc", e.message, false); }
}
async function themLoaiXe() {
  try {
    await apiFetch("/api/danh-muc/loai-xe", { method: "POST", body: JSON.stringify({ ten_loai_xe: document.getElementById("dm-loaixe-ten").value }) });
    showMsg("msg-danhmuc", "Đã thêm loại xe."); taiDanhMuc();
  } catch (e) { showMsg("msg-danhmuc", e.message, false); }
}
async function themViTri() {
  try {
    await apiFetch("/api/danh-muc/vi-tri", {
      method: "POST",
      body: JSON.stringify({ khu_vuc_id: Number(document.getElementById("dm-vitri-khuvuc").value), ma_vi_tri: document.getElementById("dm-vitri-ma").value }),
    });
    showMsg("msg-danhmuc", "Đã thêm vị trí.");
    document.getElementById("dm-vitri-ma").value = "";
    // Trước đây chỉ gọi taiChoTrong() nên danh sách "Vị trí đỗ hiện có" ở
    // mục Danh mục không cập nhật, khiến việc tạo mới trông như bị lỗi.
    taiDanhMuc(); taiChoTrong();
  } catch (e) { showMsg("msg-danhmuc", e.message, false); }
}

// Tạo nhanh 10/50/100 vị trí theo chữ cái đầu (VD: "A" -> A1, A2, ..., An).
// Backend tự bỏ qua các mã đã tồn tại sẵn trong khu vực để không trùng tên.
async function themViTriHangLoat(soLuong) {
  const khuVucId = Number(document.getElementById("dm-vitri-khuvuc").value);
  const tienTo = document.getElementById("dm-vitri-tienlo").value.trim();
  if (!khuVucId) return showMsg("msg-danhmuc", "Vui lòng chọn khu vực trước.", false);
  if (!tienTo) return showMsg("msg-danhmuc", "Vui lòng nhập chữ cái đầu, ví dụ: A.", false);
  try {
    const data = await apiFetch("/api/danh-muc/vi-tri/hang-loat", {
      method: "POST",
      body: JSON.stringify({ khu_vuc_id: khuVucId, tien_to: tienTo, so_luong: soLuong }),
    });
    const trung = data.bi_trung.length ? ` (bỏ qua ${data.bi_trung.length} mã đã tồn tại: ${data.bi_trung.slice(0, 6).join(", ")}${data.bi_trung.length > 6 ? "..." : ""})` : "";
    showMsg("msg-danhmuc", `Đã tạo thêm ${data.so_luong_da_tao} vị trí (${tienTo}1 → ${tienTo}${soLuong})${trung}.`, data.so_luong_da_tao > 0);
    taiDanhMuc(); taiChoTrong();
  } catch (e) { showMsg("msg-danhmuc", e.message, false); }
}
async function themBangGia() {
  try {
    await apiFetch("/api/danh-muc/bang-gia", {
      method: "POST",
      body: JSON.stringify({
        loai_xe_id: Number(document.getElementById("dm-gia-loaixe").value),
        khung_gio: document.getElementById("dm-gia-khung").value,
        don_gia: Number(document.getElementById("dm-gia-dongia").value),
      }),
    });
    showMsg("msg-danhmuc", "Đã thêm bảng giá.");
    document.getElementById("dm-gia-dongia").value = "";
    // Trước đây không gọi lại taiDanhMuc() nên danh sách "Bảng giá hiện có"
    // không bao giờ hiện mục vừa tạo, khiến việc tạo mới trông như bị lỗi.
    taiDanhMuc();
  } catch (e) { showMsg("msg-danhmuc", e.message, false); }
}

// ---------- Xe vào / ra ----------
async function xeVao() {
  const bienSo = document.getElementById("in-bienso-vao").value.trim();
  const loaiXeId = document.getElementById("in-loaixe").value;
  const khuVucId = document.getElementById("in-khuvuc").value;
  const viTriId = document.getElementById("in-vitri").value;
  const hinhThuc = document.getElementById("in-hinhthuc").value;
  // Bắt buộc đủ biển số + loại xe + khu vực + vị trí + thời gian gửi xe
  // ngay từ lúc xe vào, để khi xe ra hệ thống luôn tra đúng bảng giá và
  // tính đúng phí gửi xe.
  if (!bienSo || !loaiXeId || !khuVucId || !viTriId || !hinhThuc) {
    return showMsg("msg-xevao", "Vui lòng nhập đủ: biển số, loại xe, khu vực, vị trí đỗ và thời gian gửi xe.", false);
  }
  try {
    const body = {
      bien_so: bienSo,
      loai_xe_id: Number(loaiXeId),
      khu_vuc_id: Number(khuVucId),
      vi_tri_id: Number(viTriId),
      hinh_thuc_gui: hinhThuc,
      chu_xe: document.getElementById("in-chuxe").value || null,
      so_dien_thoai: document.getElementById("in-sdt").value || null,
    };
    const data = await apiFetch("/api/xe-vao", { method: "POST", body: JSON.stringify(body) });
    showMsg("msg-xevao", `Đã ghi nhận xe vào. Mã lượt gửi: #${data.id}, vị trí: ${data.vi_tri_id}`);
    document.getElementById("in-bienso-vao").value = "";
    document.getElementById("in-chuxe").value = "";
    document.getElementById("in-sdt").value = "";
    taiChoTrong(); taiViTriTrong();
  } catch (e) { showMsg("msg-xevao", e.message, false); }
}

// Lượt gửi xe đang được chọn để xác nhận xe ra (khi tìm ra nhiều kết quả
// trùng thông tin, nhân viên phải bấm chọn đúng 1 lượt trước khi xác nhận).
let _luotXeRaDaChon = null;

async function xeRa() {
  const hinhThucChon = document.getElementById("out-hinhthuc").value;
  const body = hinhThucChon ? { hinh_thuc_gui: hinhThucChon } : {};
  if (_luotXeRaDaChon) {
    body.luot_gui_xe_id = _luotXeRaDaChon;
  } else {
    const bienSo = document.getElementById("out-bienso").value.trim();
    if (!bienSo) return showMsg("msg-xera", "Vui lòng nhập biển số hoặc bấm chọn đúng xe ở kết quả kiểm tra.", false);
    body.bien_so = bienSo;
  }
  try {
    const data = await apiFetch("/api/xe-ra", { method: "POST", body: JSON.stringify(body) });
    showMsg("msg-xera", `Xe đã ra. Phí thu: ${Number(data.phi_thu).toLocaleString()} VNĐ`);
    document.getElementById("xera-preview").innerHTML = "";
    document.getElementById("out-bienso").value = "";
    document.getElementById("out-chuxe").value = "";
    document.getElementById("out-sdt").value = "";
    document.getElementById("out-hinhthuc").value = "";
    _luotXeRaDaChon = null;
    taiChoTrong();
  } catch (e) { showMsg("msg-xera", e.message, false); }
}

let _xeraPreviewTimer = null;
// Xem trước thông tin xe đang gửi - kết hợp bất kỳ tiêu chí nào (biển số,
// tên chủ xe, số điện thoại): càng nhập nhiều thông tin, kết quả càng
// chính xác khi có nhiều xe trùng thông tin. Nếu tìm ra nhiều kết quả,
// nhân viên phải bấm chọn đúng xe trước khi xác nhận xe ra.
function xemTruocXeRa() {
  clearTimeout(_xeraPreviewTimer);
  _luotXeRaDaChon = null;
  const preview = document.getElementById("xera-preview");
  const bienSo = document.getElementById("out-bienso").value.trim();
  const chuXe = document.getElementById("out-chuxe").value.trim();
  const sdt = document.getElementById("out-sdt").value.trim();
  if (!bienSo && !chuXe && !sdt) { if (preview) preview.innerHTML = ""; return; }
  _xeraPreviewTimer = setTimeout(async () => {
    try {
      const params = new URLSearchParams({ trang_thai: "dang_gui" });
      if (bienSo) params.set("bien_so", bienSo);
      if (chuXe) params.set("chu_xe", chuXe);
      if (sdt) params.set("so_dien_thoai", sdt);
      const data = await apiFetch(`/api/tra-cuu?${params.toString()}`);
      if (!preview) return;
      if (!data.length) {
        preview.innerHTML = `<div class="msg bad">Không tìm thấy xe đang gửi khớp với thông tin đã nhập.</div>`;
        return;
      }
      if (data.length === 1) {
        _luotXeRaDaChon = data[0].id;
      }
      preview.innerHTML = (data.length > 1 ? `<p class="muted">Tìm thấy ${data.length} xe khớp thông tin — bấm chọn đúng xe cần cho ra:</p>` : "") +
        data.map(luot => `
        <button type="button" class="xera-info xera-info-pick ${data.length === 1 ? "chosen" : ""}" onclick="chonXeRa(${luot.id}, this)">
          <div><b>${escapeHtml(luot.bien_so)}</b><small>${escapeHtml(luot.ten_loai_xe || "-")}</small></div>
          <div><b>${escapeHtml(luot.chu_xe || "-")}</b><small>${escapeHtml(luot.so_dien_thoai || "-")}</small></div>
          <div><b>${escapeHtml(luot.ten_khu_vuc || "-")}</b><small>Vị trí ${escapeHtml(luot.ma_vi_tri || "-")}</small></div>
          <div><b>${formatThoiGian(luot.thoi_gian_vao)}</b><small>Giờ vào</small></div>
        </button>`).join("");
    } catch (_) { if (preview) preview.innerHTML = ""; }
  }, 400);
}

function chonXeRa(luotId, btnEl) {
  _luotXeRaDaChon = luotId;
  document.querySelectorAll(".xera-info-pick").forEach(b => b.classList.remove("chosen"));
  btnEl.classList.add("chosen");
}

async function taiChoTrong() {
  const view = document.getElementById("cho-trong-view");
  if (!view) return;
  try {
    const data = await apiFetch("/api/cho-trong");
    view.innerHTML = data.map(kv => {
      const daDo = kv.vi_tri.filter(v => v.xe_dang_do);
      return `
      <div class="cho-trong-khu">
        <div class="cho-trong-khu-head">
          <b>${escapeHtml(kv.ten_khu_vuc)}</b>
          <span class="cho-trong-tong">Trống ${kv.so_cho_trong}/${kv.tong_so_vi_tri}</span>
        </div>
        <div class="vi-tri-badges">
          ${kv.vi_tri.map(v => `<span class="badge ${v.trang_thai}" title="${v.xe_dang_do ? `Biển số ${escapeHtml(v.xe_dang_do.bien_so)} · đã đỗ ${formatPhutDaDo(v.xe_dang_do.so_phut_da_do)}` : "Còn trống"}">${escapeHtml(v.ma_vi_tri)}</span>`).join("")}
        </div>
        ${daDo.length ? `
        <div class="vi-tri-chitiet">
          ${daDo.map(v => `
            <div class="vi-tri-chitiet-row">
              <span class="badge da_do">${escapeHtml(v.ma_vi_tri)}</span>
              <div>
                <b>${escapeHtml(v.xe_dang_do.bien_so)}</b>
                <small>${escapeHtml(v.xe_dang_do.ten_loai_xe || "-")}${v.xe_dang_do.chu_xe ? " · " + escapeHtml(v.xe_dang_do.chu_xe) : ""}</small>
                <small>Vào lúc ${formatThoiGian(v.xe_dang_do.thoi_gian_vao)} · đã đỗ ${formatPhutDaDo(v.xe_dang_do.so_phut_da_do)}</small>
              </div>
            </div>`).join("")}
        </div>` : ""}
      </div>`;
    }).join("") || "<i>Chưa có khu vực nào.</i>";
  } catch (e) { console.error(e); }
}

function escapeHtml(s) {
  return String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

async function traCuu() {
  const params = new URLSearchParams();
  const bienSo = document.getElementById("tc-bienso").value.trim();
  const ten = document.getElementById("tc-ten").value.trim();
  const sdt = document.getElementById("tc-sdt").value.trim();
  const loaiXe = document.getElementById("tc-loaixe").value;
  const khuVuc = document.getElementById("tc-khuvuc").value;
  const trangThai = document.getElementById("tc-trangthai").value;
  const tu = document.getElementById("tc-tu").value;
  const den = document.getElementById("tc-den").value;
  if (bienSo) params.set("bien_so", bienSo);
  if (ten) params.set("chu_xe", ten);
  if (sdt) params.set("so_dien_thoai", sdt);
  if (loaiXe) params.set("loai_xe_id", loaiXe);
  if (khuVuc) params.set("khu_vuc_id", khuVuc);
  if (trangThai) params.set("trang_thai", trangThai);
  if (tu) params.set("tu_ngay", tu + "T00:00:00");
  if (den) params.set("den_ngay", den + "T23:59:59");

  const qs = params.toString();
  const data = await apiFetch("/api/tra-cuu" + (qs ? `?${qs}` : ""));
  document.getElementById("tra-cuu-view").innerHTML = `
    <table><tr><th>Biển số</th><th>Chủ xe</th><th>SĐT</th><th>Loại xe</th><th>Khu vực</th><th>Vị trí</th><th>Thời gian gửi</th><th>Vào</th><th>Ra</th><th>Phí</th><th>TT</th></tr>
    ${data.map(l => `<tr>
        <td>${escapeHtml(l.bien_so)}</td>
        <td>${escapeHtml(l.chu_xe) || "-"}</td>
        <td>${escapeHtml(l.so_dien_thoai) || "-"}</td>
        <td>${escapeHtml(l.ten_loai_xe)}</td>
        <td>${escapeHtml(l.ten_khu_vuc)}</td>
        <td>${escapeHtml(l.ma_vi_tri)}</td>
        <td>${escapeHtml(KHUNG_GIO_LABEL[l.hinh_thuc_gui] || "-")}</td>
        <td>${l.thoi_gian_vao ?? ""}</td>
        <td>${l.thoi_gian_ra ?? "-"}</td>
        <td>${l.phi_thu != null ? Number(l.phi_thu).toLocaleString() : "-"}</td>
        <td><span class="badge ${l.trang_thai === "dang_gui" ? "da_do" : "trong"}">${l.trang_thai === "dang_gui" ? "Đang gửi" : "Hoàn tất"}</span></td>
      </tr>`).join("") || `<tr><td colspan="11"><i>Không tìm thấy lượt gửi xe phù hợp.</i></td></tr>`}
    </table>`;
}

// ---------- Thống kê ----------
async function taiThongKe() {
  const tu = document.getElementById("tk-tu").value;
  const den = document.getElementById("tk-den").value;
  if (!tu || !den) return;
  const [luuLuong, doanhThu, lapDay] = await Promise.all([
    apiFetch(`/api/thong-ke/luu-luong?tu_ngay=${tu}T00:00:00&den_ngay=${den}T23:59:59`),
    apiFetch(`/api/thong-ke/doanh-thu?tu_ngay=${tu}T00:00:00&den_ngay=${den}T23:59:59`),
    apiFetch(`/api/thong-ke/lap-day`),
  ]);
  const thoiGianDongNhat = luuLuong.thoi_gian_dong_nhat;
  document.getElementById("thong-ke-view").innerHTML = `
    <p><b>Tổng lượt xe:</b> ${luuLuong.tong_so_luot} — <b>Thời gian đông nhất:</b> ${thoiGianDongNhat ? escapeHtml(KHUNG_GIO_LABEL[thoiGianDongNhat] || thoiGianDongNhat) : "-"}</p>
    <p><b>Tổng doanh thu:</b> ${Number(doanhThu.tong_doanh_thu).toLocaleString()} VNĐ</p>
    <p><b>Tỷ lệ lấp đầy:</b> ${lapDay.theo_khu_vuc.map(k => `${k.khu_vuc}: ${(k.ty_le*100).toFixed(0)}%`).join(", ") || "-"}</p>
    <div class="thongke-chart-wrap">
      <div class="thongke-chart-title">Tỷ lệ % lượt xe theo thời gian gửi xe</div>
      <div id="thongke-chart" class="thongke-chart"></div>
    </div>`;
  veBieuDoThoiGianGuiXe(luuLuong.theo_hinh_thuc_gui, luuLuong.ty_le_theo_hinh_thuc_gui);
}

// Vẽ biểu đồ cột thuần CSS/JS (không phụ thuộc thư viện ngoài), các cột
// "mọc" lên với animation ngay khi dữ liệu vừa tải xong.
function veBieuDoThoiGianGuiXe(theoHinhThuc, tyLe) {
  const el = document.getElementById("thongke-chart");
  if (!el) return;
  const nhan = Object.keys(KHUNG_GIO_LABEL);
  const coDuLieu = nhan.some(k => (theoHinhThuc || {})[k]);
  if (!coDuLieu) {
    el.innerHTML = "<p class='muted'>Chưa có dữ liệu để vẽ biểu đồ trong khoảng thời gian này.</p>";
    return;
  }
  el.innerHTML = nhan.map(k => {
    const soLuot = (theoHinhThuc || {})[k] || 0;
    const phanTram = (tyLe || {})[k] || 0;
    return `
      <div class="chart-col">
        <div class="chart-col-value">${phanTram}%</div>
        <div class="chart-col-track"><div class="chart-col-bar" style="--target-h:${phanTram}%"></div></div>
        <div class="chart-col-label">${escapeHtml(KHUNG_GIO_LABEL[k])}</div>
        <div class="chart-col-count">${soLuot} lượt</div>
      </div>`;
  }).join("");
  // Kích hoạt animation "mọc cột": đặt chiều cao 0 trước, sau đó thêm class
  // để CSS transition chạy tới --target-h ngay khi vừa load xong dữ liệu.
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      el.querySelectorAll(".chart-col-bar").forEach(bar => bar.classList.add("grown"));
    });
  });
}

// ---------- AI ----------
async function sinhBaoCao() {
  const tu = document.getElementById("ai-bc-tu").value;
  const den = document.getElementById("ai-bc-den").value;
  if (!tu || !den) return;
  try {
    const data = await apiFetch("/api/ai/bao-cao-luu-luong", {
      method: "POST",
      body: JSON.stringify({ tu_ngay: tu + "T00:00:00", den_ngay: den + "T23:59:59" }),
    });
    document.getElementById("ai-bc-view").className = "msg ok";
    document.getElementById("ai-bc-view").textContent = data.cau_tra_loi;
  } catch (e) {
    document.getElementById("ai-bc-view").className = "msg bad";
    document.getElementById("ai-bc-view").textContent = e.message;
  }
}

async function hoiDap() {
  const cauHoi = document.getElementById("ai-cauhoi").value.trim();
  if (!cauHoi) return;
  const log = document.getElementById("chat-log");
  log.innerHTML += `<div class="chat-msg"><b>Bạn:</b> ${cauHoi}</div>`;
  document.getElementById("ai-cauhoi").value = "";
  try {
    const data = await apiFetch("/api/ai/hoi-dap", { method: "POST", body: JSON.stringify({ cau_hoi: cauHoi }) });
    log.innerHTML += `<div class="chat-msg"><b>AI:</b> ${data.cau_tra_loi}</div>`;
  } catch (e) {
    log.innerHTML += `<div class="chat-msg"><b>Lỗi:</b> ${e.message}</div>`;
  }
  log.scrollTop = log.scrollHeight;
}

async function goiYNhanSu() {
  const tu = document.getElementById("ai-ns-tu").value;
  const den = document.getElementById("ai-ns-den").value;
  if (!tu || !den) return;
  try {
    const data = await apiFetch("/api/ai/goi-y-nhan-su", {
      method: "POST",
      body: JSON.stringify({ tu_ngay: tu + "T00:00:00", den_ngay: den + "T23:59:59" }),
    });
    document.getElementById("ai-ns-view").className = "msg ok";
    document.getElementById("ai-ns-view").textContent = data.cau_tra_loi;
  } catch (e) {
    document.getElementById("ai-ns-view").className = "msg bad";
    document.getElementById("ai-ns-view").textContent = e.message;
  }
}

async function taiLichSu() {
  const data = await apiFetch("/api/ai/lich-su");
  document.getElementById("lich-su-view").innerHTML = `
    <table><tr><th>Thời gian</th><th>Loại</th><th>Câu hỏi</th><th>Trả lời</th></tr>
    ${data.map(l => `<tr><td>${l.thoi_gian}</td><td>${l.loai}</td><td>${l.cau_hoi ?? "-"}</td><td>${(l.cau_tra_loi||"").slice(0,120)}...</td></tr>`).join("")}
    </table>`;
}

// ---------- Khởi động ----------
if (TOKEN) initApp();
