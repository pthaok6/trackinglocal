import json
import asyncio
from datetime import datetime
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    CallbackQueryHandler, MessageHandler,
    ContextTypes, filters
)
from services.spx_api import get_tracking

TOKEN = "8741593712:AAH51E7aCW5GgCXOd0RyuOgmWKVJ8cKmVUM"
DATA_FILE = "data/orders.json"

# ===== STORAGE =====
def load_orders():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_orders(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ===== UTIL =====
def format_time(epoch):
    return datetime.fromtimestamp(epoch).strftime("%H:%M %d/%m")

def build_timeline(records):
    msg = "📍 Hành trình đơn hàng:\n\n"

    reversed_records = list(reversed(records[:5]))

    for i, r in enumerate(reversed_records):
        time = format_time(r["actual_time"])
        title = r["buyer_description"]

        is_latest = (i == len(reversed_records) - 1)

        if is_latest:
            msg += f"🟢 {time}\n🔥 {title}\n\n"
        else:
            msg += f"⚪ {time}\n{title}\n\n"

    return msg

# ===== MENU =====
def main_menu():
    keyboard = [
        ["➕ Thêm đơn"],
        ["📦 Xem đơn"],
        ["🌐 Xem trên web"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ===== START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id

    users = context.application.bot_data.get("users", [])
    if user_id not in users:
        users.append(user_id)
        context.application.bot_data["users"] = users
    await update.message.reply_text(
        "📦 Tracking Bot",
        reply_markup=main_menu()
    )

# ===== THÊM ĐƠN =====
async def add_order_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Nhập: mã + ghi chú")

    context.user_data["adding"] = True

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # ===== ADD FLOW =====
    if context.user_data.get("adding"):
        if " " not in text:
            await update.message.reply_text("❌ Sai format: mã ghi chú")
            return

        code, note = [x.strip() for x in text.split(" ", 1)]

        orders = load_orders()
        orders.append({"code": code, "note": note})
        save_orders(orders)

        context.user_data["adding"] = False

        await update.message.reply_text("✅ Đã thêm", reply_markup=main_menu())
        return

    # ===== MENU CLICK =====
    if text == "➕ Thêm đơn":
        await add_order_prompt(update, context)

    elif text == "📦 Xem đơn":
        await list_orders(update, context)

    elif text == "🌐 Xem trên web":
       WEB_URL = "http://localhost:5001"
    
       keyboard = [
           [InlineKeyboardButton("🚀 Open Web App", url=WEB_URL)]
        ]
       await update.message.reply_text(
        "👉 Click để mở web:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
# ===== LIST + INLINE BUTTON =====
async def list_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    orders = load_orders()

    if not orders:
        await update.message.reply_text("📭 Chưa có đơn")
        return

    keyboard = []

    for i, o in enumerate(orders):
        keyboard.append([
            InlineKeyboardButton(
                f"{o['note']} {o['code'][:3]}",
                callback_data=f"view_{i}"
            ),
            InlineKeyboardButton(
                "❌",
                callback_data=f"delete_{i}"
            )
        ])

    await update.message.reply_text(
        "📦 Danh sách các đơn hàng đang theo dõi:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ===== HANDLE BUTTON =====
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    orders = load_orders()

    # ===== VIEW =====
    if data.startswith("view_"):
        idx = int(data.split("_")[1])

        if idx >= len(orders):
            await query.edit_message_text("❌ Không tồn tại")
            return

        order = orders[idx]

        data_api = get_tracking(order["code"])

        try:
            records = data_api["data"]["sls_tracking_info"]["records"]
        except:
            await query.edit_message_text("❌ Lỗi tracking")
            return

        msg = f"📦 {order['note']}\n{order['code']}\n\n"
        msg += build_timeline(records)

        keyboard = []
        row = []

        # 🔁 các đơn khác
        for i, o in enumerate(orders):
            if i != idx:
                row.append(
                    InlineKeyboardButton(
                        o["note"][:10],
                        callback_data=f"view_{i}"
                    )
                )

        if row:
            keyboard.append(row)

        # ❌ xoá đơn hiện tại
        keyboard.append([
            InlineKeyboardButton("❌ Xoá đơn này", callback_data=f"delete_{idx}")
        ])

        await query.edit_message_text(
            msg,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # ===== DELETE =====
    elif data.startswith("delete_"):
        idx = int(data.split("_")[1])

        if idx >= len(orders):
            await query.edit_message_text("❌ Không tồn tại")
            return

        removed = orders.pop(idx)
        save_orders(orders)

        if not orders:
            await query.edit_message_text("📭 Hết đơn")
            return

        new_idx = 0
        new_order = orders[new_idx]

        data_api = get_tracking(new_order["code"])
        records = data_api["data"]["sls_tracking_info"]["records"]

        msg = f"🗑 Đã xoá {removed['note']}\n\n"
        msg += f"📦 {new_order['note']}\n{new_order['code']}\n\n"
        msg += build_timeline(records)

        keyboard = []
        row = []

        for i, o in enumerate(orders):
            if i != new_idx:
                row.append(
                    InlineKeyboardButton(
                        o["note"][:10],
                        callback_data=f"view_{i}"
                    )
                )

        if row:
            keyboard.append(row)

        keyboard.append([
            InlineKeyboardButton("❌ Xoá đơn này", callback_data=f"delete_{new_idx}")
        ])

        await query.edit_message_text(
            msg,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        #==== CHECK UPDATE ====
async def check_updates(app):
    while True:
        orders = load_orders()
        changed = False

        for o in orders:
            try:
                data = get_tracking(o["code"])
                records = data["data"]["sls_tracking_info"]["records"]

                latest = records[0]  # record mới nhất
                latest_time = latest["actual_time"]

                # nếu chưa có last_time → set luôn
                if "last_time" not in o:
                    o["last_time"] = latest_time
                    changed = True
                    continue

                # nếu có update
                if latest_time > o["last_time"]:
                    o["last_time"] = latest_time
                    changed = True

                    msg = f"📦 {o['note']}\n{o['code']}\n\n"
                    msg += f"🔔 Cập nhật mới:\n{latest['buyer_description']}"

                    # 🔥 gửi cho tất cả user đã chat bot
                    for user_id in app.bot_data.get("users", []):
                        await app.bot.send_message(user_id, msg)

            except Exception as e:
                print("ERROR:", e)

        if changed:
            save_orders(orders)

        await asyncio.sleep(60)  # check mỗi 30s
        
async def post_init(app):
    print("Bot started + background task running...")
    app.create_task(check_updates(app))

# ===== RUN =====
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
#ADD
async def add_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        _, code, note = update.message.text.split(" ", 2)

        orders = load_orders()
        orders.append({"code": code, "note": note})
        save_orders(orders)

        await update.message.reply_text(f"✅ Đã thêm:\n{note} ({code})")

    except:
        await update.message.reply_text("❌ Format: /add CODE NOTE")

app.add_handler(CommandHandler("add", add_cmd))                
app.add_handler(CallbackQueryHandler(handle_button))
app.add_handler(CommandHandler("list", list_orders))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))


    
# 🔥 chạy background
app.post_init = post_init

app.run_polling()
