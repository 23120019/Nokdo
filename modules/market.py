import requests

def get_price(symbol, access_token): 
    url = "https://openapi.koreainvestment.com:9443/stock/market-data"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"symbol": symbol}
    res = requests.get(url, headers=headers, params=params)
    res.raise_for_status()
    return res.json()