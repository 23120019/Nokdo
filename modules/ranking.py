from modules.api_client import call_api

def fn_ka10020(token, params):  # 호가잔량 상위
    return call_api(token, '/api/dostk/rkinfo', 'ka10020', params)

def fn_ka00198(token, params):  # 실시간 종목조회순위
    return call_api(token, '/api/dostk/stkinfo', 'ka00198', params)