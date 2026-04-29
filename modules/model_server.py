"""간단한 모델 로더/서빙 인터페이스.

기능:
 - 로컬에 저장된 joblib 모델을 로드
 - `predict`/`predict_proba` 메서드 제공
 - 로드 실패 시 `is_loaded` False
"""
from __future__ import annotations

from typing import Any
import os
import joblib
import numpy as np


class ModelServer:
    def __init__(self, model_path: str | None = None):
        self.model_path = model_path or os.environ.get('MODEL_PATH', 'models/model.joblib')
        self.model = None
        self.is_loaded = False
        self.load()

    def load(self) -> None:
        try:
            if not os.path.exists(self.model_path):
                self.is_loaded = False
                return
            self.model = joblib.load(self.model_path)
            self.is_loaded = True
        except Exception:
            self.model = None
            self.is_loaded = False

    def predict(self, X) -> Any:
        if not self.is_loaded:
            raise RuntimeError('Model not loaded')
        return self.model.predict(X)

    def predict_proba(self, X) -> Any:
        if not self.is_loaded:
            raise RuntimeError('Model not loaded')
        if hasattr(self.model, 'predict_proba'):
            return self.model.predict_proba(X)
        # fallback: decision_function or wrap
        if hasattr(self.model, 'decision_function'):
            scores = self.model.decision_function(X)
            # 간단한 시그모이드 근사
            probs = 1 / (1 + np.exp(-scores))
            return np.vstack([1-probs, probs]).T
        raise RuntimeError('Model has no predict_proba')


def get_default_server() -> ModelServer:
    return ModelServer()


if __name__ == '__main__':
    m = ModelServer()
    print('Model loaded:', m.is_loaded, 'Path:', m.model_path)
