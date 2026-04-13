let orders = [];
let currentIndex = null;

// ===== LOAD =====
async function loadOrders() {
    let res = await fetch("/orders?t=" + Date.now()); // 🔥 chống cache
    orders = await res.json();
    renderList();
}

// ===== ADD =====
async function add() {
    let code = document.getElementById("code").value.trim().toUpperCase();
    let note = document.getElementById("note").value;

    if (!code) return;

    await fetch("/orders/add", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({code, note})
    });

    document.getElementById("code").value = "";
    document.getElementById("note").value = "";

    loadOrders();
}

// ===== DELETE =====
async function remove(code) {
    if (!confirm("Xoá đơn này?")) return;

    orders = orders.filter(o => o.code !== code);
    renderList();

    await fetch("/orders/delete", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({code})
    });
}

// ===== RENDER LIST =====
function renderList() {
    let html = "";

    orders.forEach((o, i) => {

        let isActive = i === currentIndex;

        let isNew = o.last_time && (
            !o.seen_time || o.last_time > o.seen_time
        );

        html += `
        <div class="order ${isActive ? 'active' : ''}" onclick="view(${i})">

            ${isNew ? '<div class="badge"></div>' : ''}

            <div class="order-content">
                <b>${o.note || "Không tên"}</b><br>
                <small>${o.code}</small>
            </div>

            <div class="delete-btn" onclick="event.stopPropagation(); remove('${o.code}')">
                <svg viewBox="0 0 24 24">
                    <path d="M6 6l12 12M18 6l-12 12"
                        stroke="currentColor" stroke-width="2" fill="none"/>
                </svg>
            </div>

        </div>`;
    });

    document.getElementById("list").innerHTML = html;
}

// ===== VIEW =====
async function view(index) {
    currentIndex = index;
    let order = orders[index];

    // 🔥 mark seen ngay lập tức (UI mượt)
    order.seen_time = order.last_time;
    renderList();

    // 🔥 sync backend
    fetch("/orders/seen", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({code: order.code})
    });

    document.getElementById("title").innerText =
        `📦 ${order.note || ""} (${order.code})`;

    let res = await fetch("/track_one", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ tracking_number: order.code })
    });

    let data = await res.json();

    renderDetail(data);
}

// ===== FORMAT TIME =====
function formatTime(epoch) {
    return new Date(epoch * 1000).toLocaleString();
}

// ===== TIMELINE =====
function renderDetail(records) {
    let html = "";

    records.forEach((r, i) => {
        html += `
        <div class="item ${i===0 ? 'latest' : ''}">
            <div class="time">${formatTime(r.actual_time)}</div>
            <div class="title">${r.buyer_description}</div>
        </div>`;
    });

    document.getElementById("detail").innerHTML = html;
}

// ===== AUTO REFRESH =====
setInterval(() => {
    loadOrders(); // 🔥 reload để detect trạng thái mới
}, 15000);

// ===== INIT =====
loadOrders();