# # import requests
# # from config import CLIENT_ID, CLIENT_SECRET

# # def get_access_token():
# #     url = "https://openapi.koreainvestment.com:9443/oauth2/token"
# #     data = {
# #         "grant_type": "client_credentials",
# #         "client_id": CLIENT_ID,
# #         "client_secret": CLIENT_SECRET
# #     }
# #     res = requests.post(url, data=data)
# #     res.raise_for_status()
# #     return res.json()["access_token"]
# import requests

# def get_token(appkey, secretkey):
#     url = "https://api.kiwoom.com/oauth2/token"
#     headers = {"Content-Type": "application/json;charset=UTF-8"}
#     data = {"grant_type": "client_credentials", "appkey": appkey, "secretkey": secretkey}
#     response = requests.post(url, headers=headers, json=data)
#     return response.json()
from modules.api_client import call_api

def fn_au10001(data):
    return call_api('', '/oauth2/token', 'au10001', data)