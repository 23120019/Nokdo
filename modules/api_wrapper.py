# api_wrapper.py
from modules.api_client import call_api
from tr_codes import TR_CODES

def request_tr(token, tr_name, params):
    """
    token: 인증 토큰
    tr_name: 딕셔너리 키 (예: 'TR_00001')
    params: 요청 파라미터 dict
    """
    tr_code = TR_CODES.get(tr_name)
    if not tr_code:
        raise ValueError(f"등록되지 않은 TR 이름: {tr_name}")
    return call_api(token, '/api/dostk/mrkcond', tr_code, params)