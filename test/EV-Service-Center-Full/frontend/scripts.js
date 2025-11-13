// --- GLOBAL CONFIG ---
const API_BASE_URL = "http://localhost"; // nếu chạy qua nginx gateway, để trống là đúng
const TOKEN_KEY = "jwt_token";
const ADMIN_TOKEN_KEY = "admin_jwt_token";
let currentUserId = null;

// --- GLOBAL ELEMENTS ---
const navAuthLinks = document.getElementById("nav-auth-links");
let currentPageElement = document.getElementById("login-page");

// --- UTILITIES (Show/Hide/Toast) ---
function showLoading() {
  const loader = document.getElementById("loading-spinner");
  if (loader) loader.classList.remove("hidden");
}
function hideLoading() {
  const loader = document.getElementById("loading-spinner");
  if (loader) loader.classList.add("hidden");
}

function showToast(message, isError = false) {
  const toast = document.createElement("div");
  toast.textContent = message;
  toast.className = `fixed bottom-5 right-5 p-4 rounded-lg shadow-lg text-white z-50 ${
    isError ? "bg-red-500" : "bg-green-500"
  }`;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}
window.showToast = showToast;

// Helper: Định dạng tiền tệ
function formatCurrency(amount) {
  return new Intl.NumberFormat("vi-VN").format(amount) + "₫";
}

// Helper: Định dạng trạng thái Hóa đơn
function formatInvoiceStatus(status) {
  switch (status) {
    case "pending":
      return { text: "Chờ thanh toán", class: "bg-yellow-100 text-yellow-800" };
    case "issued":
      return { text: "Đã xuất", class: "bg-blue-100 text-blue-800" };
    case "paid":
      return { text: "Đã thanh toán", class: "bg-green-100 text-green-800" };
    case "canceled":
      return { text: "Đã hủy", class: "bg-red-100 text-red-800" };
    case "success":
      return { text: "Thành công", class: "bg-green-100 text-green-800" };
    case "failed":
      return { text: "Thất bại", class: "bg-red-100 text-red-800" };
    default:
      return { text: status, class: "bg-gray-100 text-gray-800" };
  }
}

// --- AUTH & NAVIGATION HELPERS (Hoisted/Đưa ra ngoài phạm vi) ---
function updateNav() {
  const token = localStorage.getItem(TOKEN_KEY);
  if (!navAuthLinks) return;

  // ✅ BỔ SUNG NÚT 'CÔNG VIỆC' VÀ 'HÓA ĐƠN' CHO NGƯỜI DÙNG ĐÃ ĐĂNG NHẬP
  navAuthLinks.innerHTML = token
    ? `
        <a href="#" onclick="navigateTo('booking')" class="nav-link text-gray-600 hover:bg-indigo-600 hover:text-white px-3 py-2 rounded-md text-sm font-medium">Đặt Lịch</a> 
        <a href="#" onclick="navigateTo('my-tasks')" class="nav-link text-gray-600 hover:bg-indigo-600 hover:text-white px-3 py-2 rounded-md text-sm font-medium">Công Việc</a> 
        <a href="#" onclick="navigateTo('invoice-history')" class="nav-link text-gray-600 hover:bg-indigo-600 hover:text-white px-3 py-2 rounded-md text-sm font-medium">Hóa Đơn</a> 
        <a href="#" onclick="navigateTo('profile')" class="nav-link text-gray-600 hover:bg-indigo-600 hover:text-white px-3 py-2 rounded-md text-sm font-medium">Hồ Sơ</a>
        <a href="#" onclick="logout()" class="ml-4 bg-red-500 text-white px-3 py-2 rounded-md text-sm font-medium hover:bg-red-600">Đăng Xuất</a>
        `
    : `
        <a href="#" onclick="navigateTo('login')" class="nav-link text-gray-600 hover:bg-indigo-600 hover:text-white px-3 py-2 rounded-md text-sm font-medium">Đăng Nhập</a>
        <a href="#" onclick="navigateTo('register')" class="ml-4 bg-green-500 text-white px-3 py-2 rounded-md text-sm font-medium hover:bg-green-600">Đăng Ký</a>
        `;
}

function logout() {
  localStorage.removeItem(TOKEN_KEY);
  showToast("Đã đăng xuất!");
  updateNav();
  navigateTo("login");
}
window.logout = logout;

// --- CORE API REQUEST (UPDATED) ---
async function apiRequestCore(tokenKey, endpoint, method = "GET", body = null) {
  showLoading();
  try {
    const headers = { "Content-Type": "application/json" };

    const token = localStorage.getItem(tokenKey || TOKEN_KEY);
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const options = { method, headers };
    if (body) options.body = JSON.stringify(body);

    const url = endpoint.startsWith("http")
      ? endpoint
      : `${API_BASE_URL}${endpoint}`;

    const response = await fetch(url, options);

    const text = await response.text();
    let data;
    try {
      data = JSON.parse(text);
    } catch {
      data = { message: text };
    }

    if (!response.ok) {
      // XỬ LÝ 401: Tự động đăng xuất
      if (response.status === 401) {
        if ((tokenKey || TOKEN_KEY) === TOKEN_KEY) {
          logout();
          throw {
            message: "Phiên làm việc hết hạn. Vui lòng đăng nhập lại.",
            status: 401,
          };
        }
      }

      const errMsg =
        data.error || data.message || `HTTP Error ${response.status}`;
      throw { message: errMsg, status: response.status };
    }

    return data;
  } catch (err) {
    const errMsg = err.message || "Lỗi không xác định!";
    console.error("🚨 API Request Error:", err);
    showToast(errMsg, true);
    throw err;
  } finally {
    hideLoading();
  }
}

// ✅ NEW FUNCTION: Đặt loại dịch vụ khi chuyển từ trang Inventory
function setServiceType(itemName) {
  // Chờ 1 chút để trang booking được tải và các element hiện ra
  setTimeout(() => {
    const selectElement = document.getElementById("service-type");
    const newOptionValue = `Yêu cầu thay thế/lắp đặt: ${itemName}`;

    // 1. Kiểm tra xem option đã tồn tại chưa
    let optionExists = false;
    for (let i = 0; i < selectElement.options.length; i++) {
      if (selectElement.options[i].value === newOptionValue) {
        selectElement.value = newOptionValue;
        optionExists = true;
        break;
      }
    }

    // 2. Nếu chưa tồn tại, thêm option mới và chọn nó
    if (!optionExists) {
      const newOption = document.createElement("option");
      newOption.value = newOptionValue;
      newOption.textContent = newOptionValue;
      selectElement.appendChild(newOption);
      selectElement.value = newOptionValue;
    }

    // Tùy chọn: Scroll đến form đặt lịch nếu cần
    document
      .getElementById("booking-form")
      ?.scrollIntoView({ behavior: "smooth" });
  }, 100);
}
window.setServiceType = setServiceType;

// --- NAVIGATION (Định nghĩa DUY NHẤT một lần) ---
function navigateTo(pageId) {
  const nextPageElement = document.getElementById(`${pageId}-page`);
  document.querySelectorAll(".page").forEach((p) => {
    p.classList.add("hidden");
    p.classList.remove("active");
  });

  if (nextPageElement) {
    nextPageElement.classList.remove("hidden");
    nextPageElement.classList.add("active");
  }
  currentPageElement = nextPageElement;

  if (pageId === "profile") loadProfileDetails(); // ✅ Trigger tải Profile và Lịch sử
  if (pageId === "forget-password") resetForgetForm?.();

  // Tải dữ liệu tùy thuộc vào section
  if (pageId === "inventory-list") loadInventoryList();
  if (pageId === "booking") {
    loadMyBookings(); // Tải lịch hẹn cho trang đặt lịch
  }
  if (pageId === "invoice-history") {
    // Khi vào trang hóa đơn, mặc định hiển thị tab Hóa đơn
    showHistory("invoices", document.getElementById("tab-invoices"));
  }
  // ✅ TẢI CÔNG VIỆC BẢO TRÌ
  if (pageId === "my-tasks") {
    loadMyTasks();
  }

  // Gọi updateNav sau khi điều hướng
  updateNav();
}
window.navigateTo = navigateTo;

// --- NAVIGATION HELPERS (Logic không cần public) ---

function resetForgetForm() {
  const emailInput = document.getElementById("forget-email");
  const otpInput = document.getElementById("otp-code");
  const newPasswordInput = document.getElementById("new-password");

  if (emailInput) {
    emailInput.value = "";
  }
  if (otpInput) {
    otpInput.value = "";
  }
  if (newPasswordInput) {
    newPasswordInput.value = "";
  }

  const forgetForm = document.getElementById("forget-password-form");
  const resetForm = document.getElementById("reset-password-form");

  if (forgetForm) {
    forgetForm.classList.remove("hidden"); // Hiện form gửi email
  }
  if (resetForm) {
    resetForm.classList.add("hidden"); // Ẩn form nhập OTP/pass mới
  }
}

// --- PROFILE HANDLERS (Đã sửa để tải lịch sử) ---
function toggleProfileForm(forceShow) {
  const form = document.getElementById("profile-update-form");
  const btnBox = document.getElementById("update-profile-button-container");
  if (!form || !btnBox) return;

  const show = forceShow ?? form.classList.contains("hidden");
  if (show) {
    form.classList.remove("hidden");
    btnBox.classList.add("hidden");
  } else {
    form.classList.add("hidden");
    btnBox.classList.remove("hidden");
  }
}
window.toggleProfileForm = toggleProfileForm;

// ✅ HÀM TẢI PROFILE MỚI: Tải cả thông tin cá nhân và lịch sử
async function loadProfileDetails() {
  const bookingListEl = document.getElementById("profile-booking-list");
  if (bookingListEl) {
    // Đặt trạng thái tải khi bắt đầu
    bookingListEl.innerHTML =
      '<div class="bg-white p-6 rounded-lg shadow-md text-gray-500">Đang tải lịch sử đặt lịch...</div>';
  }

  try {
    // 1. Tải Profile
    const profile = await apiRequestCore(TOKEN_KEY, "/api/profile", "GET");

    const div = document.getElementById("profile-details");
    if (!div) return;

    div.innerHTML = `
            <p><strong>Họ và tên:</strong> ${
              profile.full_name || "Chưa cập nhật"
            }</p>
            <p><strong>Điện thoại:</strong> ${
              profile.phone_number || "Chưa cập nhật"
            }</p>
            <p><strong>Địa chỉ:</strong> ${
              profile.address || "Chưa cập nhật"
            }</p>
            <p><strong>Model Xe:</strong> ${
              profile.vehicle_model || "Chưa cập nhật"
            }</p>
            <p><strong>Số VIN:</strong> ${
              profile.vin_number || "Chưa cập nhật"
            }</p>
        `;

    const fields = [
      ["profile-fullname", "full_name"],
      ["profile-phone", "phone_number"],
      ["profile-address", "address"],
      ["profile-vehicle-model", "vehicle_model"],
      ["profile-vin-number", "vin_number"],
    ];

    fields.forEach(([id, key]) => {
      const input = document.getElementById(id);
      if (input) input.value = profile[key] || "";
    });

    toggleProfileForm(false);

    // 2. Tải Lịch sử Đặt Lịch
    await loadBookingsForProfile();
  } catch (err) {
    if (err.status === 404) {
      const div = document.getElementById("profile-details");
      if (div)
        div.innerHTML = "<p>Chưa có thông tin hồ sơ. Vui lòng cập nhật.</p>";
      toggleProfileForm(true);
      return;
    }

    console.error("❌ Failed to load profile:", err);
    const div = document.getElementById("profile-details");
    if (div) div.innerHTML = "<p>Lỗi tải hồ sơ. Vui lòng thử lại sau.</p>";
    toggleProfileForm(false);

    if (bookingListEl) {
      bookingListEl.innerHTML =
        '<div class="bg-red-100 p-6 rounded-lg shadow-md text-red-700">Lỗi: Không thể tải lịch sử đặt lịch.</div>';
    }
  }
}

// --- FORM HANDLERS ---
document.getElementById("login-form")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const email_username = document.getElementById("login-email-username")?.value;
  const password = document.getElementById("login-password")?.value;

  try {
    const data = await apiRequestCore(null, "/api/login", "POST", {
      email_username,
      password,
    });

    if (data?.access_token) {
      localStorage.setItem(TOKEN_KEY, data.access_token);
      showToast("Đăng nhập thành công!");
      updateNav();

      const token = data.access_token;
      const payload = JSON.parse(atob(token.split(".")[1]));
      currentUserId = payload.sub;

      navigateTo("home");
    }
  } catch (error) {
    console.error("Login failed:", error);
  }
});

document
  .getElementById("register-form")
  ?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const username = document.getElementById("register-username")?.value;
    const email = document.getElementById("register-email")?.value;
    const password = document.getElementById("register-password")?.value;

    try {
      // SỬ DỤNG apiRequestCore
      const data = await apiRequestCore(null, "/api/register", "POST", {
        username,
        email,
        password,
      });
      showToast(data.message || "Đăng ký thành công!");
      e.target.reset();
      navigateTo("login");
    } catch (error) {
      console.error("Register failed:", error);
    }
  });

// Event listener cho form cập nhật hồ sơ
document
  .getElementById("profile-update-form")
  ?.addEventListener("submit", async (e) => {
    e.preventDefault();

    const data = {
      full_name: document.getElementById("profile-fullname")?.value,
      phone_number: document.getElementById("profile-phone")?.value,
      address: document.getElementById("profile-address")?.value,
      vehicle_model: document.getElementById("profile-vehicle-model")?.value,
      vin_number: document.getElementById("profile-vin-number")?.value,
    };

    try {
      const result = await apiRequestCore(
        TOKEN_KEY,
        "/api/profile",
        "PUT",
        data
      );
      showToast(result.message || "Cập nhật hồ sơ thành công!");
      loadProfileDetails(); // Tải lại thông tin sau khi cập nhật
    } catch (error) {
      console.error("Lỗi khi cập nhật hồ sơ:", error);
    }
  });

document
  .getElementById("booking-form")
  ?.addEventListener("submit", async (e) => {
    e.preventDefault();

    // 1. Lấy dữ liệu từ form
    const service_type = document.getElementById("service-type")?.value;
    const technician_id = parseInt(
      document.getElementById("technician-id")?.value
    );
    const station_id = parseInt(document.getElementById("station-id")?.value);

    const startTimeInput = document.getElementById("start-time")?.value;
    const endTimeInput = document.getElementById("end-time")?.value;

    if (!startTimeInput || !endTimeInput) {
      showToast("Vui lòng nhập đầy đủ thời gian.", true);
      return;
    }

    // Logic kiểm tra thời gian
    if (new Date(startTimeInput) >= new Date(endTimeInput)) {
      showToast("Thời gian kết thúc phải sau thời gian bắt đầu.", true);
      return;
    }

    const bookingData = {
      service_type,
      technician_id,
      station_id,
      // Backend Flask/Python cần định dạng ISO 8601 (như datetime-local cung cấp)
      start_time: startTimeInput + ":00",
      end_time: endTimeInput + ":00",
    };

    try {
      // 2. Gọi API CREATE BOOKING (Endpoint: /api/bookings/items)
      const data = await apiRequestCore(
        TOKEN_KEY,
        "/api/bookings/items",
        "POST",
        bookingData
      );

      // 3. Xử lý thành công
      showToast(data.message || "Đặt lịch thành công!");
      e.target.reset();

      // Tải lại danh sách lịch hẹn sau khi đặt thành công
      loadMyBookings();
    } catch (error) {
      // Lỗi đã được xử lý trong apiRequestCore
      console.error("Lỗi khi đặt lịch:", error);
    }
  });

// --- INIT ---
document.addEventListener("DOMContentLoaded", () => {
  updateNav();
  const token = localStorage.getItem(TOKEN_KEY);

  if (token) {
    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      currentUserId = payload.sub;
      const now = Math.floor(Date.now() / 1000);
      if (payload.exp && payload.exp < now) logout();
      else navigateTo("home");
    } catch {
      logout();
    }
  } else {
    navigateTo("login");
  }
});

// Thêm lại event listener cho form quên mật khẩu
document.addEventListener("DOMContentLoaded", () => {
  // --- Bộ não cho Form 1: Gửi Mã OTP ---
  const forgetForm = document.getElementById("forget-password-form");
  if (forgetForm) {
    forgetForm.addEventListener("submit", async (event) => {
      event.preventDefault(); // Ngăn trang tải lại

      const emailInput = document.getElementById("forget-email");
      const email = emailInput.value;
      const submitButton = forgetForm.querySelector('button[type="submit"]');

      if (!email) {
        showToast("Vui lòng nhập email của bạn.", true);
        return;
      }

      submitButton.disabled = true;
      submitButton.textContent = "Đang gửi...";

      try {
        const data = await apiRequestCore(null, "/api/send-otp", "POST", {
          email: email,
        });

        showToast(
          data.message || "Gửi OTP thành công! Vui lòng kiểm tra email."
        );

        forgetForm.classList.add("hidden");
        document
          .getElementById("reset-password-form")
          .classList.remove("hidden");

        document.getElementById("reset-email-hidden").value = email;
      } catch (error) {
        console.error("Lỗi khi gửi OTP:", error);
        // Lỗi đã được xử lý trong apiRequestCore
      } finally {
        submitButton.disabled = false;
        submitButton.textContent = "Gửi Mã OTP";
      }
    });
  }

  // --- Bộ não cho Form 2: Đặt Lại Mật Khẩu ---
  const resetForm = document.getElementById("reset-password-form");
  if (resetForm) {
    resetForm.addEventListener("submit", async (event) => {
      event.preventDefault(); // Ngăn trang tải lại

      const email = document.getElementById("reset-email-hidden").value;
      const otp = document.getElementById("otp-code").value;
      const newPassword = document.getElementById("new-password").value;
      const submitButton = resetForm.querySelector('button[type="submit"]');

      if (!otp || !newPassword) {
        showToast("Vui lòng nhập Mã OTP và Mật khẩu mới.", true);
        return;
      }

      submitButton.disabled = true;
      submitButton.textContent = "Đang xử lý...";

      try {
        const data = await apiRequestCore(null, "/api/reset-password", "POST", {
          email: email,
          otp: otp,
          new_password: newPassword,
        });

        showToast(
          data.message || "Đặt lại mật khẩu thành công! Bạn có thể đăng nhập."
        );

        navigateTo("login");
        resetForgetForm();
      } catch (error) {
        console.error("Lỗi khi reset mật khẩu:", error);
        // Lỗi đã được xử lý trong apiRequestCore
      } finally {
        submitButton.disabled = false;
        submitButton.textContent = "Đặt Lại Mật Khẩu";
      }
    });
  }
});

// ========================================================
// LOGIC CHỨC NĂNG (INVENTORY VÀ BOOKING)
// ========================================================

// ✅ Cập nhật renderItemCard để thêm nút "Đặt Lịch Dịch Vụ Liên Quan"
function renderItemCard(item) {
  return `
    <div class="bg-white p-5 rounded-lg shadow-md border border-gray-200 hover:shadow-lg transition duration-200">
        <h3 class="text-xl font-semibold text-indigo-700">${item.name}</h3>
        <p class="text-gray-500 text-sm mt-1">Mã Part: <span class="font-mono text-gray-700">${
          item.part_number
        }</span></p>
        
        <div class="mt-4 flex justify-between items-center">
            <div>
                <p class="text-lg font-bold text-green-600">
                    ${formatCurrency(item.price)}
                </p>
                <p class="text-xs text-gray-400">Giá tham khảo</p>
            </div>
            <div class="text-right">
                <span class="text-sm font-medium text-gray-800 p-2 bg-indigo-100 rounded-full">
                    Còn: ${item.quantity || "Liên hệ"}
                </span>
            </div>
        </div>
        
        <div class="mt-4 pt-4 border-t border-gray-100">
            <button 
                onclick="navigateTo('booking'); setServiceType('${item.name}')" 
                class="w-full bg-indigo-600 text-white text-sm font-medium py-2 rounded-lg hover:bg-indigo-700 transition"
            >
                Đặt Lịch Dịch Vụ Liên Quan
            </button>
        </div>
        
    </div>
  `;
}

async function loadInventoryList() {
  const container = document.getElementById("inventory-list-container");
  const loadingMessage = document.getElementById("inventory-loading-message");
  if (!container || !loadingMessage) return;

  // Hiển thị thông báo tải
  loadingMessage.classList.remove("hidden");
  container.innerHTML = "";

  try {
    // Gọi API Inventory Service (GET /api/inventory/items)
    const items = await apiRequestCore(
      null, // Không cần token JWT cho user thường xem danh sách
      "/api/inventory/items"
    );

    loadingMessage.classList.add("hidden");

    if (!items || items.length === 0) {
      container.innerHTML = `
        <div class="text-center py-12 bg-gray-50 rounded-lg">
            <p class="text-lg text-gray-500">Hiện tại chưa có phụ tùng nào được niêm yết.</p>
        </div>
    `;
      return;
    }

    // Render các card vật tư
    container.innerHTML = items.map(renderItemCard).join("");
  } catch (error) {
    loadingMessage.classList.add("hidden");
    container.innerHTML = `
        <div class="text-center py-12 bg-red-100 text-red-700 rounded-lg border border-red-300">
            <p>Lỗi khi tải danh sách vật tư. Vui lòng thử lại sau.</p>
        </div>
    `;
    console.error("Failed to load inventory list:", error);
  }
}

// Logic Booking
function formatBookingStatus(status) {
  switch (status) {
    case "pending":
      return { text: "Chờ xác nhận", class: "bg-yellow-100 text-yellow-800" };
    case "confirmed":
      return { text: "Đã xác nhận", class: "bg-green-100 text-green-800" };
    case "completed":
      return { text: "Hoàn thành", class: "bg-indigo-100 text-indigo-800" };
    case "canceled":
      return { text: "Đã hủy", class: "bg-red-100 text-red-800" };
    default:
      return { text: status, class: "bg-gray-100 text-gray-800" };
  }
}

// ✅ HÀM MỚI: Tải lịch hẹn cho trang profile (Tương tự loadMyBookings)
async function loadBookingsForProfile() {
  const bookingListEl = document.getElementById("profile-booking-list");
  if (!bookingListEl) return;

  try {
    const bookings = await apiRequestCore(
      TOKEN_KEY,
      "/api/bookings/my-bookings",
      "GET"
    );

    if (bookings.length === 0) {
      bookingListEl.innerHTML =
        '<div class="bg-white p-6 rounded-lg shadow-md text-center text-gray-500">Bạn chưa có lịch hẹn nào.</div>';
      return;
    }

    let html = "";
    bookings.forEach((booking) => {
      const startDate = new Date(booking.start_time).toLocaleString("vi-VN", {
        dateStyle: "short",
        timeStyle: "short",
      });
      const endDate = new Date(booking.end_time).toLocaleTimeString("vi-VN", {
        timeStyle: "short",
      });
      const status = formatBookingStatus(booking.status);

      html += `
                <div class="booking-item bg-white p-6 rounded-lg shadow-md border-l-4 border-indigo-500">
                    <p class="font-bold text-lg">${booking.service_type}</p>
                    <p class="text-gray-600">Lịch ID: ${booking.id} | KTV: ID ${booking.technician_id} | Trạm: ID ${booking.station_id}</p>
                    <p class="text-sm text-gray-500">Thời gian: ${startDate} - ${endDate}</p>
                    <span class="inline-flex items-center px-3 py-0.5 rounded-full text-sm font-medium ${status.class}">
                        Trạng thái: ${status.text}
                    </span>
                </div>
            `;
    });
    bookingListEl.innerHTML = html;
  } catch (error) {
    bookingListEl.innerHTML =
      '<div class="bg-red-100 p-6 rounded-lg shadow-md text-center text-red-700">Lỗi: Không thể tải lịch hẹn.</div>';
    console.error("Lỗi khi tải lịch hẹn cho profile:", error);
  }
}

async function loadMyBookings() {
  const bookingListEl = document.getElementById("booking-list");
  if (!bookingListEl) return;
  bookingListEl.innerHTML =
    '<div class="bg-white p-6 rounded-lg shadow-md text-center text-gray-500">Đang tải lịch hẹn...</div>';

  try {
    // Gọi API GET MY BOOKINGS
    const bookings = await apiRequestCore(
      TOKEN_KEY,
      "/api/bookings/my-bookings",
      "GET"
    );

    if (bookings.length === 0) {
      bookingListEl.innerHTML =
        '<div class="bg-white p-6 rounded-lg shadow-md text-center text-gray-500">Bạn chưa có lịch hẹn nào.</div>';
      return;
    }

    let html = "";
    bookings.forEach((booking) => {
      const startDate = new Date(booking.start_time).toLocaleString("vi-VN", {
        dateStyle: "short",
        timeStyle: "short",
      });
      const endDate = new Date(booking.end_time).toLocaleTimeString("vi-VN", {
        timeStyle: "short",
      });
      const status = formatBookingStatus(booking.status);

      html += `
        <div class="booking-item bg-white p-6 rounded-lg shadow-md border-l-4 border-indigo-500">
            <p class="font-bold text-lg">${booking.service_type}</p>
            <p class="text-gray-600">Lịch ID: ${booking.id} | KTV: ID ${booking.technician_id} | Trạm: ID ${booking.station_id}</p>
            <p class="text-sm text-gray-500">Thời gian: ${startDate} - ${endDate}</p>
            <span class="inline-flex items-center px-3 py-0.5 rounded-full text-sm font-medium ${status.class}">
                Trạng thái: ${status.text}
            </span>
        </div>
    `;
    });
    bookingListEl.innerHTML = html;
  } catch (error) {
    bookingListEl.innerHTML =
      '<div class="bg-red-100 p-6 rounded-lg shadow-md text-center text-red-700">Lỗi: Không thể tải lịch hẹn.</div>';
    console.error("Lỗi khi tải lịch hẹn:", error);
  }
}

// ========================================================
// ✅ LOGIC CHỨC NĂNG (MY TASKS - USER)
// ========================================================

/**
 * Helper: Định dạng trạng thái công việc (Tương tự Admin)
 */
function formatMaintenanceStatus(status) {
  switch (status) {
    case "pending":
      return { text: "Chờ thực hiện", class: "bg-yellow-100 text-yellow-800" };
    case "in_progress":
      return { text: "Đang tiến hành", class: "bg-blue-100 text-blue-800" };
    case "completed":
      return { text: "Hoàn thành", class: "bg-green-100 text-green-800" };
    case "failed":
      return { text: "Thất bại/Hủy", class: "bg-red-100 text-red-800" };
    default:
      return { text: status, class: "bg-gray-100 text-gray-800" };
  }
}

/**
 * Tải danh sách công việc bảo trì của người dùng hiện tại
 */
async function loadMyTasks() {
  const container = document.getElementById("my-tasks-list-container");
  if (!container) return;

  container.innerHTML =
    '<div class="bg-white p-6 rounded-lg shadow-md text-center text-gray-500">Đang tải danh sách công việc...</div>';

  try {
    const tasks = await apiRequestCore(
      TOKEN_KEY,
      "/api/maintenance/my-tasks", // Endpoint GET MY TASKS
      "GET"
    );

    if (!tasks || tasks.length === 0) {
      container.innerHTML =
        '<div class="bg-white p-6 rounded-lg shadow-md text-center text-gray-500">Bạn chưa có công việc bảo trì nào.</div>';
      return;
    }

    container.innerHTML = tasks.map(renderTaskCard).join("");
  } catch (error) {
    container.innerHTML = `
            <div class="text-center py-8 bg-red-100 text-red-700 rounded-lg border border-red-300">
                <p>Lỗi khi tải danh sách công việc. Vui lòng thử lại sau.</p>
            </div>
        `;
    console.error("Failed to load my tasks:", error);
  }
}
window.loadMyTasks = loadMyTasks;

function renderTaskCard(task) {
  const statusInfo = formatMaintenanceStatus(task.status);
  const date = new Date(task.created_at).toLocaleDateString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });

  return `
        <div class="bg-white p-5 rounded-lg shadow-md border-l-4 border-${
          statusInfo.class.includes("green")
            ? "green-500"
            : statusInfo.class.includes("blue")
            ? "blue-500"
            : statusInfo.class.includes("yellow")
            ? "yellow-500"
            : "red-500"
        } flex justify-between items-center">
            <div>
                <h3 class="text-xl font-bold text-gray-800">${
                  task.description
                }</h3>
                <p class="text-sm text-gray-500 mt-1">Booking ID: ${
                  task.booking_id
                } | Task ID: ${task.id} | KTV ID: ${task.technician_id}</p>
                <p class="text-sm text-gray-600 mt-1">VIN Xe: <span class="font-mono text-indigo-700">${
                  task.vehicle_vin
                }</span></p>
                <p class="text-xs text-gray-400 mt-2">Ngày khởi tạo: ${date}</p>
            </div>
            <div class="text-right space-y-2">
                <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                  statusInfo.class
                }">
                    Trạng thái: ${statusInfo.text}
                </span>
                <p class="text-sm text-gray-500">
                    ${
                      task.status === "completed"
                        ? "Hoàn thành!"
                        : task.status === "pending"
                        ? "Công việc chờ được xử lý."
                        : "Đang được tiến hành..."
                    }
                </p>
            </div>
        </div>
    `;
}

// ========================================================
// ✅ LOGIC CHỨC NĂNG (INVOICE - USER)
// ========================================================

// --- Tab Navigation Logic (MỚI) ---
function showHistory(type, element) {
  // Cập nhật style của tabs
  document
    .querySelectorAll('#invoice-history-page a[id^="tab-"]')
    .forEach((tab) => {
      tab.classList.remove(
        "bg-white",
        "text-indigo-600",
        "border-l",
        "border-t",
        "border-r"
      );
      tab.classList.add("bg-gray-100", "text-gray-500", "hover:text-gray-700");
    });

  element.classList.add(
    "bg-white",
    "text-indigo-600",
    "border-l",
    "border-t",
    "border-r"
  );
  element.classList.remove(
    "bg-gray-100",
    "text-gray-500",
    "hover:text-gray-700"
  );

  // Ẩn/Hiện nội dung
  document.querySelectorAll(".history-content").forEach((content) => {
    content.classList.add("hidden");
  });
  document.getElementById(`history-content-${type}`).classList.remove("hidden");

  // Tải dữ liệu tương ứng
  if (type === "invoices") {
    loadMyInvoicesList();
  } else if (type === "payments") {
    loadMyPaymentHistoryList();
  }
}
window.showHistory = showHistory;

// --- TẢI DANH SÁCH HÓA ĐƠN (Invoice List) ---
async function loadMyInvoicesList() {
  const container = document.getElementById("invoice-list-container");
  if (!container) return;

  container.innerHTML =
    '<div class="bg-white p-6 rounded-lg shadow-md text-center text-gray-500">Đang tải lịch sử hóa đơn...</div>';

  try {
    const invoices = await apiRequestCore(
      TOKEN_KEY,
      "/api/invoices/my", // Endpoint GET MY INVOICES
      "GET"
    );

    if (!invoices || invoices.length === 0) {
      container.innerHTML =
        '<div class="bg-white p-6 rounded-lg shadow-md text-center text-gray-500">Bạn chưa có hóa đơn nào.</div>';
      return;
    }

    container.innerHTML = invoices.map(renderInvoiceCard).join("");
  } catch (error) {
    container.innerHTML = `
              <div class="text-center py-8 bg-red-100 text-red-700 rounded-lg border border-red-300">
                  <p>Lỗi khi tải lịch sử hóa đơn. Vui lòng thử lại sau.</p>
              </div>
          `;
    console.error("Failed to load invoice history:", error);
  }
}

// --- TẢI DANH SÁCH GIAO DỊCH (Payment History List) ---
async function loadMyPaymentHistoryList() {
  const container = document.getElementById("payment-history-list-container");
  if (!container) return;

  container.innerHTML =
    '<div class="bg-white p-6 rounded-lg shadow-md text-center text-gray-500">Đang tải lịch sử giao dịch...</div>';

  try {
    const history = await apiRequestCore(
      TOKEN_KEY,
      "/api/payments/history/my", // Endpoint GET MY HISTORY
      "GET"
    );

    if (!history || history.length === 0) {
      container.innerHTML =
        '<div class="bg-white p-6 rounded-lg shadow-md text-center text-gray-500">Bạn chưa có giao dịch thanh toán nào.</div>';
      return;
    }

    // Sử dụng lại hàm renderPaymentCard đã định nghĩa
    container.innerHTML = history.map(renderPaymentCard).join("");
  } catch (error) {
    container.innerHTML = `
              <div class="text-center py-8 bg-red-100 text-red-700 rounded-lg border border-red-300">
                  <p>Lỗi khi tải lịch sử giao dịch. Vui lòng thử lại sau.</p>
              </div>
          `;
    console.error("Failed to load payment history:", error);
  }
}

// --- Render Invoice Card (ĐÃ SỬA NÚT THANH TOÁN) ---
function renderInvoiceCard(invoice) {
  const statusInfo = formatInvoiceStatus(invoice.status);
  const date = new Date(invoice.created_at).toLocaleDateString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });

  const isPaid = invoice.status === "paid";
  const payButton = isPaid
    ? '<span class="block w-full text-sm text-center text-green-600 font-bold py-2">ĐÃ THANH TOÁN</span>'
    : `<button 
          onclick="showPaymentModal(${invoice.id}, ${invoice.total_amount}, '${invoice.status}')" 
          class="block w-full bg-green-500 text-white text-sm font-medium py-2 px-4 rounded-lg hover:bg-green-600 transition"
        >
          Thanh Toán Ngay
        </button>`;

  return `
        <div class="bg-white p-5 rounded-lg shadow-md border-l-4 border-indigo-500 flex justify-between items-center hover:shadow-lg transition duration-200">
            <div>
                <h3 class="text-xl font-bold text-gray-800">Hóa Đơn #${
                  invoice.id
                }</h3>
                <p class="text-sm text-gray-500 mt-1">Lịch hẹn ID: ${
                  invoice.booking_id
                } | Ngày tạo: ${date}</p>
                <p class="text-2xl font-bold ${
                  isPaid ? "text-green-600" : "text-red-600"
                } mt-2">
                    ${formatCurrency(invoice.total_amount)}
                </p>
            </div>
            <div class="text-right space-y-2">
                <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                  statusInfo.class
                }">
                    ${statusInfo.text}
                </span>
                <button 
                    onclick="showInvoiceDetails(${invoice.id})" 
                    class="block w-full bg-indigo-500 text-white text-sm font-medium py-2 px-4 rounded-lg hover:bg-indigo-600 transition"
                >
                    Xem Chi Tiết
                </button>
                ${payButton}
            </div>
        </div>
    `;
}

// --- Render Payment Card ---
function renderPaymentCard(transaction) {
  const statusInfo = formatInvoiceStatus(transaction.status);
  const date = new Date(transaction.created_at).toLocaleString("vi-VN", {
    dateStyle: "short",
    timeStyle: "short",
  });

  return `
          <div class="bg-white p-5 rounded-lg shadow-md border-l-4 border-indigo-500 flex justify-between items-center hover:shadow-lg transition duration-200">
              <div>
                  <h3 class="text-xl font-bold text-gray-800">Giao dịch #${
                    transaction.id
                  }</h3>
                  <p class="text-sm text-gray-500 mt-1">Hóa đơn ID: ${
                    transaction.invoice_id
                  } | Ngày: ${date}</p>
                  <p class="text-sm text-gray-500 mt-1">Phương thức: ${transaction.method.toUpperCase()} | PG ID: ${
    transaction.pg_transaction_id
  }</p>
                  <p class="text-2xl font-bold ${
                    transaction.status === "success"
                      ? "text-green-600"
                      : "text-red-600"
                  } mt-2">
                      ${formatCurrency(transaction.amount)}
                  </p>
              </div>
              <div class="text-right space-y-2">
                  <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                    statusInfo.class
                  }">
                      ${statusInfo.text}
                  </span>
              </div>
          </div>
      `;
}

// --- LOGIC MODAL CHI TIẾT ---

const invoiceDetailModal = document.getElementById("invoice-detail-modal");

function closeInvoiceDetailModal() {
  if (invoiceDetailModal) invoiceDetailModal.classList.add("hidden");
}
window.closeInvoiceDetailModal = closeInvoiceDetailModal; // Export ra window

async function showInvoiceDetails(invoiceId) {
  try {
    const detail = await apiRequestCore(
      TOKEN_KEY,
      `/api/invoices/${invoiceId}`,
      "GET"
    );

    if (!detail) throw new Error("Không tìm thấy chi tiết hóa đơn.");

    // 1. Cập nhật header/footer
    const statusInfo = formatInvoiceStatus(detail.status);
    const date = new Date(detail.created_at).toLocaleString("vi-VN");

    document.getElementById("invoice-detail-id").textContent = detail.id;
    document.getElementById("invoice-detail-date").textContent = date;
    document.getElementById("invoice-detail-status").textContent =
      statusInfo.text;
    document.getElementById(
      "invoice-detail-status"
    ).className = `font-bold ${statusInfo.class} p-1 rounded`;
    document.getElementById("invoice-detail-total").textContent =
      formatCurrency(detail.total_amount);

    // 2. Cập nhật danh sách items
    const tbody = document.getElementById("invoice-items-table-body");
    tbody.innerHTML = detail.items
      .map(
        (item) => `
            <tr>
                <td class="px-3 py-2 text-sm text-gray-900">${
                  item.description
                }</td>
                <td class="px-3 py-2 text-sm text-right">${item.quantity}</td>
                <td class="px-3 py-2 text-sm text-right">${formatCurrency(
                  item.unit_price
                )}</td>
                <td class="px-3 py-2 text-sm text-right font-medium">${formatCurrency(
                  item.sub_total
                )}</td>
            </tr>
        `
      )
      .join("");

    if (invoiceDetailModal) invoiceDetailModal.classList.remove("hidden");
  } catch (error) {
    console.error("Lỗi khi tải chi tiết hóa đơn:", error);
  }
}
window.showInvoiceDetails = showInvoiceDetails; // Export ra window

// --- PAYMENT HANDLERS ---
window.currentTransaction = null;

function showPaymentModal(invoiceId, amount, status) {
  if (status === "paid") {
    showToast("Hóa đơn này đã được thanh toán.", true);
    return;
  }

  // Reset và hiển thị modal
  document.getElementById("payment-modal").classList.remove("hidden");
  document
    .getElementById("payment-method-selection")
    .classList.remove("hidden");
  document.getElementById("payment-details-container").classList.add("hidden");
  document.getElementById("qr-code-display").classList.add("hidden");
  document.getElementById("bank-info-display").classList.add("hidden");

  // Cập nhật thông tin hóa đơn
  document.getElementById("payment-invoice-id").textContent = invoiceId;
  document.getElementById("payment-amount").textContent =
    formatCurrency(amount);

  // Gán tạm invoiceId cho modal
  document.getElementById("payment-modal").dataset.invoiceId = invoiceId;
}
window.showPaymentModal = showPaymentModal;

function closePaymentModal() {
  document.getElementById("payment-modal").classList.add("hidden");
  window.currentTransaction = null;
  showHistory("invoices", document.getElementById("tab-invoices")); // Quay lại tab Hóa đơn và tải lại
}
window.closePaymentModal = closePaymentModal;

async function processPayment(method) {
  const invoiceId = document.getElementById("payment-modal").dataset.invoiceId;

  try {
    // 1. Gọi Finance Service để tạo giao dịch
    // LƯU Ý: Phải truyền amount đi cùng request để tránh deadlock
    const amount = parseFloat(
      document
        .getElementById("payment-amount")
        .textContent.replace(/[^0-9,.]/g, "")
        .replace(",", ".")
    );

    const response = await apiRequestCore(
      TOKEN_KEY,
      `/api/invoices/${invoiceId}/pay`,
      "POST",
      { method, amount } // ✅ ĐÃ SỬA: Truyền cả amount và method
    );

    showToast(response.message || "Đang chờ thanh toán...");
    window.currentTransaction = response.transaction;

    // Lỗi: payment_data là chuỗi JSON, cần parse
    const rawDetails = response.transaction.payment_data;
    const details = JSON.parse(rawDetails);

    // 2. Cập nhật UI
    document.getElementById("payment-method-selection").classList.add("hidden");
    document
      .getElementById("payment-details-container")
      .classList.remove("hidden");
    document.getElementById("payment-detail-title").textContent =
      method === "momo_qr"
        ? "Quét Mã QR Momo"
        : "Thông Tin Chuyển Khoản Ngân Hàng";

    // ✅ Dòng 1222: Hiển thị Mã Giao Dịch thống nhất
    const testCodeToDisplay =
      details.test_code || response.transaction.pg_transaction_id;
    document.getElementById("test-code-display").textContent =
      testCodeToDisplay;

    if (method === "momo_qr") {
      document.getElementById("bank-info-display").classList.add("hidden");
      document.getElementById("qr-code-display").classList.remove("hidden");

      // ✅ Dòng 1228: Gán URL từ backend (chứa ảnh cá nhân của bạn)
      document.getElementById("qr-image").src =
        details.qr_code_url ||
        "https://via.placeholder.com/150?text=QR+Code+Error";

      document.getElementById("payment-note-qr").textContent =
        details.payment_text;
    } else if (method === "bank_transfer") {
      document.getElementById("qr-code-display").classList.add("hidden");
      document.getElementById("bank-info-display").classList.remove("hidden");
      document.getElementById("bank-name").textContent = details.bank_name;
      document.getElementById("account-name").textContent =
        details.account_name;
      document.getElementById("account-number").textContent =
        details.account_number;
      document.getElementById("amount-bank").textContent = formatCurrency(
        details.amount
      );
      document.getElementById("payment-note-bank").textContent = details.note;
    }
  } catch (error) {
    console.error("Lỗi khi tạo giao dịch thanh toán:", error);
  }
}
window.processPayment = processPayment;

async function simulatePaymentSuccess() {
  if (!window.currentTransaction) {
    showToast("Lỗi mô phỏng: Không có giao dịch đang chờ.", true);
    return;
  }

  // FIX: Lấy PG ID từ object đã parse
  const pgTransactionId = window.currentTransaction.pg_transaction_id;

  if (
    !confirm(
      "Bạn có chắc chắn muốn mô phỏng giao dịch thành công? Hành động này sẽ cập nhật hóa đơn thành 'paid'."
    )
  )
    return;

  try {
    // Gọi Mock Webhook API (Endpoint public của Payment Service)
    await apiRequestCore(null, "/api/payments/webhook", "POST", {
      pg_transaction_id: pgTransactionId,
      status: "success",
    });

    showToast("✅ Mô phỏng thanh toán thành công! Hóa đơn đã được cập nhật.");
    closePaymentModal();
  } catch (error) {
    console.error("Lỗi mô phỏng webhook:", error);
  }
}
window.simulatePaymentSuccess = simulatePaymentSuccess;
