from modules.api_client import call_api

def fn_ka10014(token, params):  # 공매도 추이
    return call_api(token, '/api/dostk/shsa', 'ka10014', params)

def fn_ka10008(token, params):  # 외국인 매매동향
    return call_api(token, '/api/dostk/frgnistt', 'ka10008', params)

def fn_ka10068(token, params):  # 대차거래 추이
    return call_api(token, '/api/dostk/slb', 'ka10068', params)