"""간단한 주식 학습 파이프라인 템플릿.

사용법:
  - 예: `python -m modules.train --symbol 005930.KS --start 2020-01-01 --end 2024-01-01`

이 파일은 하이브리드 모델(시계열 딥러닝 + 트리 기반 특징 모델)을 구성하기 위한
기본 데이터 로딩, 특성공학, 라벨링, 학습/평가 훅을 제공합니다.
구체적 모델(Transformer/LSTM/XGBoost/LightGBM)은 TODO 섹션에 삽입하세요.
"""
from __future__ import annotations

import dataclasses
from typing import Dict, Any, Tuple

import pandas as pd
import numpy as np
import yfinance as yf
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import classification_report, accuracy_score
from sklearn.model_selection import train_test_split
import joblib


@dataclasses.dataclass
class PipelineConfig:
    symbol: str = "005930.KS"
    start: str = "2018-01-01"
    end: str = "2024-01-01"
    horizon: int = 1
    test_size: float = 0.2
    label_threshold: float = 0.0


class MLPipeline:
    def __init__(self, cfg: PipelineConfig | Dict[str, Any]):
        if isinstance(cfg, dict):
            cfg = PipelineConfig(**cfg)
        self.cfg = cfg

    def fetch_data(self) -> pd.DataFrame:
        df = yf.download(self.cfg.symbol, start=self.cfg.start, end=self.cfg.end, progress=False)
        if df.empty:
            raise RuntimeError(f"No data for {self.cfg.symbol} {self.cfg.start}..{self.cfg.end}")
        new_cols = []
        for c in df.columns:
            if isinstance(c, tuple):
                new_cols.append(str(c[0]).lower())
            else:
                new_cols.append(str(c).lower())
        df.columns = new_cols
        return df

    def feature_engineering(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['close_ret'] = df['close'].pct_change()
        df['ma5'] = df['close'].rolling(5).mean()
        df['ma20'] = df['close'].rolling(20).mean()
        df['vol_change'] = df['volume'].pct_change()
        df['ma5_ma20'] = df['ma5'] - df['ma20']
        df['rsi_14'] = self._rsi(df['close'], 14)
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.dropna()
        return df

    def _rsi(self, series: pd.Series, period: int = 14) -> pd.Series:
        delta = series.diff()
        up = delta.clip(lower=0).rolling(window=period).mean()
        down = -delta.clip(upper=0).rolling(window=period).mean()
        rs = up / (down + 1e-9)
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def generate_labels(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['future_close'] = df['close'].shift(-self.cfg.horizon)
        df['future_ret'] = df['future_close'] / df['close'] - 1
        df['label'] = (df['future_ret'] > self.cfg.label_threshold).astype(int)
        df = df.dropna()
        return df

    def prepare_xy(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        features = ['close_ret', 'ma5', 'ma20', 'vol_change', 'ma5_ma20', 'rsi_14']
        X = df[features].replace([np.inf, -np.inf], np.nan).dropna()
        df = df.loc[X.index]
        y = df['label']
        return X, y

    def train_classifier(self, X_train: pd.DataFrame, y_train: pd.Series) -> Any:
        # 기본: scikit-learn GradientBoostingClassifier 사용 (경량, 의존성 적음)
        X_train = X_train.replace([np.inf, -np.inf], np.nan).dropna()
        y_train = y_train.loc[X_train.index]
        model = GradientBoostingClassifier(n_estimators=100, learning_rate=0.05, max_depth=3)
        model.fit(X_train, y_train)
        return model

    def evaluate(self, model: Any, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, Any]:
        preds = model.predict(X_test)
        report = classification_report(y_test, preds, output_dict=True)
        acc = accuracy_score(y_test, preds)
        return {"accuracy": acc, "report": report}

    def save_model(self, model: Any, path: str) -> None:
        joblib.dump(model, path)


def example_run(symbol: str = "005930.KS", start: str = "2020-01-01", end: str = "2023-01-01") -> Dict[str, Any]:
    cfg = PipelineConfig(symbol=symbol, start=start, end=end)
    p = MLPipeline(cfg)
    df = p.fetch_data()
    df = p.feature_engineering(df)
    df = p.generate_labels(df)
    X, y = p.prepare_xy(df)
    split = int(len(X) * (1 - cfg.test_size))
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]
    model = p.train_classifier(X_train, y_train)
    metrics = p.evaluate(model, X_test, y_test)
    return {"model": model, "metrics": metrics}


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--symbol', default='005930.KS')
    parser.add_argument('--start', default='2018-01-01')
    parser.add_argument('--end', default='2024-01-01')
    parser.add_argument('--out', default='models/model.joblib')
    args = parser.parse_args()
    out = example_run(symbol=args.symbol, start=args.start, end=args.end)
    model = out['model']
    print('Metrics:', out['metrics'])
    import os
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    joblib.dump(model, args.out)
