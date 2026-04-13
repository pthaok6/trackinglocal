import requests

def get_tracking(tracking_number):
    url = "https://tramavandon.com/api/spx.php"

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Linux; Android 10)",
        "Origin": "https://tramavandon.com",
        "Referer": f"https://tramavandon.com/spx/?tracking_number={tracking_number}",
        "X-Requested-With": "XMLHttpRequest"
    }

    payload = {
        "tracking_id": tracking_number
    }

    try:
        res = requests.post(url, json=payload, headers=headers, timeout=10)

        print("STATUS:", res.status_code)
        #print("TEXT:", res.text[:200])

        return res.json()

    except Exception as e:
        return {"error": str(e)}
