import requests

def place_order(symbol, qty, price, side, access_token):
    url = "https://openapi.koreainvestment.com:9443/stock/order"
    headers = {"Authorization": f"Bearer {access_token}"}
    data = {
        "symbol": symbol,
        "qty": qty,
        "price": price,
        "side": side  # "buy" or "sell"
    }
    res = requests.post(url, headers=headers, json=data)
    res.raise_for_status()
    return res.json()