from flask import Flask, request, jsonify, render_template
from services.spx_api import get_tracking
from services.order_store import load_orders, save_orders

app = Flask(__name__)

# ===== NO CACHE =====
@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store"
    return response

@app.route("/")
def index():
    return render_template("index.html")

# ===== TRACK ONE =====
@app.route("/track_one", methods=["POST"])
def track_one():
    code = request.json.get("tracking_number")

    try:
        data = get_tracking(code)
        records = data["data"]["sls_tracking_info"]["records"]
        return jsonify(records)
    except:
        return jsonify([])

# ===== GET ORDERS =====
@app.route("/orders")
def get_orders():
    orders = load_orders()
    changed = False

    for o in orders:
        try:
            api = get_tracking(o["code"])

            if not api or "data" not in api:
                continue

            records = api["data"]["sls_tracking_info"]["records"]
            if not records:
                continue

            latest = records[0]["actual_time"]

            if o.get("last_time") != latest:
                o["last_time"] = latest
                changed = True

        except:
            pass

    if changed:
        save_orders(orders)

    return jsonify(orders)

# ===== ADD =====
@app.route("/orders/add", methods=["POST"])
def add():
    data = request.json
    code = data.get("code", "").strip().upper()
    note = data.get("note", "")

    orders = load_orders()

    # tránh trùng
    if any(o["code"] == code for o in orders):
        return {"error": "duplicate"}

    orders.append({
        "code": code,
        "note": note,
        "last_time": 0,
        "seen_time": 0
    })

    save_orders(orders)

    return {"ok": True}

# ===== DELETE =====
@app.route("/orders/delete", methods=["POST"])
def delete():
    code = request.json.get("code")

    orders = load_orders()
    orders = [o for o in orders if o["code"] != code]

    save_orders(orders)

    return {"ok": True}

# ===== MARK SEEN =====
@app.route("/orders/seen", methods=["POST"])
def seen():
    code = request.json.get("code")

    orders = load_orders()

    for o in orders:
        if o["code"] == code:
            o["seen_time"] = o.get("last_time", 0)

    save_orders(orders)

    return {"ok": True}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=False)