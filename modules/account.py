from modules.api_client import call_api

def fn_ka00001(token, params): 
    return call_api(token, '/api/dostk/acnt', 'ka00001', params) 