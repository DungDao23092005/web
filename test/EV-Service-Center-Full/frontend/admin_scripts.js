// ===================== GLOBAL CONFIG =====================
window.ADMIN_TOKEN_KEY = "admin_jwt_token";
window.ADMIN_ROLE = "admin";

// ===================== UI UTILITIES =====================
window.showToast = function (message, isError = false) {
  const toast = document.createElement("div");
  toast.textContent = message;
  toast.className = `fixed bottom-5 right-5 px-4 py-3 rounded-md text-white font-medium shadow-lg z-50 transition-all duration-500 ${
    isError ? "bg-red-500" : "bg-green-500"
  }`;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
};

window.showLoading = function () {
  document.getElementById("loading-spinner")?.classList.remove("hidden");
};
window.hideLoading = function () {
  document.getElementById("loading-spinner")?.classList.add("hidden");
};

// --- Helper: Định dạng tiền tệ (BỔ SUNG) ---
function formatCurrency(amount) {
  return new Intl.NumberFormat("vi-VN").format(amount) + "₫";
}

// --- Helper: Định dạng trạng thái thanh toán (BỔ SUNG) ---
function formatPaymentStatus(status) {
  switch (status) {
    case "pending":
      return { text: "Chờ thanh toán", class: "bg-yellow-100 text-yellow-800" };
    case "success":
      return { text: "Thành công", class: "bg-green-100 text-green-800" };
    case "failed":
      return { text: "Thất bại", class: "bg-red-100 text-red-800" };
    case "expired":
      return { text: "Hết hạn", class: "bg-gray-100 text-gray-800" };
    default:
      return { text: status, class: "bg-gray-100 text-gray-800" };
  }
}

// ===================== ADMIN CORE FUNCTIONS =====================
const loginPage = document.getElementById("admin-login-page");
const dashboardPage = document.getElementById("dashboard");
const dashboardTitle = document.getElementById("dashboard-title");

function adminLogout() {
  localStorage.removeItem(window.ADMIN_TOKEN_KEY);
  window.showToast(
    "Phiên làm việc hết hạn hoặc không hợp lệ. Vui lòng đăng nhập lại.",
    true
  );
  // Đảm bảo navigate về trang login
  loginPage.classList.remove("hidden");
  dashboardPage.classList.add("hidden");
}
window.adminLogout = adminLogout; // Xuất ra window để có thể gọi từ bên ngoài

function showDashboard() {
  loginPage.classList.add("hidden");
  dashboardPage.classList.remove("hidden");
}

// ===================== CORE REQUEST FUNCTION (UPDATED) =====================
window.apiRequestCore = async function (
  tokenKey,
  endpoint,
  method = "GET",
  body = null
) {
  // API_BASE_URL không được định nghĩa trong file này, dùng window.location.origin
  const url = `${window.location.origin}${endpoint}`;
  const token = tokenKey ? localStorage.getItem(tokenKey) : null;

  const options = {
    method: method?.toString().toUpperCase() || "GET",
    headers: { "Content-Type": "application/json" },
  };

  if (token) options.headers["Authorization"] = `Bearer ${token}`;
  if (body) options.body = JSON.stringify(body);

  try {
    showLoading();
    const response = await fetch(url, options);
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      // ✅ THÊM LOGIC XỬ LÝ LỖI 401
      if (response.status === 401 && token) {
        adminLogout();
        // Ném lỗi để dừng xử lý tiếp theo và thoát khỏi khối try
        throw new Error("Token Admin hết hạn.");
      }

      console.error("API Error:", data);
      // Hiển thị toast cho các lỗi khác (400, 403, 404, 409,...)
      const errorMessage =
        data.message || data.error || `HTTP Error ${response.status}`;
      window.showToast(errorMessage || "Lỗi hệ thống!", true);

      throw new Error(errorMessage || "API Error");
    }

    return data;
  } catch (err) {
    console.error("🚨 API Request Error:", err);
    // Không show toast ở đây vì nó đã được xử lý trong khối if (!response.ok)
    throw err;
  } finally {
    hideLoading();
  }
};

// ===================== NAVIGATION LOGIC =====================

/**
 * Chuyển đổi giữa các phần Users, Inventory, Bookings, Invoices, Maintenance và Payment History
 */
function navigateToDashboardSection(sectionId, title) {
  document.querySelectorAll(".dashboard-section").forEach((section) => {
    section.classList.add("hidden");
    section.classList.remove("active");
  });

  const activeSection = document.getElementById(sectionId);
  if (activeSection) {
    activeSection.classList.remove("hidden");
    activeSection.classList.add("active");
    if (dashboardTitle) dashboardTitle.textContent = title;
  }

  // Tải dữ liệu tùy thuộc vào section
  if (sectionId === "inventory-section") {
    loadAllInventory();
  } else if (sectionId === "users-section") {
    loadAllUsers();
  } else if (sectionId === "bookings-section") {
    loadAllBookings();
  } else if (sectionId === "invoices-section") {
    loadAllInvoices();
  }
  // ✅ TẢI DỮ LIỆU MAINTENANCE
  else if (sectionId === "maintenance-section") {
    loadAllMaintenanceTasks();
  }
  // ✅ TẢI DỮ LIỆU PAYMENT HISTORY
  else if (sectionId === "payment-history-section") {
    loadAllPaymentHistory();
  }
}
window.navigateToDashboardSection = navigateToDashboardSection;

// ===================== LOGIN HANDLER =====================
document
  .getElementById("admin-login-form")
  ?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email_username = document.getElementById("admin-email").value;
    const password = document.getElementById("admin-password").value;

    try {
      // Gọi API login (không dùng tokenKey)
      const data = await window.apiRequestCore(null, "/api/login", "POST", {
        email_username,
        password,
      });
      const token = data.access_token;

      const payload = JSON.parse(atob(token.split(".")[1]));
      if (payload.role !== window.ADMIN_ROLE) {
        adminLogout();
        window.showToast("Bạn không có quyền truy cập trang quản trị.", true);
        return;
      }

      localStorage.setItem(window.ADMIN_TOKEN_KEY, token);
      window.showToast("Đăng nhập quản trị thành công!");
      showDashboard();
      // CHUYỂN MẶC ĐỊNH SANG INVENTORY
      navigateToDashboardSection("inventory-section", "Quản lý Kho Phụ Tùng");
    } catch (error) {
      console.error("Login failed:", error);
    }
  });

// ===================== USER MANAGEMENT =====================
async function loadAllUsers() {
  try {
    const users = await window.apiRequestCore(
      window.ADMIN_TOKEN_KEY,
      "/api/admin/users"
    );
    const tbody = document.getElementById("users-table-body");
    tbody.innerHTML = "";

    if (!users || users.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center text-gray-500 py-4">Không có người dùng.</td></tr>`;
      return;
    }

    tbody.innerHTML = users
      .map(
        (u) => `
            <tr>
                <td class="px-6 py-4 text-sm">${u.user_id}</td>
                <td class="px-6 py-4 text-sm">${u.username}</td>
                <td class="px-6 py-4 text-sm">${u.email}</td>
                <td class="px-6 py-4 text-sm">${u.role}</td>
                <td class="px-6 py-4 text-sm">${u.status}</td>
                <td class="px-6 py-4 text-center space-x-2">
                    <button onclick="toggleUserLock(${
                      u.user_id
                    })" class="text-indigo-600 hover:text-indigo-900">
                        ${u.status === "active" ? "Lock" : "Unlock"}
                    </button>
                    <button onclick="deleteUser(${
                      u.user_id
                    })" class="text-red-600 hover:text-red-900">Delete</button>
                </td>
            </tr>`
      )
      .join("");
  } catch (err) {
    console.error(err);
    document.getElementById(
      "users-table-body"
    ).innerHTML = `<tr><td colspan="6" class="text-center text-red-500 py-4">Lỗi khi tải dữ liệu người dùng.</td></tr>`;
  }
}
async function toggleUserLock(userId) {
  try {
    await window.apiRequestCore(
      window.ADMIN_TOKEN_KEY,
      `/api/admin/users/${userId}/toggle-lock`,
      "PUT"
    );
    window.showToast("Cập nhật trạng thái người dùng thành công.");
    loadAllUsers();
  } catch (error) {
    console.error("Lỗi khi khóa/mở khóa user:", error);
    // Toast được hiển thị trong apiRequestCore
  }
}

async function deleteUser(userId) {
  if (!confirm("Bạn có chắc chắn muốn xóa người dùng này?")) return;

  try {
    await window.apiRequestCore(
      window.ADMIN_TOKEN_KEY,
      `/api/admin/users/${userId}`,
      "DELETE"
    );
    window.showToast("Đã xóa người dùng!");
    loadAllUsers();
  } catch (error) {
    // Toast được hiển thị trong apiRequestCore
  }
}
window.deleteUser = deleteUser;
window.toggleUserLock = toggleUserLock; // Cần export cho onclick

// XỬ LÝ MODAL THÊM NGƯỜI DÙNG
const addUserModal = document.getElementById("add-user-modal");
function openAddUserModal() {
  if (addUserModal) addUserModal.classList.remove("hidden");
}
window.openAddUserModal = openAddUserModal; // Export cho onclick

function closeAddUserModal() {
  if (addUserModal) addUserModal.classList.add("hidden");
  document.getElementById("add-user-form")?.reset();
}
window.closeAddUserModal = closeAddUserModal; // Export cho onclick

document
  .getElementById("add-user-form")
  ?.addEventListener("submit", async (e) => {
    e.preventDefault();

    const username = document.getElementById("add-username").value;
    const email = document.getElementById("add-email").value;
    const password = document.getElementById("add-password").value;
    const role = document.getElementById("add-role").value;

    try {
      await window.apiRequestCore(
        window.ADMIN_TOKEN_KEY,
        "/api/admin/users",
        "POST",
        { username, email, password, role }
      );

      window.showToast("Tạo người dùng thành công!");
      closeAddUserModal();
      loadAllUsers();
    } catch (error) {
      console.error("Lỗi khi tạo người dùng:", error);
    }
  });

// ===================== INVENTORY MANAGEMENT =====================
// --- LOAD INVENTORY ---
async function loadAllInventory() {
  try {
    const items = await window.apiRequestCore(
      window.ADMIN_TOKEN_KEY,
      "/api/inventory/items" // Endpoint GET ALL ITEMS
    );
    const tbody = document.getElementById("inventory-table-body");
    tbody.innerHTML = "";

    if (!items || items.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center text-gray-500 py-4">Không có vật tư nào trong kho.</td></tr>`;
      return;
    }

    tbody.innerHTML = items
      .map((item) => {
        // Logic hiển thị tồn kho thấp
        const isLowStock = item.quantity <= item.min_quantity;
        const rowClass = isLowStock
          ? "bg-red-50 hover:bg-red-100"
          : "hover:bg-gray-50";
        const statusBadge = isLowStock
          ? '<span class="p-1 rounded-full text-xs font-semibold bg-red-100 text-red-800">Cần bổ sung</span>'
          : '<span class="p-1 rounded-full text-xs font-semibold bg-green-100 text-green-800">Đủ hàng</span>';

        return `
                    <tr class="${rowClass}">
                        <td class="px-6 py-4 text-sm">${item.id}</td>
                        <td class="px-6 py-4 text-sm">${item.name}</td>
                        <td class="px-6 py-4 text-sm">${item.part_number}</td>
                        <td class="px-6 py-4 text-sm text-center font-bold">${
                          item.quantity
                        }</td>
                        <td class="px-6 py-4 text-sm text-center">${
                          item.min_quantity
                        }</td>
                        <td class="px-6 py-4 text-sm">${new Intl.NumberFormat(
                          "vi-VN"
                        ).format(item.price)}₫</td>
                        <td class="px-6 py-4 text-center space-x-2">
                            ${statusBadge}
                            <button onclick="openItemModal('edit', ${
                              item.id
                            })" class="text-indigo-600 hover:text-indigo-900">
                                Edit
                            </button>
                            <button onclick="deleteItem(${
                              item.id
                            })" class="text-red-600 hover:text-red-900">
                                Delete
                            </button>
                        </td>
                    </tr>`;
      })
      .join("");
  } catch (err) {
    console.error(err);
    document.getElementById(
      "inventory-table-body"
    ).innerHTML = `<tr><td colspan="7" class="text-center text-red-500 py-4">Lỗi khi tải dữ liệu Kho.</td></tr>`;
  }
}
window.loadAllInventory = loadAllInventory; // Export cho onclick Load lại

// --- MODAL HANDLERS ---
const itemModal = document.getElementById("item-modal");
const itemForm = document.getElementById("item-form");
const itemModalTitle = document.getElementById("item-modal-title");
const itemSubmitButton = document.getElementById("item-submit-button");

function closeItemModal() {
  if (itemModal) itemModal.classList.add("hidden");
  itemForm?.reset();
  document.getElementById("item-id-hidden").value = "";
}
window.closeItemModal = closeItemModal; // Export cho onclick

async function openItemModal(mode, itemId = null) {
  itemForm.dataset.mode = mode;
  itemForm.reset();

  if (mode === "add") {
    itemModalTitle.textContent = "Thêm Vật tư Mới";
    itemSubmitButton.textContent = "Thêm";
    document.getElementById("item-part-number").disabled = false;
    if (itemModal) itemModal.classList.remove("hidden");
  } else if (mode === "edit" && itemId) {
    itemModalTitle.textContent = "Chỉnh Sửa Vật tư";
    itemSubmitButton.textContent = "Lưu Thay Đổi";
    document.getElementById("item-id-hidden").value = itemId;

    try {
      const item = await window.apiRequestCore(
        window.ADMIN_TOKEN_KEY,
        `/api/inventory/items/${itemId}`
      );

      document.getElementById("item-name").value = item.name;
      document.getElementById("item-part-number").value = item.part_number;
      document.getElementById("item-part-number").disabled = true;
      document.getElementById("item-quantity").value = item.quantity;
      document.getElementById("item-min-quantity").value = item.min_quantity;
      document.getElementById("item-price").value = item.price;

      if (itemModal) itemModal.classList.remove("hidden");
    } catch (error) {
      // Toast đã được xử lý trong apiRequestCore
    }
  }
}
window.openItemModal = openItemModal; // Export cho onclick

// --- FORM SUBMIT HANDLER (Add/Edit) ---
itemForm?.addEventListener("submit", async (e) => {
  e.preventDefault();

  const mode = itemForm.dataset.mode;
  const itemId = document.getElementById("item-id-hidden").value;

  const data = {
    name: document.getElementById("item-name").value,
    part_number: document.getElementById("item-part-number").value,
    quantity: parseInt(document.getElementById("item-quantity").value),
    min_quantity: parseInt(document.getElementById("item-min-quantity").value),
    price: parseFloat(document.getElementById("item-price").value),
  };

  try {
    if (mode === "add") {
      await window.apiRequestCore(
        window.ADMIN_TOKEN_KEY,
        "/api/inventory/items",
        "POST",
        data
      );
      window.showToast("Thêm vật tư thành công!");
    } else if (mode === "edit" && itemId) {
      delete data.part_number;

      await window.apiRequestCore(
        window.ADMIN_TOKEN_KEY,
        `/api/inventory/items/${itemId}`,
        "PUT",
        data
      );
      window.showToast("Cập nhật vật tư thành công!");
    }

    closeItemModal();
    loadAllInventory(); // Tải lại bảng
  } catch (error) {
    console.error("Lỗi khi lưu vật tư:", error);
  }
});

// --- DELETE FUNCTION ---
async function deleteItem(itemId) {
  if (!confirm(`Bạn có chắc chắn muốn xóa vật tư có ID ${itemId} này không?`))
    return;

  try {
    await window.apiRequestCore(
      window.ADMIN_TOKEN_KEY,
      `/api/inventory/items/${itemId}`,
      "DELETE"
    );
    window.showToast("Đã xóa vật tư!");
    loadAllInventory();
  } catch (error) {
    // Toast đã được xử lý trong apiRequestCore
  }
}
window.deleteItem = deleteItem; // Cần export hàm này ra window để HTML có thể gọi

// ========================================================
// ✅ LOGIC MAINTENANCE MANAGEMENT (MỚI)
// ========================================================

/**
 * Helper: Định dạng trạng thái công việc
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
 * 1. Tải tất cả công việc bảo trì
 */
async function loadAllMaintenanceTasks() {
  const tbody = document.getElementById("maintenance-table-body");
  if (!tbody) return;
  tbody.innerHTML =
    '<tr><td colspan="7" class="text-center text-gray-500 py-4">Đang tải dữ liệu...</td></tr>';

  try {
    const tasks = await window.apiRequestCore(
      window.ADMIN_TOKEN_KEY,
      "/api/maintenance/tasks", // Endpoint GET ALL TASKS
      "GET"
    );

    if (!tasks || tasks.length === 0) {
      tbody.innerHTML =
        '<tr><td colspan="7" class="text-center text-gray-500 py-4">Không có công việc bảo trì nào.</td></tr>';
      return;
    }

    tbody.innerHTML = tasks
      .map((task) => {
        const statusInfo = formatMaintenanceStatus(task.status);
        const disabled =
          task.status === "completed" || task.status === "failed"
            ? "disabled"
            : "";

        return `
                    <tr id="maintenance-row-${task.id}">
                        <td class="px-6 py-4 text-sm">${task.id}</td>
                        <td class="px-6 py-4 text-sm">${task.booking_id}</td>
                        <td class="px-6 py-4 text-sm">${task.description}</td>
                        <td class="px-6 py-4 text-sm font-mono">${
                          task.vehicle_vin
                        }</td>
                        <td class="px-6 py-4 text-sm">KTV ID: ${
                          task.technician_id
                        }</td>
                        <td class="px-6 py-4 text-sm">
                            <select 
                                class="status-select border rounded p-1 text-xs ${
                                  statusInfo.class
                                }" 
                                data-task-id="${task.id}" 
                                onchange="updateTaskStatus(${
                                  task.id
                                }, this.value)"
                                ${disabled}>
                                <option value="pending" ${
                                  task.status === "pending" ? "selected" : ""
                                }>Chờ thực hiện</option>
                                <option value="in_progress" ${
                                  task.status === "in_progress"
                                    ? "selected"
                                    : ""
                                }>Đang tiến hành</option>
                                <option value="completed" ${
                                  task.status === "completed" ? "selected" : ""
                                }>Hoàn thành</option>
                                <option value="failed" ${
                                  task.status === "failed" ? "selected" : ""
                                }>Thất bại/Hủy</option>
                            </select>
                        </td>
                        <td class="px-6 py-4 text-center space-x-2">
                            ${
                              disabled
                                ? '<span class="text-gray-400">Đã khóa</span>'
                                : "<button onclick=\"if(confirm('Chuyển trạng thái sang hoàn thành?')) updateTaskStatus(" +
                                  task.id +
                                  ', \'completed\')" class="text-green-600 hover:text-green-900">Hoàn Thành</button>'
                            }
                        </td>
                    </tr>
                `;
      })
      .join("");
  } catch (err) {
    console.error(err);
    tbody.innerHTML =
      '<tr><td colspan="7" class="text-center text-red-500 py-4">Lỗi khi tải dữ liệu Công việc Bảo trì.</td></tr>';
  }
}
window.loadAllMaintenanceTasks = loadAllMaintenanceTasks;

/**
 * 2. Cập nhật trạng thái công việc
 */
async function updateTaskStatus(taskId, newStatus) {
  if (
    !confirm(
      `Bạn có chắc muốn cập nhật trạng thái của Công việc ${taskId} thành ${newStatus.toUpperCase()}?`
    )
  ) {
    loadAllMaintenanceTasks(); // Tải lại để revert nếu người dùng hủy
    return;
  }

  try {
    await window.apiRequestCore(
      window.ADMIN_TOKEN_KEY,
      `/api/maintenance/tasks/${taskId}/status`,
      "PUT",
      { status: newStatus }
    );
    window.showToast("Cập nhật trạng thái công việc thành công!");
    loadAllMaintenanceTasks(); // Tải lại bảng
  } catch (error) {
    // Toast đã được xử lý trong apiRequestCore
    loadAllMaintenanceTasks(); // Tải lại để reset trạng thái
    console.error("Lỗi cập nhật trạng thái công việc:", error);
  }
}
window.updateTaskStatus = updateTaskStatus;

// --- MODAL TẠO TASK HANDLERS ---
const createTaskModal = document.getElementById("create-task-modal");

function closeCreateTaskModal() {
  if (createTaskModal) createTaskModal.classList.add("hidden");
  document.getElementById("create-task-form")?.reset();
}
window.closeCreateTaskModal = closeCreateTaskModal;

function openCreateTaskModal() {
  if (createTaskModal) createTaskModal.classList.remove("hidden");
}
window.openCreateTaskModal = openCreateTaskModal;

document
  .getElementById("create-task-form")
  ?.addEventListener("submit", async (e) => {
    e.preventDefault();

    const bookingId = parseInt(
      document.getElementById("task-booking-id")?.value
    );
    const technicianId = parseInt(
      document.getElementById("task-technician-id")?.value
    );

    if (isNaN(bookingId) || isNaN(technicianId)) {
      window.showToast("Booking ID và Technician ID phải là số hợp lệ.", true);
      return;
    }

    try {
      const data = await window.apiRequestCore(
        window.ADMIN_TOKEN_KEY,
        "/api/maintenance/tasks",
        "POST",
        {
          booking_id: bookingId,
          technician_id: technicianId,
        }
      );

      window.showToast(data.message || "Tạo công việc thành công!");
      closeCreateTaskModal();
      loadAllMaintenanceTasks();
    } catch (error) {
      console.error("Lỗi khi tạo công việc:", error);
    }
  });
// ========================================================
// ✅ LOGIC PAYMENT HISTORY MANAGEMENT (MỚI)
// ========================================================

/**
 * Helper: Định dạng tiền tệ
 */
function formatCurrency(amount) {
  return new Intl.NumberFormat("vi-VN").format(amount) + "₫";
}

// [DÁN LẠI ĐỊNH NGHĨA formatPaymentStatus CHO RÕ RÀNG TRONG BẢN CUỐI CÙNG]
// function formatPaymentStatus(status) { ... }
// Đã được định nghĩa ở trên, chỉ giữ lại định nghĩa này thôi.

/**
 * 1. Tải tất cả lịch sử thanh toán (Admin)
 */
async function loadAllPaymentHistory() {
  const tbody = document.getElementById("payment-history-table-body");
  if (!tbody) return;
  tbody.innerHTML =
    '<tr><td colspan="7" class="text-center text-gray-500 py-4">Đang tải dữ liệu...</td></tr>';

  try {
    const history = await window.apiRequestCore(
      window.ADMIN_TOKEN_KEY,
      "/api/payments/history/all", // Endpoint GET ALL PAYMENT HISTORY
      "GET"
    );

    if (!history || history.length === 0) {
      tbody.innerHTML =
        '<tr><td colspan="7" class="text-center text-gray-500 py-4">Không có giao dịch nào.</td></tr>';
      return;
    }

    tbody.innerHTML = history
      .map((t) => {
        const statusInfo = formatPaymentStatus(t.status);

        return `
                    <tr class="hover:bg-gray-50">
                        <td class="px-6 py-4 text-sm font-semibold">${t.id}</td>
                        <td class="px-6 py-4 text-sm">${t.invoice_id}</td>
                        <td class="px-6 py-4 text-sm">${t.user_id}</td>
                        <td class="px-6 py-4 text-sm font-bold text-red-600">${formatCurrency(
                          t.amount
                        )}</td>
                        <td class="px-6 py-4 text-sm uppercase">${t.method}</td>
                        <td class="px-6 py-4 text-sm font-mono">${
                          t.pg_transaction_id
                        }</td>
                        <td class="px-6 py-4 text-sm">
                            <span class="p-1 rounded-full text-xs font-semibold ${
                              statusInfo.class
                            }">
                                ${statusInfo.text}
                            </span>
                        </td>
                    </tr>
                `;
      })
      .join("");
  } catch (err) {
    console.error(err);
    tbody.innerHTML =
      '<tr><td colspan="7" class="text-center text-red-500 py-4">Lỗi khi tải dữ liệu Lịch sử Thanh toán.</td></tr>';
  }
}
window.loadAllPaymentHistory = loadAllPaymentHistory;
// ========================================================
// LOGIC BOOKING MANAGEMENT
// ... (GIỮ NGUYÊN HOẶC KHÔNG DÁN LẠI NẾU KHÔNG CÓ THAY ĐỔI)
// ========================================================
// Hàm Helper: Định dạng trạng thái hiển thị
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

// 1. Tải tất cả lịch hẹn
async function loadAllBookings() {
  const tbody = document.getElementById("bookings-table-body");
  if (!tbody) return;
  tbody.innerHTML =
    '<tr><td colspan="7" class="text-center text-gray-500 py-4">Đang tải dữ liệu...</td></tr>';

  try {
    const bookings = await window.apiRequestCore(
      window.ADMIN_TOKEN_KEY,
      "/api/bookings/items", // Endpoint GET ALL BOOKINGS (Đã bảo vệ)
      "GET"
    );

    if (!bookings || bookings.length === 0) {
      tbody.innerHTML =
        '<tr><td colspan="7" class="text-center text-gray-500 py-4">Không có lịch hẹn nào.</td></tr>';
      return;
    }

    tbody.innerHTML = bookings
      .map((booking) => {
        const startDate = new Date(booking.start_time).toLocaleString("vi-VN", {
          dateStyle: "short",
          timeStyle: "short",
        });
        const endDate = new Date(booking.end_time).toLocaleTimeString("vi-VN", {
          timeStyle: "short",
        });
        const statusInfo = formatBookingStatus(booking.status);

        return `
                    <tr id="booking-row-${booking.id}">
                        <td class="px-6 py-4 text-sm">${booking.id}</td>
                        <td class="px-6 py-4 text-sm">${
                          booking.customer_name
                        } (ID: ${booking.user_id})</td>
                        <td class="px-6 py-4 text-sm">${startDate} - ${endDate}</td>
                        <td class="px-6 py-4 text-sm">${
                          booking.service_type
                        }</td>
                        <td class="px-6 py-4 text-sm">KTV: ${
                          booking.technician_id
                        } / Trạm: ${booking.station_id}</td>
                        <td class="px-6 py-4 text-sm">
                            <select 
                                class="status-select border rounded p-1 text-xs ${
                                  statusInfo.class
                                }" 
                                data-booking-id="${booking.id}" 
                                onchange="updateBookingStatus(${
                                  booking.id
                                }, this.value)">
                                <option value="pending" ${
                                  booking.status === "pending" ? "selected" : ""
                                }>Chờ xác nhận</option>
                                <option value="confirmed" ${
                                  booking.status === "confirmed"
                                    ? "selected"
                                    : ""
                                }>Đã xác nhận</option>
                                <option value="completed" ${
                                  booking.status === "completed"
                                    ? "selected"
                                    : ""
                                }>Hoàn thành</option>
                                <option value="canceled" ${
                                  booking.status === "canceled"
                                    ? "selected"
                                    : ""
                                }>Hủy</option>
                            </select>
                        </td>
                        <td class="px-6 py-4 text-center space-x-2">
                            <button onclick="deleteBooking(${
                              booking.id
                            })" class="text-red-600 hover:text-red-900">Xóa</button>
                        </td>
                    </tr>
                `;
      })
      .join("");
  } catch (err) {
    console.error(err);
    tbody.innerHTML =
      '<tr><td colspan="7" class="text-center text-red-500 py-4">Lỗi khi tải dữ liệu Lịch Hẹn.</td></tr>';
  }
}
window.loadAllBookings = loadAllBookings; // Export ra window cho HTML gọi

// 2. Cập nhật trạng thái
async function updateBookingStatus(bookingId, newStatus) {
  if (
    !confirm(
      `Bạn có chắc muốn cập nhật trạng thái của lịch hẹn ${bookingId} thành ${newStatus.toUpperCase()}?`
    )
  ) {
    loadAllBookings(); // Tải lại để revert nếu người dùng hủy
    return;
  }

  try {
    await window.apiRequestCore(
      window.ADMIN_TOKEN_KEY,
      `/api/bookings/items/${bookingId}/status`,
      "PUT",
      { status: newStatus }
    );
    window.showToast("Cập nhật trạng thái thành công!");
    loadAllBookings(); // Tải lại bảng để cập nhật màu sắc/hiển thị
  } catch (error) {
    // Toast đã được xử lý trong apiRequestCore
    loadAllBookings(); // Tải lại để reset trạng thái
    console.error("Lỗi cập nhật trạng thái:", error);
  }
}
window.updateBookingStatus = updateBookingStatus; // Export ra window cho HTML gọi

// 3. Xóa lịch hẹn
async function deleteBooking(bookingId) {
  if (!confirm(`Bạn có chắc chắn muốn xóa vĩnh viễn lịch hẹn ID ${bookingId}?`))
    return;

  try {
    await window.apiRequestCore(
      window.ADMIN_TOKEN_KEY,
      `/api/bookings/items/${bookingId}`,
      "DELETE"
    );
    window.showToast("Đã xóa lịch hẹn!");

    // Xóa dòng khỏi bảng
    document.getElementById(`booking-row-${bookingId}`)?.remove();
  } catch (error) {
    // Toast đã được xử lý trong apiRequestCore
  }
}
window.deleteBooking = deleteBooking; // Export ra window cho HTML gọi

// ========================================================
// LOGIC INVOICE MANAGEMENT
// ========================================================
// Hàm Helper: Định dạng tiền tệ
function formatCurrency(amount) {
  return new Intl.NumberFormat("vi-VN").format(amount) + "₫";
}

// Hàm Helper: Định dạng trạng thái Hóa đơn
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
    default:
      return { text: status, class: "bg-gray-100 text-gray-800" };
  }
}

// 1. Tải tất cả hóa đơn
async function loadAllInvoices() {
  const tbody = document.getElementById("invoices-table-body");
  if (!tbody) return;
  tbody.innerHTML =
    '<tr><td colspan="6" class="text-center text-gray-500 py-4">Đang tải dữ liệu...</td></tr>';

  try {
    const invoices = await window.apiRequestCore(
      window.ADMIN_TOKEN_KEY,
      "/api/invoices/", // Endpoint GET ALL INVOICES
      "GET"
    );

    if (!invoices || invoices.length === 0) {
      tbody.innerHTML =
        '<tr><td colspan="6" class="text-center text-gray-500 py-4">Không có hóa đơn nào.</td></tr>';
      return;
    }

    tbody.innerHTML = invoices
      .map((invoice) => {
        const statusInfo = formatInvoiceStatus(invoice.status);
        const date = new Date(invoice.created_at).toLocaleDateString("vi-VN");

        return `
                    <tr id="invoice-row-${invoice.id}" class="hover:bg-gray-50">
                        <td class="px-6 py-4 text-sm">${invoice.id}</td>
                        <td class="px-6 py-4 text-sm">${invoice.booking_id}</td>
                        <td class="px-6 py-4 text-sm">${invoice.user_id}</td>
                        <td class="px-6 py-4 text-sm font-semibold text-red-600">${formatCurrency(
                          invoice.total_amount
                        )}</td>
                        <td class="px-6 py-4 text-sm">
                            <select 
                                class="status-select border rounded p-1 text-xs ${
                                  statusInfo.class
                                }" 
                                data-invoice-id="${invoice.id}" 
                                onchange="updateInvoiceStatus(${
                                  invoice.id
                                }, this.value)">
                                <option value="issued" ${
                                  invoice.status === "issued" ? "selected" : ""
                                }>Đã xuất</option>
                                <option value="pending" ${
                                  invoice.status === "pending" ? "selected" : ""
                                }>Chờ thanh toán</option>
                                <option value="paid" ${
                                  invoice.status === "paid" ? "selected" : ""
                                }>Đã thanh toán</option>
                                <option value="canceled" ${
                                  invoice.status === "canceled"
                                    ? "selected"
                                    : ""
                                }>Đã hủy</option>
                            </select>
                        </td>
                        <td class="px-6 py-4 text-center space-x-2">
                            <button onclick="showAdminInvoiceDetails(${
                              invoice.id
                            })" class="text-indigo-600 hover:text-indigo-900">
                                Xem Chi Tiết
                            </button>
                            </td>
                    </tr>
                `;
      })
      .join("");
  } catch (err) {
    console.error(err);
    tbody.innerHTML =
      '<tr><td colspan="6" class="text-center text-red-500 py-4">Lỗi khi tải dữ liệu Hóa Đơn.</td></tr>';
  }
}
window.loadAllInvoices = loadAllInvoices;

// 2. Cập nhật trạng thái hóa đơn
async function updateInvoiceStatus(invoiceId, newStatus) {
  if (
    !confirm(
      `Bạn có chắc muốn cập nhật trạng thái của Hóa Đơn ${invoiceId} thành ${newStatus.toUpperCase()}?`
    )
  ) {
    loadAllInvoices(); // Tải lại để revert nếu người dùng hủy
    return;
  }

  try {
    await window.apiRequestCore(
      window.ADMIN_TOKEN_KEY,
      `/api/invoices/${invoiceId}/status`,
      "PUT",
      { status: newStatus }
    );
    window.showToast("Cập nhật trạng thái thành công!");
    loadAllInvoices(); // Tải lại bảng để cập nhật màu sắc/hiển thị
  } catch (error) {
    // Toast đã được xử lý trong apiRequestCore
    loadAllInvoices(); // Tải lại để reset trạng thái
    console.error("Lỗi cập nhật trạng thái hóa đơn:", error);
  }
}
window.updateInvoiceStatus = updateInvoiceStatus;

// 3. Logic Tạo Hóa Đơn (Từ Booking)
const createInvoiceModal = document.getElementById("create-invoice-modal");
const partsInputContainer = document.getElementById("parts-input-container");

function closeCreateInvoiceModal() {
  if (createInvoiceModal) createInvoiceModal.classList.add("hidden");
  document.getElementById("create-invoice-form")?.reset();
  partsInputContainer.innerHTML = ""; // Clear parts inputs
}
window.closeCreateInvoiceModal = closeCreateInvoiceModal;

function openCreateInvoiceModal() {
  if (createInvoiceModal) createInvoiceModal.classList.remove("hidden");
  // Thêm một input phụ tùng mặc định
  if (partsInputContainer.children.length === 0) {
    addPartInput();
  }
}
window.openCreateInvoiceModal = openCreateInvoiceModal;

function addPartInput() {
  const count = partsInputContainer.children.length + 1;
  const partHtml = `
        <div class="flex space-x-2 part-input-group" data-id="${count}">
            <input
                type="number"
                placeholder="Item ID"
                class="w-1/4 px-3 py-2 border rounded-md shadow-sm"
                name="item_id"
                required
                min="1"
            />
            <input
                type="number"
                placeholder="Số lượng"
                class="w-1/4 px-3 py-2 border rounded-md shadow-sm"
                name="quantity"
                required
                min="1"
                value="1"
            />
            <span class="w-2/4 text-sm text-gray-500 flex items-center">
                (Phụ tùng ${count})
            </span>
            <button type="button" onclick="removePartInput(${count})" class="text-red-500 hover:text-red-700">
                &times;
            </button>
        </div>
    `;
  partsInputContainer.insertAdjacentHTML("beforeend", partHtml);
}
window.addPartInput = addPartInput;

function removePartInput(id) {
  const element = document.querySelector(`.part-input-group[data-id="${id}"]`);
  if (element) element.remove();
}

document
  .getElementById("create-invoice-form")
  ?.addEventListener("submit", async (e) => {
    e.preventDefault();

    const bookingId = parseInt(
      document.getElementById("invoice-booking-id").value
    );

    // Lấy dữ liệu phụ tùng
    const partsData = [];
    const groups = document.querySelectorAll(
      "#parts-input-container .part-input-group"
    );

    groups.forEach((group) => {
      const itemId = parseInt(
        group.querySelector('input[name="item_id"]')?.value
      );
      const quantity = parseInt(
        group.querySelector('input[name="quantity"]')?.value
      );

      if (itemId && quantity && quantity > 0) {
        partsData.push({
          item_id: itemId,
          quantity: quantity,
        });
      }
    });

    try {
      const data = await window.apiRequestCore(
        window.ADMIN_TOKEN_KEY,
        "/api/invoices/",
        "POST",
        {
          booking_id: bookingId,
          parts_data: partsData,
        }
      );

      window.showToast(data.message || "Tạo hóa đơn thành công!");
      closeCreateInvoiceModal();
      loadAllInvoices();
    } catch (error) {
      console.error("Lỗi khi tạo hóa đơn:", error);
    }
  });

// 4. Logic Xem Chi Tiết Hóa Đơn (Admin)
const adminInvoiceDetailModal = document.getElementById(
  "admin-invoice-detail-modal"
);

function closeAdminInvoiceDetailModal() {
  if (adminInvoiceDetailModal) adminInvoiceDetailModal.classList.add("hidden");
}
window.closeAdminInvoiceDetailModal = closeAdminInvoiceDetailModal; // Export ra window

async function showAdminInvoiceDetails(invoiceId) {
  try {
    // API cho Admin cho phép lấy chi tiết (có items)
    const detail = await window.apiRequestCore(
      window.ADMIN_TOKEN_KEY,
      `/api/invoices/${invoiceId}`,
      "GET"
    );

    if (!detail) throw new Error("Không tìm thấy chi tiết hóa đơn.");

    // 1. Cập nhật header/footer
    const statusInfo = formatInvoiceStatus(detail.status);
    const date = new Date(detail.created_at).toLocaleString("vi-VN");

    document.getElementById("admin-invoice-detail-id").textContent = detail.id;
    document.getElementById("admin-invoice-detail-date").textContent = date;
    document.getElementById("admin-invoice-detail-status").textContent =
      statusInfo.text;
    document.getElementById(
      "admin-invoice-detail-status"
    ).className = `font-bold ${statusInfo.class} p-1 rounded`;
    document.getElementById("admin-invoice-detail-total").textContent =
      formatCurrency(detail.total_amount);

    // 2. Cập nhật danh sách items
    const tbody = document.getElementById("admin-invoice-items-table-body");
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

    if (adminInvoiceDetailModal)
      adminInvoiceDetailModal.classList.remove("hidden");
  } catch (error) {
    console.error("Lỗi khi tải chi tiết hóa đơn:", error);
  }
}
window.showAdminInvoiceDetails = showAdminInvoiceDetails; // Export ra window

// --- Khối INIT: Đảm bảo tải Inventory mặc định ---
document.addEventListener("DOMContentLoaded", () => {
  const token = localStorage.getItem(window.ADMIN_TOKEN_KEY);
  if (!token) return;

  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    const valid = payload.exp * 1000 > Date.now();

    if (valid && payload.role === window.ADMIN_ROLE) {
      showDashboard();
      // CHUYỂN TẢI MẶC ĐỊNH SANG INVENTORY SAU KHI PAGE ĐÃ HIỆN
      navigateToDashboardSection("inventory-section", "Quản lý Kho Phụ Tùng");
    } else {
      adminLogout();
    }
  } catch {
    adminLogout();
  }
});
