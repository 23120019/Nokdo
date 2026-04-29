from modules.api_client import call_api

def fn_ka10048(token, params):  # ELW 민감도 지표
    return call_api(token, '/api/dostk/elw', 'ka10048', params)

def fn_ka40001(token, params):  # ETF 수익률
    return call_api(token, '/api/dostk/etf', 'ka40001', params)