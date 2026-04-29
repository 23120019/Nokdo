from modules.api_client import call_api

def fn_ka10010(token, params):  # 업종 프로그램 요청
    return call_api(token, '/api/dostk/sect', 'ka10010', params)

def fn_ka90001(token, params):  # 테마 그룹별 요청
    return call_api(token, '/api/dostk/thme', 'ka90001', params)