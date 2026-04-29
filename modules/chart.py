from modules.api_client import call_api
from tr_codes import CHART_URI, CHART_API_IDS

def _chart_request(token: str, params: dict, period: str):
    """
    Kiwoom 주식 차트 조회
    """
    api_id = CHART_API_IDS.get(period, CHART_API_IDS["D"])
    body = {
        "stk_cd": params.get("stk_cd"),
        "base_dt": params.get("base_dt"),
        "upd_stkpc_tp": params.get("upd_stkpc_tp") or params.get("updn_tp", "0"),
    }
    return call_api(token, CHART_URI, api_id, body)


def fn_ka10081(token: str, params: dict):
    """주식일봉차트조회요청"""
    return _chart_request(token, params, "D")


def fn_ka10082(token: str, params: dict):
    """주식주봉차트조회요청"""
    return _chart_request(token, params, "W")


def fn_ka10083(token: str, params: dict):
    """주식월봉차트조회요청"""
    return _chart_request(token, params, "M")


def fn_ka10094(token: str, params: dict):
    """주식년봉차트조회요청"""
    return _chart_request(token, params, "Y")


def fn_ka10005(token: str, params: dict):
    """Backward-compatible alias for the old chart helper name."""
    return fn_ka10081(token, params)