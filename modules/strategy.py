import pandas as pd
from typing import List, Dict, Any

# 모델 기반 예측을 위한 경량 인터페이스
try:
    from .model_server import ModelServer
except Exception:
    # relative import for direct script execution
    try:
        from modules.model_server import ModelServer
    except Exception:
        ModelServer = None


_MODEL = None
if ModelServer is not None:
    try:
        _MODEL = ModelServer()
    except Exception:
        _MODEL = None


def simple_strategy(prices: List[Dict[str, Any]]):
    df = pd.DataFrame(prices)
    df["ma5"] = df["close"].rolling(5).mean()
    df["ma20"] = df["close"].rolling(20).mean()
    if df["ma5"].iloc[-1] > df["ma20"].iloc[-1]:
        return "buy"
    elif df["ma5"].iloc[-1] < df["ma20"].iloc[-1]:
        return "sell"
    else:
        return "hold"


def model_strategy(prices: List[Dict[str, Any]]):
    """모델이 로드되어 있으면 모델 예측을 사용하고, 아니면 simple_strategy를 사용합니다.

    `prices`는 dict 리스트로, 각 항목에 `close`와 `volume`이 포함되어야 합니다.
    """
    global _MODEL
    if _MODEL is None or not getattr(_MODEL, 'is_loaded', False):
        return simple_strategy(prices)

    df = pd.DataFrame(prices)
    # 특징: ml_pipeline과 동일한 피처 생성 규칙을 따릅니다
    df['close_ret'] = df['close'].pct_change()
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma20'] = df['close'].rolling(20).mean()
    df['vol_change'] = df['volume'].pct_change()
    df['ma5_ma20'] = df['ma5'] - df['ma20']
    # 단순 RSI 구현 (동일 코드 재사용을 피하기 위해 inline)
    delta = df['close'].diff()
    up = delta.clip(lower=0).rolling(window=14).mean()
    down = -delta.clip(upper=0).rolling(window=14).mean()
    rs = up / (down + 1e-9)
    df['rsi_14'] = 100 - (100 / (1 + rs))
    df = df.dropna()
    if df.empty:
        return simple_strategy(prices)

    features = ['close_ret', 'ma5', 'ma20', 'vol_change', 'ma5_ma20', 'rsi_14']
    X = df[features]
    # 모델에 마지막 행을 입력
    x_last = X.iloc[[-1]]
    pred = _MODEL.predict(x_last)
    # 예: 1=상승(매수), 0=하락(매도)
    if hasattr(pred, '__len__'):
        p = int(pred[0])
    else:
        p = int(pred)
    return 'buy' if p == 1 else 'sell'


def choose_signal(prices: List[Dict[str, Any]]):
    """실거래에서 호출할 유틸리티: 모델 우선, 비어있으면 룰 기반"""
    try:
        return model_strategy(prices)
    except Exception:
        return simple_strategy(prices)