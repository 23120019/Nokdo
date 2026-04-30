import datetime
import hmac
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from modules.auth import fn_au10001
from modules.chart import fn_ka10081, fn_ka10082, fn_ka10083, fn_ka10094

try:
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
    SKLEARN_AVAILABLE = True
except Exception:
    SKLEARN_AVAILABLE = False

try:
    import yfinance as yf

    YFINANCE_AVAILABLE = True
except Exception:
    YFINANCE_AVAILABLE = False

try:
    from streamlit_autorefresh import st_autorefresh

    AUTOREFRESH_AVAILABLE = True
except Exception:
    AUTOREFRESH_AVAILABLE = False


DOMESTIC_STOCK_PRESETS = {
    "직접 입력": None,
    "삼성전자 (005930)": "005930",
    "SK하이닉스 (000660)": "000660",
    "LG에너지솔루션 (373220)": "373220",
    "현대차 (005380)": "005380",
    "기아 (000270)": "000270",
    "네이버 (035420)": "035420",
    "카카오 (035720)": "035720",
    "셀트리온 (068270)": "068270",
    "KB금융 (105560)": "105560",
    "POSCO홀딩스 (005490)": "005490",
}

OVERSEAS_STOCK_PRESETS = {
    "직접 입력": None,
    "Apple (AAPL)": "AAPL",
    "Microsoft (MSFT)": "MSFT",
    "NVIDIA (NVDA)": "NVDA",
    "Tesla (TSLA)": "TSLA",
    "Amazon (AMZN)": "AMZN",
    "Alphabet (GOOGL)": "GOOGL",
    "Meta (META)": "META",
    "TSMC (TSM)": "TSM",
    "Toyota (7203.T)": "7203.T",
    "Tencent (0700.HK)": "0700.HK",
}


def _build_ml_dataset(price_df: pd.DataFrame):
    ml_df = price_df.copy()
    ml_df = ml_df.sort_values("date").reset_index(drop=True)

    # 기본 수익률/변동성 특징량
    ml_df["ret_1"] = ml_df["close"].pct_change(1)
    ml_df["ret_3"] = ml_df["close"].pct_change(3)
    ml_df["ret_5"] = ml_df["close"].pct_change(5)
    ml_df["hl_range"] = (ml_df["high"] - ml_df["low"]) / ml_df["close"]
    ml_df["oc_change"] = (ml_df["close"] - ml_df["open"]) / ml_df["open"]

    # 이동평균 기반 특징량
    ml_df["ma_5"] = ml_df["close"].rolling(5).mean()
    ml_df["ma_20"] = ml_df["close"].rolling(20).mean()
    ml_df["ma_ratio"] = (ml_df["ma_5"] / ml_df["ma_20"]) - 1

    # RSI(14)
    delta = ml_df["close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, pd.NA)
    ml_df["rsi_14"] = 100 - (100 / (1 + rs))

    # 거래량이 있으면 변화율 추가
    volume_column = next((col for col in ["trde_qty", "acml_vol", "volume"] if col in ml_df.columns), None)
    if volume_column is not None:
        ml_df["volume"] = pd.to_numeric(ml_df[volume_column], errors="coerce")
        ml_df["vol_chg_1"] = ml_df["volume"].pct_change(1)
    else:
        ml_df["vol_chg_1"] = 0.0

    # 다음 봉 상승 여부를 타깃으로 설정
    ml_df["target_up"] = (ml_df["close"].shift(-1) > ml_df["close"]).astype(int)

    feature_cols = [
        "ret_1",
        "ret_3",
        "ret_5",
        "hl_range",
        "oc_change",
        "ma_ratio",
        "rsi_14",
        "vol_chg_1",
    ]

    # 분모가 0인 구간 등에서 inf/-inf가 발생할 수 있어 모델 입력 전 정리
    ml_df[feature_cols] = ml_df[feature_cols].apply(pd.to_numeric, errors="coerce")
    ml_df[feature_cols] = ml_df[feature_cols].replace([float("inf"), float("-inf")], float("nan"))

    model_df = ml_df.dropna(subset=feature_cols + ["target_up"]).copy()
    return model_df, feature_cols


def _run_ml_prediction(price_df: pd.DataFrame):
    if not SKLEARN_AVAILABLE:
        return {"error": "scikit-learn이 설치되어 있지 않습니다. requirements 설치 후 다시 시도해주세요."}

    model_df, feature_cols = _build_ml_dataset(price_df)
    if len(model_df) < 80:
        return {"error": f"학습 데이터가 부족합니다. 현재 {len(model_df)}개 (최소 80개 필요)"}

    split_idx = int(len(model_df) * 0.8)
    if len(model_df) - split_idx < 15:
        return {"error": "검증 구간 데이터가 부족합니다. 더 긴 기간의 데이터를 조회해주세요."}

    train_df = model_df.iloc[:split_idx]
    test_df = model_df.iloc[split_idx:]

    x_train = train_df[feature_cols]
    y_train = train_df["target_up"]
    x_test = test_df[feature_cols]
    y_test = test_df["target_up"]

    # 혹시 남은 비정상값이 있으면 학습 직전에 한 번 더 제거
    x_train = x_train.replace([float("inf"), float("-inf")], float("nan"))
    x_test = x_test.replace([float("inf"), float("-inf")], float("nan"))

    train_valid_mask = x_train.notna().all(axis=1)
    test_valid_mask = x_test.notna().all(axis=1)
    x_train = x_train.loc[train_valid_mask]
    y_train = y_train.loc[train_valid_mask]
    x_test = x_test.loc[test_valid_mask]
    y_test = y_test.loc[test_valid_mask]

    if len(x_train) < 50 or len(x_test) < 10:
        return {"error": "유효한 학습/검증 데이터가 부족합니다. 조회 기간을 늘리거나 종목을 변경해주세요."}

    pipeline = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=2000, class_weight="balanced")),
        ]
    )
    pipeline.fit(x_train, y_train)

    y_pred = pipeline.predict(x_test)
    y_prob = pipeline.predict_proba(x_test)[:, 1]

    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred, zero_division=0),
        "f1": f1_score(y_test, y_pred, zero_division=0),
    }

    unique_classes = y_test.nunique()
    if unique_classes > 1:
        metrics["roc_auc"] = roc_auc_score(y_test, y_prob)
    else:
        metrics["roc_auc"] = None

    latest_x = model_df[feature_cols].iloc[[-1]]
    next_up_prob = float(pipeline.predict_proba(latest_x)[:, 1][0])
    next_down_prob = 1.0 - next_up_prob

    if next_up_prob >= 0.55:
        signal = "상승 우세"
    elif next_up_prob <= 0.45:
        signal = "하락 우세"
    else:
        signal = "중립"

    return {
        "metrics": metrics,
        "train_size": len(train_df),
            "test_size": len(test_df),
        "next_up_prob": next_up_prob,
        "next_down_prob": next_down_prob,
        "signal": signal,
    }


def _build_overseas_dataset(ticker: str, period: str, realtime_mode: bool = False, adjusted_price: bool = False):
    if not YFINANCE_AVAILABLE:
        return {"error": "yfinance가 설치되어 있지 않습니다. 해외주식 기능을 사용하려면 requirements를 설치하세요."}

    ticker = (ticker or "").strip()
    if not ticker:
        return {"error": "티커를 입력해주세요. 예: AAPL, TSLA, NVDA, 7203.T, 0700.HK"}

    period_map = {
        "1M": "1mo",
        "3M": "3mo",
        "6M": "6mo",
        "1Y": "1y",
        "5Y": "5y",
        "MAX": "max",
    }
    yf_period = period_map.get(period, "1y")
    yf_interval = "1d"

    # 자동 갱신 모드에서는 체결 변화가 보이도록 분봉 데이터를 사용
    if realtime_mode:
        yf_period = "5d"
        yf_interval = "1m"

    try:
        raw = yf.download(
            tickers=ticker,
            period=yf_period,
            interval=yf_interval,
            auto_adjust=adjusted_price,
            progress=False,
            threads=False,
        )
    except Exception as exc:
        return {"error": f"해외주식 조회 실패: {exc}"}

    if raw is None or raw.empty:
        return {"error": "조회된 해외주식 데이터가 없습니다."}

    df = raw.copy()

    # yfinance는 종종 MultiIndex 컬럼을 반환하므로 단일 컬럼명으로 평탄화
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [str(col[0]) for col in df.columns]

    df = df.reset_index()
    date_column = next((column for column in ["Date", "Datetime"] if column in df.columns), None)
    if date_column is None:
        return {"error": "해외주식 응답에서 날짜 컬럼을 찾지 못했습니다."}

    rename_map = {}
    for source, target in [("Open", "open"), ("High", "high"), ("Low", "low"), ("Close", "close"), ("Volume", "volume")]:
        if source in df.columns:
            rename_map[source] = target

    df = df.rename(columns=rename_map)
    df["date"] = pd.to_datetime(df[date_column], errors="coerce")
    required_columns = ["date", "open", "high", "low", "close"]

    missing_columns = [column for column in required_columns if column not in df.columns]
    if missing_columns:
        return {"error": f"해외주식 응답 컬럼이 부족합니다: {', '.join(missing_columns)}"}

    df = df.dropna(subset=required_columns).sort_values("date").reset_index(drop=True)

    if df.empty:
        return {"error": "해외주식 데이터 정규화 후 유효한 행이 없습니다."}

    return {
        "df": df,
        "response": {
            "source": "yfinance",
            "ticker": ticker,
            "period": yf_period,
            "interval": yf_interval,
            "adjusted_price": adjusted_price,
            "rows": len(df),
        },
    }


def _fetch_overseas_realtime_price(ticker: str):
    if not YFINANCE_AVAILABLE:
        return {"error": "yfinance가 설치되어 있지 않습니다."}

    ticker = (ticker or "").strip().upper()
    if not ticker:
        return {"error": "티커가 비어 있습니다."}

    try:
        ticker_obj = yf.Ticker(ticker)

        fast_info = getattr(ticker_obj, "fast_info", None)
        if fast_info:
            for key in ["lastPrice", "regularMarketPrice", "previousClose"]:
                value = fast_info.get(key)
                if value is not None:
                    return {
                        "price": float(value),
                        "timestamp": pd.Timestamp.now().floor("s"),
                        "source": f"fast_info.{key}",
                    }

        info = getattr(ticker_obj, "info", None) or {}
        for key in ["regularMarketPrice", "currentPrice", "previousClose"]:
            value = info.get(key)
            if value is not None:
                return {
                    "price": float(value),
                    "timestamp": pd.Timestamp.now().floor("s"),
                    "source": f"info.{key}",
                }
    except Exception as exc:
        return {"error": f"현재가 조회 실패: {exc}"}

    return {"error": "현재가 정보를 찾지 못했습니다."}


def _fetch_domestic_chart(token: str, stock_code: str, query_date: datetime.date, updn_tp: str, chart_period: str):
    dt_str = query_date.strftime("%Y%m%d")
    params = {
        "stk_cd": stock_code,
        "base_dt": dt_str,
        "updn_tp": updn_tp,
    }

    chart_fn = {
        "D": fn_ka10081,
        "W": fn_ka10082,
        "M": fn_ka10083,
        "Y": fn_ka10094,
    }[chart_period]
    response = chart_fn(token, params)

    if response.get("return_code") not in (None, 0):
        return {
            "error": f"API 오류: {response.get('return_msg', '알 수 없는 오류')}",
            "response": response,
        }

    data = next(
        (
            value
            for value in response.values()
            if isinstance(value, list) and len(value) > 0
        ),
        None,
    )

    if not data or not isinstance(data, list):
        return {
            "error": "차트 데이터가 없습니다.",
            "response": response,
        }

    df = pd.DataFrame(data)

    date_column = next((column for column in ["stck_bsop_date", "base_dt", "dt"] if column in df.columns), None)
    if date_column is None:
        return {
            "error": "날짜 컬럼을 찾지 못했습니다.",
            "response": response,
        }

    df["date"] = pd.to_datetime(df[date_column], format="%Y%m%d", errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

    open_column = next((column for column in ["stck_oprc", "open_pric"] if column in df.columns), None)
    high_column = next((column for column in ["stck_hgpr", "high_pric"] if column in df.columns), None)
    low_column = next((column for column in ["stck_lwpr", "low_pric"] if column in df.columns), None)
    close_column = next((column for column in ["stck_clpr", "cur_prc", "close_pric"] if column in df.columns), None)

    if None in (open_column, high_column, low_column, close_column):
        return {
            "error": "OHLC 컬럼을 찾지 못했습니다.",
            "response": response,
        }

    df["open"] = pd.to_numeric(df[open_column], errors="coerce")
    df["high"] = pd.to_numeric(df[high_column], errors="coerce")
    df["low"] = pd.to_numeric(df[low_column], errors="coerce")
    df["close"] = pd.to_numeric(df[close_column], errors="coerce")
    df = df.dropna(subset=["open", "high", "low", "close"]).reset_index(drop=True)

    return {
        "df": df,
        "response": response,
    }


def _append_realtime_point(df: pd.DataFrame, stock_code: str, chart_period: str, state_prefix: str = "domestic"):
    if df.empty:
        return

    latest_close = float(df["close"].iloc[-1])
    now_ts = pd.Timestamp.now().floor("s")
    trace_key = f"{stock_code}_{chart_period}"
    points_key = f"{state_prefix}_realtime_points"
    trace_state_key = f"{state_prefix}_realtime_trace_key"

    if st.session_state.get(trace_state_key) != trace_key:
        st.session_state[points_key] = []
        st.session_state[trace_state_key] = trace_key

    points = st.session_state.get(points_key, [])
    points.append({"time": now_ts, "price": latest_close})
    st.session_state[points_key] = points[-120:]


def _append_realtime_price(price: float, symbol: str, period: str, state_prefix: str = "overseas"):
    now_ts = pd.Timestamp.now().floor("s")
    trace_key = f"{symbol}_{period}"
    points_key = f"{state_prefix}_realtime_points"
    trace_state_key = f"{state_prefix}_realtime_trace_key"

    if st.session_state.get(trace_state_key) != trace_key:
        st.session_state[points_key] = []
        st.session_state[trace_state_key] = trace_key

    points = st.session_state.get(points_key, [])
    points.append({"time": now_ts, "price": float(price)})
    st.session_state[points_key] = points[-240:]

# 페이지 설정
st.set_page_config(page_title="Kiwoom 실시간 캔들차트", layout="wide", initial_sidebar_state="expanded")


def _get_allowed_users():
    try:
        secret_users = st.secrets.get("users", {})
    except Exception:
        secret_users = {}

    allowed_users = {}
    if isinstance(secret_users, dict):
        for username, password in secret_users.items():
            allowed_users[str(username).strip()] = str(password).strip()

    if not allowed_users:
        secrets_path = Path(__file__).resolve().parent / ".streamlit" / "secrets.toml"
        if secrets_path.exists():
            in_users_section = False
            try:
                for raw_line in secrets_path.read_text(encoding="utf-8").splitlines():
                    line = raw_line.strip()
                    if not line or line.startswith("#"):
                        continue

                    if line.startswith("[") and line.endswith("]"):
                        in_users_section = line[1:-1].strip() == "users"
                        continue

                    if not in_users_section or "=" not in line:
                        continue

                    key, value = line.split("=", 1)
                    username = key.strip().strip('"').strip("'")
                    password = value.strip().strip('"').strip("'")
                    if username:
                        allowed_users[username] = password
            except Exception:
                pass

    legacy_password = str(st.secrets.get("APP_PASSWORD", "") or os.getenv("STREAMLIT_APP_PASSWORD", "")).strip()
    if legacy_password and "nokdo" not in allowed_users:
        allowed_users["nokdo"] = legacy_password

    return allowed_users


ALLOWED_USERS = _get_allowed_users()
REQUIRE_LOCAL_LOGIN = str(os.getenv("STREAMLIT_REQUIRE_LOCAL_LOGIN", "0")).strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}

# Streamlit 요청의 호스트 정보를 기반으로 API 주소 동적 결정
def get_presence_api_base():
    """현재 요청의 호스트를 기반으로 올바른 Presence API 주소 결정"""
    env_override = os.getenv("STREAMLIT_PRESENCE_API_BASE", "").strip()
    if env_override:
        return env_override.rstrip("/")
    
    # 기본값: 로컬 Firebase 에뮬레이터 사용
    return "http://127.0.0.1:8355/fir-demo-project/us-central1/api"

PRESENCE_API_BASE = get_presence_api_base()
PRESENCE_TOUCH_INTERVAL_SECONDS = int(os.getenv("STREAMLIT_PRESENCE_TOUCH_INTERVAL_SECONDS", "15"))
# 고정 로그인 URL: 프론트엔드 로그인 페이지로 기본값 설정
# 환경변수 STREAMLIT_FIREBASE_LOGIN_URL로 덮어쓸 수 있다.
FIREBASE_LOGIN_URL = str(
    os.getenv("STREAMLIT_FIREBASE_LOGIN_URL", "https://commissions-spent-accessories-feet.trycloudflare.com")
).strip()
# 기본 동작: 사용자를 식별할 수 없으면(쿼리파라미터 또는 세션 없음) Firebase 로그인으로 리다이렉트
# 기본값은 false (명시적으로 STREAMLIT_REDIRECT_IF_NO_USER=1 환경변수로 활성화)
STREAMLIT_REDIRECT_IF_NO_USER = str(os.getenv("STREAMLIT_REDIRECT_IF_NO_USER", "0")).strip().lower() in {"1", "true", "yes", "on"}


def _presence_request(path: str, method: str = "GET", payload=None, timeout_sec: float = 2.5):
    if not PRESENCE_API_BASE:
        return None, "presence API base가 비어 있습니다."

    url = f"{PRESENCE_API_BASE}{path}"
    body = None
    headers = {}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url=url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(request, timeout=timeout_sec) as response:
            raw = response.read().decode("utf-8")
        return (json.loads(raw) if raw else {}), ""
    except urllib.error.HTTPError as exc:
        return None, f"presence API HTTP 오류: {exc.code}"
    except Exception as exc:  # noqa: BLE001
        return None, f"presence API 연결 실패: {exc}"


def _resolve_presence_username() -> str:
    state_user = str(st.session_state.get("authenticated_user", "") or "").strip()
    if state_user:
        return state_user

    try:
        query_params = st.query_params
        query_user = query_params.get("user", "")
    except Exception:  # noqa: BLE001
        query_user = ""

    if isinstance(query_user, list):
        query_user = query_user[0] if query_user else ""

    normalized = str(query_user or "").strip()
    if normalized:
        st.session_state.authenticated_user = normalized

    return normalized


def _format_presence_clock(ts_millis):
    try:
        ts = int(ts_millis)
    except Exception:  # noqa: BLE001
        return "-"

    if ts <= 0:
        return "-"

    dt = datetime.datetime.fromtimestamp(ts / 1000)
    return dt.strftime("%H:%M:%S")


def _format_presence_ago(ts_millis):
    try:
        ts = int(ts_millis)
    except Exception:  # noqa: BLE001
        return "-"

    if ts <= 0:
        return "-"

    diff_sec = max(0, int(datetime.datetime.now().timestamp() - (ts / 1000)))
    if diff_sec < 60:
        return f"{diff_sec}초 전"
    if diff_sec < 3600:
        return f"{diff_sec // 60}분 전"
    return f"{diff_sec // 3600}시간 전"


def _redirect_to_login_page() -> None:
    if not FIREBASE_LOGIN_URL:
        st.warning("로그인 화면 URL이 설정되지 않았습니다. `STREAMLIT_FIREBASE_LOGIN_URL`을 지정해주세요.")
        return
    # iframe JS보다 메타 리프레시가 브라우저 호환성이 좋다.
    st.markdown(
        f'<meta http-equiv="refresh" content="0; url={FIREBASE_LOGIN_URL}">',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'이동 중입니다... [로그인 화면으로 이동]({FIREBASE_LOGIN_URL})',
        unsafe_allow_html=True,
    )

if "authenticated" not in st.session_state:
    st.session_state.authenticated = not REQUIRE_LOCAL_LOGIN
if "authenticated_user" not in st.session_state:
    st.session_state.authenticated_user = ""
if "presence_users" not in st.session_state:
    st.session_state.presence_users = []
if "presence_error" not in st.session_state:
    st.session_state.presence_error = ""
if "presence_last_touch_at" not in st.session_state:
    st.session_state.presence_last_touch_at = 0.0
if "logout_redirect_pending" not in st.session_state:
    st.session_state.logout_redirect_pending = False

if st.session_state.logout_redirect_pending:
    st.session_state.logout_redirect_pending = False
    _redirect_to_login_page()
    st.stop()

if REQUIRE_LOCAL_LOGIN and not st.session_state.authenticated:
    st.title("접속 제한")
    st.write("허용된 사용자만 접근할 수 있습니다.")

    with st.form("app_login_form"):
        entered_username = st.text_input("사용자명")
        entered_password = st.text_input("비밀번호", type="password")
        submit_login = st.form_submit_button("접속")

    if submit_login:
        stored_password = ALLOWED_USERS.get(entered_username.strip())
        if not ALLOWED_USERS:
            st.error("허용된 사용자가 설정되지 않았습니다. .streamlit/secrets.toml의 [users]를 확인하세요.")
        elif stored_password and hmac.compare_digest(entered_password, stored_password):
            st.session_state.authenticated = True
            st.session_state.authenticated_user = entered_username.strip()
            st.rerun()
        else:
            st.error("사용자명 또는 비밀번호가 올바르지 않습니다.")

    st.stop()

# 제목
st.title("🕯️ Nokdo 실시간 캔들차트")
st.markdown("---")

presence_username = _resolve_presence_username()
# 자동 리다이렉트: 식별 정보가 없으면 Firebase 로그인으로 보냄
if STREAMLIT_REDIRECT_IF_NO_USER and not REQUIRE_LOCAL_LOGIN and not presence_username:
    _redirect_to_login_page()
    st.stop()
if presence_username:
    now_ts = datetime.datetime.now().timestamp()
    if now_ts - float(st.session_state.presence_last_touch_at) >= PRESENCE_TOUCH_INTERVAL_SECONDS:
        _, touch_error = _presence_request(
            "/presence/touch",
            method="POST",
            payload={"username": presence_username, "isActive": True},
        )
        if not touch_error:
            st.session_state.presence_last_touch_at = now_ts
        else:
            st.session_state.presence_error = touch_error

presence_result, presence_error = _presence_request("/presence")
if presence_result and isinstance(presence_result.get("users"), list):
    st.session_state.presence_users = presence_result["users"]
    st.session_state.presence_error = ""
elif presence_error:
    st.session_state.presence_error = presence_error

if presence_username and not any(
    str(item.get("username", "")).strip() == presence_username for item in st.session_state.presence_users
):
    st.session_state.presence_users.append(
        {
            "username": presence_username,
            "isIdle": False,
            "lastActiveAt": int(datetime.datetime.now().timestamp() * 1000),
        }
    )

# 클라이언트에서 탭 닫기/이동 시 presence disconnect를 시도하도록 JS를 주입
if presence_username and PRESENCE_API_BASE:
    disconnect_url = f"{PRESENCE_API_BASE}/presence/disconnect"
    # Build HTML/JS safely without f-string interpolation to avoid brace conflicts
    html = (
        '<script>'
        '(function(){'
        'const url = ' + json.dumps(disconnect_url) + ';'
        'const payload = JSON.stringify({ username: ' + json.dumps(presence_username) + '});'
        'try {'
        "window.addEventListener('unload', function() {"
        "  const blob = new Blob([payload], { type: 'application/json' });"
        "  if (navigator.sendBeacon) { navigator.sendBeacon(url, blob); } else {"
        "    var xhr = new XMLHttpRequest(); xhr.open('POST', url, false); xhr.setRequestHeader('Content-Type', 'application/json'); try { xhr.send(payload); } catch (e) {}"
        "  }"
        "});"
        ' } catch (e) {}'
        '})();'
        '</script>'
    )
    components.html(html, height=0)

# 세션 상태 초기화
if "token" not in st.session_state:
    st.session_state.token = ""
if "chart_data" not in st.session_state:
    st.session_state.chart_data = None
if "stock_code" not in st.session_state:
    st.session_state.stock_code = "005930"
if "overseas_symbol" not in st.session_state:
    st.session_state.overseas_symbol = "AAPL"
if "overseas_data" not in st.session_state:
    st.session_state.overseas_data = None
if "domestic_realtime_points" not in st.session_state:
    st.session_state.domestic_realtime_points = []
if "domestic_realtime_trace_key" not in st.session_state:
    st.session_state.domestic_realtime_trace_key = ""
if "overseas_realtime_points" not in st.session_state:
    st.session_state.overseas_realtime_points = []
if "overseas_realtime_trace_key" not in st.session_state:
    st.session_state.overseas_realtime_trace_key = ""
if "overseas_last_candle_fetch_at" not in st.session_state:
    st.session_state.overseas_last_candle_fetch_at = None

# 사이드바: 인증
with st.sidebar:
    st.header("🔐 인증 설정")
    
    appkey_input = st.text_input(
        "APPKEY",
        value="106kkiYckDEfJKfG2GoYYL46FTukNEz8fseXe6f83Ao",  # ← 사용자 APPKEY
        key="appkey_input"
    )
    secretkey_input = st.text_input(
        "APPSECRET",
        value="n38UhjmRSBWr6-5cm60_3XZgsCDLxsDhOpPI-y8MKo4",  # ← 사용자 SECRETKEY
        type="password",
        key="secretkey_input"
    )
    
    if st.button("🔑 토큰 발급", key="token_btn"):
        with st.spinner("토큰 발급 중..."):
            try:
                token_info = fn_au10001({
                    "grant_type": "client_credentials",
                    "appkey": appkey_input,
                    "secretkey": secretkey_input,
                })
                token = token_info.get("token") or token_info.get("access_token")
                if token:
                    st.session_state.token = token
                    st.success("✅ 토큰 발급 완료!")
                else:
                    st.error("❌ 토큰 발급 실패")
                    st.json(token_info)
            except Exception as e:
                st.error(f"❌ 오류: {str(e)}")
    
    if st.session_state.token:
        st.success("✅ 인증됨")
        st.caption(st.session_state.token[:30] + "...")
    else:
        st.warning("⚠️ 토큰을 발급해주세요.")

    st.markdown("---")
    st.header("👥 접속 명단")
    if presence_username:
        st.success(f"{presence_username}님 접속중")
    else:
        st.info("현재 사용자 식별 정보가 없습니다.")

    if st.session_state.presence_users:
        for user_info in st.session_state.presence_users:
            row_username = str(user_info.get("username", "")).strip() or "(unknown)"
            is_idle = bool(user_info.get("isIdle", False))
            status = "자리비움" if is_idle else "활동중"
            last_active_at = user_info.get("lastActiveAt")
            st.write(f"- {row_username} · {status}")
            st.caption(
                f"최근 활동 {_format_presence_ago(last_active_at)} (시각 {_format_presence_clock(last_active_at)})"
            )
    else:
        st.caption("표시할 접속자가 없습니다.")

    if st.session_state.presence_error:
        st.warning(st.session_state.presence_error)

    if st.button("🚪 로그아웃", key="local_logout_btn"):
        if presence_username:
            _presence_request(
                "/presence/disconnect",
                method="POST",
                payload={"username": presence_username},
            )
        try:
            st.query_params.clear()
        except Exception:  # noqa: BLE001
            pass
        # 세션 상태 초기화 후 rerun - 다음 렌더링에서 자동 리다이렉트 로직이 작동
        st.session_state.authenticated = False
        st.session_state.authenticated_user = ""
        st.session_state.presence_last_touch_at = 0.0
        st.session_state.token = ""
        st.session_state.logout_redirect_pending = True
        st.rerun()

# 메인 영역
st.header("📊 차트 조회")

col1, col2, col3, col4 = st.columns(4)
with col1:
    domestic_pick = st.selectbox(
        "국내 종목 선택",
        options=list(DOMESTIC_STOCK_PRESETS.keys()),
        index=0,
        key="domestic_pick",
    )
    selected_domestic_code = DOMESTIC_STOCK_PRESETS.get(domestic_pick)
    if selected_domestic_code and st.session_state.stock_code != selected_domestic_code:
        st.session_state.stock_code = selected_domestic_code

    stock_code = st.text_input("종목코드", key="stock_code", help="목록에서 선택하거나 직접 입력하세요.")
with col2:
    query_date = st.date_input("조회 날짜", value=datetime.date.today(), key="query_date")
with col3:
    chart_period = st.selectbox("차트 주기", ["D", "W", "M", "Y"], index=0, key="chart_period")
    updn_tp = st.selectbox("수정주가 반영", ["0", "1"], index=0, key="updn_tp")
with col4:
    auto_refresh = st.toggle("실시간 갱신", value=False, key="auto_refresh")
    refresh_sec = st.selectbox("갱신 주기(초)", [2, 3, 5, 10], index=2, key="refresh_sec")

refresh_count = 0
if auto_refresh:
    if AUTOREFRESH_AVAILABLE:
        refresh_count = st_autorefresh(interval=int(refresh_sec) * 1000, key="domestic_chart_autorefresh")
        st.caption(f"자동 새로고침 활성화 ({refresh_sec}초 간격)")
    else:
        st.warning("실시간 자동 갱신을 사용하려면 streamlit-autorefresh 설치가 필요합니다.")

manual_chart_refresh = st.button("🔍 차트 조회", key="chart_btn", use_container_width=True)
auto_chart_refresh = auto_refresh and AUTOREFRESH_AVAILABLE and refresh_count > 0

if manual_chart_refresh or auto_chart_refresh:
    if not st.session_state.token:
        st.error("❌ 먼저 토큰을 발급해주세요.")
    else:
        spinner_msg = "📥 차트 데이터를 조회 중입니다..." if manual_chart_refresh else "🔄 실시간 데이터 갱신 중..."
        with st.spinner(spinner_msg):
            try:
                domestic_result = _fetch_domestic_chart(
                    token=st.session_state.token,
                    stock_code=stock_code,
                    query_date=query_date,
                    updn_tp=updn_tp,
                    chart_period=chart_period,
                )

                if "error" in domestic_result:
                    st.error(f"❌ {domestic_result['error']}")
                    with st.expander("원본 응답 보기"):
                        st.json(domestic_result.get("response", {}))
                else:
                    df = domestic_result["df"]
                    st.session_state.chart_data = {
                        "stock_code": stock_code,
                        "chart_period": chart_period,
                        "df": df,
                        "response": domestic_result["response"],
                    }
                    if auto_chart_refresh:
                        _append_realtime_point(df, stock_code, chart_period, state_prefix="domestic")
                    if manual_chart_refresh:
                        st.success(f"✅ 데이터 로드 완료 ({len(df)}개)")
            except Exception as e:
                st.error(f"❌ 오류 발생: {str(e)}")

# 차트 표시
if st.session_state.chart_data:
    data = st.session_state.chart_data
    df = data["df"].copy()
    
    if not df.empty:
        selected_period = data.get("chart_period", chart_period)
        period_label = {
            "D": "일봉",
            "W": "주봉",
            "M": "월봉",
            "Y": "년봉",
        }.get(selected_period, "일봉")
        st.subheader(f"🕯️ {data['stock_code']} {period_label}차트")
        
        # Plotly 캔들차트 (응답 필드명 매핑)
        fig = go.Figure(data=[go.Candlestick(
            x=df["date"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            hovertemplate=(
                "일자: %{x|%Y-%m-%d}<br>"
                "시가: %{open:,.0f}원<br>"
                "고가: %{high:,.0f}원<br>"
                "저가: %{low:,.0f}원<br>"
                "종가: %{close:,.0f}원"
                "<extra></extra>"
            )
        )])
        
        fig.update_layout(
            xaxis_title="일자",
            yaxis_title="가격(원)",
            xaxis_rangeslider_visible=False,
            uirevision=f"domestic_{data['stock_code']}_{selected_period}",
            yaxis={
                "tickformat": ",.0f",
                "ticksuffix": "원",
                "hoverformat": ",.0f",
                "separatethousands": True,
            },
            template="plotly_white"
        )
        
        st.plotly_chart(fig, use_container_width=True, key="domestic_candlestick_chart")

        if auto_refresh and st.session_state.get("domestic_realtime_points"):
            trace_df = pd.DataFrame(st.session_state.domestic_realtime_points)
            if not trace_df.empty:
                latest_price = trace_df["price"].iloc[-1]
                prev_price = trace_df["price"].iloc[-2] if len(trace_df) > 1 else latest_price
                delta = latest_price - prev_price
                st.metric("실시간 추적 종가", f"{latest_price:,.0f}원", delta=f"{delta:,.0f}원")
                st.line_chart(trace_df.set_index("time")["price"], use_container_width=True)
        
        # 통계
        with st.expander("📊 통계"):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("최고가", f"{df['high'].max():,.0f}원")
            with col2:
                st.metric("최저가", f"{df['low'].min():,.0f}원")
            with col3:
                st.metric("평균 종가", f"{df['close'].mean():,.0f}원")
            with col4:
                st.metric("데이터 수", f"{len(df)}개")
        
        # 데이터 테이블
        with st.expander("📋 데이터 테이블"):
            df_display = df.copy()
            df_display["date"] = df_display["date"].dt.strftime("%Y-%m-%d")
            for price_col in ["open", "high", "low", "close"]:
                df_display[f"{price_col}_원"] = df_display[price_col].map(lambda x: f"{x:,.0f}원")
                df_display[f"{price_col}_만원"] = df_display[price_col].map(lambda x: f"{x / 10000:,.1f}만원")
            st.dataframe(df_display, use_container_width=True)

        # 통계/머신러닝 예측
        with st.expander("🤖 통계/머신러닝 예측"):
            ml_result = _run_ml_prediction(df)
            if "error" in ml_result:
                st.warning(ml_result["error"])
            else:
                st.caption(f"학습 구간 {ml_result['train_size']}개 / 검증 구간 {ml_result['test_size']}개")

                m1, m2, m3, m4, m5 = st.columns(5)
                m1.metric("정확도", f"{ml_result['metrics']['accuracy']:.2%}")
                m2.metric("정밀도", f"{ml_result['metrics']['precision']:.2%}")
                m3.metric("재현율", f"{ml_result['metrics']['recall']:.2%}")
                m4.metric("F1", f"{ml_result['metrics']['f1']:.2%}")
                if ml_result["metrics"]["roc_auc"] is None:
                    m5.metric("ROC-AUC", "N/A")
                else:
                    m5.metric("ROC-AUC", f"{ml_result['metrics']['roc_auc']:.2%}")

                st.markdown(f"### 다음 봉 예측: {ml_result['signal']}")
                st.progress(ml_result["next_up_prob"])
                st.write(
                    f"상승 확률: {ml_result['next_up_prob']:.2%} | "
                    f"하락 확률: {ml_result['next_down_prob']:.2%}"
                )
                st.caption("참고: 예측은 확률 기반 참고지표이며 투자 손익을 보장하지 않습니다.")
        
        # 원본 응답
        with st.expander("🔍 원본 응답 데이터"):
            st.json(data["response"])


# 해외주식 조회
st.markdown("---")
st.header("🌍 해외주식 조회")
st.caption("Kiwoom REST는 현재 국내주식 중심이라, 해외주식은 외부 시세 소스(yfinance)를 사용합니다.")

col4, col5, col6, col7 = st.columns(4)
with col4:
    overseas_pick = st.selectbox(
        "해외 종목 선택",
        options=list(OVERSEAS_STOCK_PRESETS.keys()),
        index=0,
        key="overseas_pick",
    )
    selected_overseas_symbol = OVERSEAS_STOCK_PRESETS.get(overseas_pick)
    if selected_overseas_symbol and st.session_state.overseas_symbol != selected_overseas_symbol:
        st.session_state.overseas_symbol = selected_overseas_symbol

    overseas_symbol = st.text_input("해외 티커", key="overseas_symbol", help="목록에서 선택하거나 직접 입력하세요.")
with col5:
    overseas_period = st.selectbox("조회 기간", ["1M", "3M", "6M", "1Y", "5Y", "MAX"], index=3, key="overseas_period")
with col6:
    overseas_auto_refresh = st.toggle("해외 실시간 갱신", value=False, key="overseas_auto_refresh")
    overseas_refresh_sec = st.selectbox("해외 갱신 주기(초)", [2, 3, 5, 10], index=2, key="overseas_refresh_sec")
with col7:
    overseas_updn_tp = st.selectbox("해외 수정주가 반영", ["0", "1"], index=1, key="overseas_updn_tp")

overseas_refresh_count = 0
if overseas_auto_refresh:
    if AUTOREFRESH_AVAILABLE:
        overseas_refresh_count = st_autorefresh(
            interval=int(overseas_refresh_sec) * 1000,
            key="overseas_chart_autorefresh",
        )
        st.caption(f"해외 자동 새로고침 활성화 ({overseas_refresh_sec}초 간격)")
    else:
        st.warning("해외 실시간 자동 갱신을 사용하려면 streamlit-autorefresh 설치가 필요합니다.")

manual_overseas_refresh = st.button("🔍 해외주식 조회", key="overseas_btn", use_container_width=True)
auto_overseas_refresh = overseas_auto_refresh and AUTOREFRESH_AVAILABLE and overseas_refresh_count > 0

if manual_overseas_refresh or auto_overseas_refresh:
    spinner_msg = "📥 해외주식 데이터를 조회 중입니다..." if manual_overseas_refresh else "🔄 해외주식 실시간 갱신 중..."
    with st.spinner(spinner_msg):
        now = pd.Timestamp.now()
        current_symbol = overseas_symbol.upper()
        current_state = st.session_state.overseas_data
        state_changed = (
            current_state is None
            or current_state.get("symbol") != current_symbol
            or current_state.get("period") != overseas_period
        )

        last_fetch = st.session_state.overseas_last_candle_fetch_at
        candle_refresh_window = max(20, int(overseas_refresh_sec) * 4)
        stale_candle = (
            last_fetch is None
            or (now - last_fetch).total_seconds() >= candle_refresh_window
        )
        should_refresh_candle = manual_overseas_refresh or state_changed or stale_candle

        if should_refresh_candle:
            overseas_result = _build_overseas_dataset(
                overseas_symbol,
                overseas_period,
                realtime_mode=overseas_auto_refresh,
                adjusted_price=(overseas_updn_tp == "1"),
            )

            if "error" in overseas_result:
                st.error(overseas_result["error"])
            else:
                overseas_df = overseas_result["df"]
                st.session_state.overseas_data = {
                    "symbol": current_symbol,
                    "period": overseas_period,
                    "df": overseas_df,
                    "response": overseas_result["response"],
                }
                st.session_state.overseas_last_candle_fetch_at = now
                if manual_overseas_refresh:
                    st.success(f"✅ 해외 데이터 로드 완료 ({len(overseas_df)}개)")

        if auto_overseas_refresh:
            quote_result = _fetch_overseas_realtime_price(overseas_symbol)
            if "error" not in quote_result:
                _append_realtime_price(
                    quote_result["price"],
                    symbol=current_symbol,
                    period=overseas_period,
                    state_prefix="overseas",
                )
            elif st.session_state.overseas_data is not None:
                _append_realtime_point(
                    st.session_state.overseas_data["df"],
                    current_symbol,
                    overseas_period,
                    state_prefix="overseas",
                )

if st.session_state.overseas_data:
    overseas_data = st.session_state.overseas_data
    overseas_symbol_view = overseas_data["symbol"]
    overseas_period_view = overseas_data["period"]
    overseas_df = overseas_data["df"].copy()
    overseas_trace_df = pd.DataFrame(st.session_state.get("overseas_realtime_points", []))
    has_overseas_overlay = overseas_auto_refresh and not overseas_trace_df.empty
    has_overseas_close = not overseas_df.empty
    st.subheader(f"🕯️ {overseas_symbol_view} 해외주식 차트")

    fig = go.Figure(data=[go.Candlestick(
        x=overseas_df["date"],
        open=overseas_df["open"],
        high=overseas_df["high"],
        low=overseas_df["low"],
        close=overseas_df["close"],
        hovertemplate=(
            "일자: %{x|%Y-%m-%d}<br>"
            "시가: %{open:,.2f}<br>"
            "고가: %{high:,.2f}<br>"
            "저가: %{low:,.2f}<br>"
            "종가: %{close:,.2f}"
            "<extra></extra>"
        )
    )])

    fig.update_layout(
        xaxis_title="일자",
        yaxis_title="가격",
        xaxis_rangeslider_visible=False,
        uirevision=f"overseas_{overseas_symbol_view}_{overseas_period_view}",
        yaxis={
            "tickformat": ",.2f",
            "hoverformat": ",.2f",
            "separatethousands": True,
        },
        template="plotly_white",
    )

    if has_overseas_overlay:
        fig.add_trace(
            go.Scatter(
                x=overseas_trace_df["time"],
                y=overseas_trace_df["price"],
                mode="lines+markers",
                name="실시간 추적",
                yaxis="y2",
                line={"color": "#ff6b35", "width": 2},
                marker={"size": 4},
                hovertemplate=(
                    "시각: %{x|%Y-%m-%d %H:%M:%S}<br>"
                    "실시간가: %{y:,.2f}"
                    "<extra></extra>"
                ),
            )
        )
        fig.update_layout(
            yaxis2={
                "title": "실시간가",
                "overlaying": "y",
                "side": "right",
                "showgrid": False,
                "tickformat": ",.2f",
                "hoverformat": ",.2f",
            }
        )

    st.plotly_chart(fig, use_container_width=True, key="overseas_candlestick_chart")

    if has_overseas_close:
        if not overseas_trace_df.empty:
            latest_price = float(overseas_trace_df["price"].iloc[-1])
            prev_price = float(overseas_trace_df["price"].iloc[-2]) if len(overseas_trace_df) > 1 else latest_price
        else:
            latest_price = float(overseas_df["close"].iloc[-1])
            prev_price = float(overseas_df["close"].iloc[-2]) if len(overseas_df) > 1 else latest_price

        delta = latest_price - prev_price
        st.metric("해외 실시간 추적 종가", f"{latest_price:,.2f}", delta=f"{delta:,.2f}")

    with st.expander("📊 해외주식 통계"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("최고가", f"{overseas_df['high'].max():,.2f}")
        with col2:
            st.metric("최저가", f"{overseas_df['low'].min():,.2f}")
        with col3:
            st.metric("평균 종가", f"{overseas_df['close'].mean():,.2f}")
        with col4:
            st.metric("데이터 수", f"{len(overseas_df)}개")

    with st.expander("📋 해외주식 데이터 테이블"):
        overseas_display = overseas_df.copy()
        overseas_display["date"] = overseas_display["date"].dt.strftime("%Y-%m-%d")
        for price_col in ["open", "high", "low", "close"]:
            overseas_display[f"{price_col}_표시"] = overseas_display[price_col].map(lambda x: f"{x:,.2f}")
        st.dataframe(overseas_display, use_container_width=True)

    with st.expander("🤖 해외주식 통계/머신러닝 예측"):
        overseas_ml_result = _run_ml_prediction(overseas_df)
        if "error" in overseas_ml_result:
            st.warning(overseas_ml_result["error"])
        else:
            st.caption(f"학습 구간 {overseas_ml_result['train_size']}개 / 검증 구간 {overseas_ml_result['test_size']}개")

            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("정확도", f"{overseas_ml_result['metrics']['accuracy']:.2%}")
            m2.metric("정밀도", f"{overseas_ml_result['metrics']['precision']:.2%}")
            m3.metric("재현율", f"{overseas_ml_result['metrics']['recall']:.2%}")
            m4.metric("F1", f"{overseas_ml_result['metrics']['f1']:.2%}")
            if overseas_ml_result["metrics"]["roc_auc"] is None:
                m5.metric("ROC-AUC", "N/A")
            else:
                m5.metric("ROC-AUC", f"{overseas_ml_result['metrics']['roc_auc']:.2%}")

            st.markdown(f"### 다음 봉 예측: {overseas_ml_result['signal']}")
            st.progress(overseas_ml_result["next_up_prob"])
            st.write(
                f"상승 확률: {overseas_ml_result['next_up_prob']:.2%} | "
                f"하락 확률: {overseas_ml_result['next_down_prob']:.2%}"
            )
            st.caption("참고: 해외주식 예측도 확률 기반 참고지표이며 투자 손익을 보장하지 않습니다.")

    with st.expander("🔍 해외주식 원본 응답 데이터"):
        st.json(overseas_data["response"])