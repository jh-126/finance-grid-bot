import os
import requests
import time
import hashlib
import hmac
import urllib.parse

TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
TELEGRAM_CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
API_KEY = os.environ['BINANCE_API_KEY']
API_SECRET = os.environ['BINANCE_API_SECRET'].encode()

symbol = "USDCUSDT"
amount = 10
price_step = 0.0001
DRY_RUN = False

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": msg}
    try:
        requests.post(url, data=data)
    except Exception:
        print("Telegram 發送失敗")

def sign(params):
    query_string = urllib.parse.urlencode(params)
    signature = hmac.new(API_SECRET, query_string.encode(), hashlib.sha256).hexdigest()
    return f"{query_string}&signature={signature}"

def binance_request(method, path, params={}, private=False):
    base_url = "https://api.binance.com"
    headers = {"X-MBX-APIKEY": API_KEY} if private else {}
    if private:
        params['timestamp'] = int(time.time() * 1000)
        url = f"{base_url}{path}?{sign(params)}"
    else:
        url = f"{base_url}{path}?{urllib.parse.urlencode(params)}"
    resp = requests.request(method, url, headers=headers)
    return resp.json()

def get_price():
    data = binance_request("GET", "/api/v3/ticker/price", {"symbol": symbol})
    return float(data["price"])

def place_order(side, price, quantity):
    if DRY_RUN:
        print(f"[模擬下單] {side} {quantity} @ {price}")
        return {"orderId": int(time.time()), "price": price}
    params = {
        "symbol": symbol,
        "side": side,
        "type": "LIMIT",
        "timeInForce": "GTC",
        "quantity": f"{quantity:.2f}",
        "price": f"{price:.4f}"
    }
    return binance_request("POST", "/api/v3/order", params, private=True)

def cancel_order(order_id):
    if DRY_RUN:
        print(f"[模擬取消] 訂單 {order_id}")
        return
    binance_request("DELETE", "/api/v3/order", {"symbol": symbol, "orderId": order_id}, private=True)

def check_filled(order_id):
    data = binance_request("GET", "/api/v3/order", {"symbol": symbol, "orderId": order_id}, private=True)
    return data.get("status") == "FILLED"

def TradingLoop():
    while True:
        try:
            current_price = get_price()
            base_price = round(current_price, 4)
            buy_price = round(base_price - price_step, 4)
            sell_price = round(base_price + price_step, 4)

            buy_order = place_order("BUY", buy_price, amount)
            sell_order = place_order("SELL", sell_price, amount)

            send_telegram(f"掛單：買 {buy_price}, 賣 {sell_price}")

            while True:
                if check_filled(buy_order["orderId"]):
                    cancel_order(sell_order["orderId"])
                    send_telegram(f"買入成交@{buy_price}")
                    break
                elif check_filled(sell_order["orderId"]):
                    cancel_order(buy_order["orderId"])
                    send_telegram(f"賣出成交@{sell_price}")
                    break
                time.sleep(1)
        except Exception as e:
            send_telegram(f"錯誤：{str(e)}")
            time.sleep(5)

if __name__ == "__main__":
    TradingLoop()
