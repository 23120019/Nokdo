"""FastAPI 기반 예측 서빙 엔드포인트(간단 버전).

엔드포인트:
 - POST /predict { symbol?: str, prices?: [{close, volume}], horizon?: int }

동작:
 - 로컬에 로드된 joblib 모델을 사용해 마지막 타임스텝을 예측.
 - 모델이 없으면 `modules.strategy.choose_signal`을 사용해 룰 기반 신호를 반환.
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

import pandas as pd

from modules.model_server import get_default_server
from modules.strategy import choose_signal

import yfinance as yf

app = FastAPI(title='Trading Model Server')


class PredictRequest(BaseModel):
    symbol: Optional[str] = None
    prices: Optional[List[Dict[str, Any]]] = None
    horizon: int = 1


@app.post('/predict')
async def predict(req: PredictRequest):
    if not req.prices and not req.symbol:
        raise HTTPException(status_code=400, detail="Provide 'symbol' or 'prices'")

    # Fetch or use provided prices
    if req.prices:
        prices = req.prices
    else:
        df = yf.download(req.symbol, period='90d', interval='1d', progress=False)
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail='No data for symbol')
        df = df.rename(columns={c: c.lower() if not isinstance(c, tuple) else str(c[0]).lower() for c in df.columns})
        df = df.dropna()
        prices = [{'close': float(r['close']), 'volume': int(r['volume'])} for _, r in df.iterrows()]

    # Fallback when model not loaded
    server = get_default_server()
    if not server.is_loaded:
        signal = choose_signal(prices)
        return {'signal': signal, 'model_loaded': False}

    # Build features same as training pipeline
    pdf = pd.DataFrame(prices)
    pdf['close_ret'] = pdf['close'].pct_change()
    pdf['ma5'] = pdf['close'].rolling(5).mean()
    pdf['ma20'] = pdf['close'].rolling(20).mean()
    pdf['vol_change'] = pdf['volume'].pct_change()
    pdf['ma5_ma20'] = pdf['ma5'] - pdf['ma20']
    delta = pdf['close'].diff()
    up = delta.clip(lower=0).rolling(window=14).mean()
    down = -delta.clip(upper=0).rolling(window=14).mean()
    rs = up / (down + 1e-9)
    pdf['rsi_14'] = 100 - (100 / (1 + rs))
    pdf = pdf.dropna()
    if pdf.empty:
        signal = choose_signal(prices)
        return {'signal': signal, 'model_loaded': server.is_loaded}

    features = ['close_ret', 'ma5', 'ma20', 'vol_change', 'ma5_ma20', 'rsi_14']
    X_last = pdf[features].iloc[[-1]]

    try:
        prob = None
        if hasattr(server.model, 'predict_proba'):
            proba = server.predict_proba(X_last)
            prob = float(proba[0][1])
        pred = server.predict(X_last)
        pred_int = int(pred[0]) if hasattr(pred, '__len__') else int(pred)
        signal = 'buy' if pred_int == 1 else 'sell'
        return {'signal': signal, 'prob': prob, 'model_loaded': True}
    except Exception as e:
        # Fallback to rule-based
        signal = choose_signal(prices)
        return {'signal': signal, 'model_loaded': server.is_loaded, 'error': str(e)}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
