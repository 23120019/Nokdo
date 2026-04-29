"""간단한 주식 백테스트 프레임워크.

핵심 특징:
 - 미래 데이터 누수 없이, 각 시점까지의 히스토리만으로 `choose_signal()` 호출
 - 하루 단위 long/short/flat 시뮬레이션
 - 누적수익률, 승률, 샤프, MDD, 거래 횟수 계산

예시:
  python -m modules.backtest --symbol 005930.KS --start 2020-01-01 --end 2023-01-01
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List

import numpy as np
import pandas as pd
import yfinance as yf

from modules.strategy import choose_signal


@dataclass
class BacktestConfig:
    symbol: str = '005930.KS'
    start: str = '2020-01-01'
    end: str = '2023-01-01'
    period: str = '1d'
    interval: str = '1d'
    transaction_cost: float = 0.0005
    warmup: int = 30


class Backtester:
    def __init__(self, cfg: BacktestConfig | Dict[str, Any]):
        if isinstance(cfg, dict):
            cfg = BacktestConfig(**cfg)
        self.cfg = cfg

    def fetch_data(self) -> pd.DataFrame:
        df = yf.download(
            self.cfg.symbol,
            start=self.cfg.start,
            end=self.cfg.end,
            period=None,
            interval=self.cfg.interval,
            progress=False,
        )
        if df.empty:
            raise RuntimeError(f'No data for {self.cfg.symbol}')

        cols = []
        for c in df.columns:
            if isinstance(c, tuple):
                cols.append(str(c[0]).lower())
            else:
                cols.append(str(c).lower())
        df.columns = cols
        df = df.replace([np.inf, -np.inf], np.nan).dropna()
        return df

    def _to_price_dicts(self, df_slice: pd.DataFrame) -> List[Dict[str, Any]]:
        prices: List[Dict[str, Any]] = []
        for _, row in df_slice.iterrows():
            prices.append({'close': float(row['close']), 'volume': int(row.get('volume', 0))})
        return prices

    def run(self, df: pd.DataFrame | None = None) -> Dict[str, Any]:
        if df is None:
            df = self.fetch_data()

        if len(df) <= self.cfg.warmup + 1:
            raise RuntimeError('Not enough data for backtest')

        df = df.copy()
        df['daily_ret'] = df['close'].pct_change()
        df = df.dropna().reset_index(drop=False)

        equity = 1.0
        equity_curve = [equity]
        positions = []
        signals = []
        strategy_returns = []
        trades = 0
        prev_position = 0

        for i in range(self.cfg.warmup, len(df) - 1):
            hist_slice = df.iloc[: i + 1]
            prices = self._to_price_dicts(hist_slice)
            signal = choose_signal(prices)
            signals.append(signal)

            if signal == 'buy':
                position = 1
            elif signal == 'sell':
                position = -1
            else:
                position = 0

            positions.append(position)
            if position != prev_position:
                trades += 1
            prev_position = position

            next_ret = float(df.iloc[i + 1]['daily_ret'])
            gross = position * next_ret
            net = gross - (self.cfg.transaction_cost if position != 0 else 0.0)
            equity *= (1.0 + net)
            strategy_returns.append(net)
            equity_curve.append(equity)

        equity_series = pd.Series(equity_curve)
        return self._metrics(df, equity_series, strategy_returns, positions, signals, trades)

    def _metrics(
        self,
        df: pd.DataFrame,
        equity_series: pd.Series,
        strategy_returns: List[float],
        positions: List[int],
        signals: List[str],
        trades: int,
    ) -> Dict[str, Any]:
        returns = pd.Series(strategy_returns)
        if returns.empty:
            raise RuntimeError('No strategy returns computed')

        total_return = float(equity_series.iloc[-1] - 1.0)
        n_days = len(returns)
        ann_return = float((equity_series.iloc[-1] ** (252 / max(n_days, 1))) - 1.0)
        ann_vol = float(returns.std(ddof=0) * np.sqrt(252)) if len(returns) > 1 else 0.0
        sharpe = float((returns.mean() / (returns.std(ddof=0) + 1e-12)) * np.sqrt(252)) if len(returns) > 1 else 0.0

        roll_max = equity_series.cummax()
        drawdown = equity_series / roll_max - 1.0
        max_drawdown = float(drawdown.min())

        wins = int((returns > 0).sum())
        losses = int((returns < 0).sum())
        win_rate = float(wins / max(len(returns), 1))

        benchmark_ret = df['close'].pct_change().dropna()
        benchmark_equity = float((1.0 + benchmark_ret).prod()) - 1.0 if not benchmark_ret.empty else 0.0

        return {
            'symbol': self.cfg.symbol,
            'total_return': total_return,
            'annualized_return': ann_return,
            'annualized_volatility': ann_vol,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'trades': trades,
            'signals': signals,
            'positions': positions,
            'equity_curve': equity_series.tolist(),
            'benchmark_return': float(benchmark_equity),
            'days': n_days,
            'wins': wins,
            'losses': losses,
        }


def run_backtest(symbol: str = '005930.KS', start: str = '2020-01-01', end: str = '2023-01-01', transaction_cost: float = 0.0005, warmup: int = 30) -> Dict[str, Any]:
    bt = Backtester(BacktestConfig(symbol=symbol, start=start, end=end, transaction_cost=transaction_cost, warmup=warmup))
    return bt.run()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--symbol', default='005930.KS')
    parser.add_argument('--start', default='2020-01-01')
    parser.add_argument('--end', default='2023-01-01')
    parser.add_argument('--transaction-cost', type=float, default=0.0005)
    parser.add_argument('--warmup', type=int, default=30)
    args = parser.parse_args()

    result = run_backtest(
        symbol=args.symbol,
        start=args.start,
        end=args.end,
        transaction_cost=args.transaction_cost,
        warmup=args.warmup,
    )

    print('Backtest result:')
    for key in ['symbol', 'total_return', 'annualized_return', 'annualized_volatility', 'sharpe_ratio', 'max_drawdown', 'win_rate', 'trades', 'benchmark_return', 'days', 'wins', 'losses']:
        print(f'{key}: {result[key]}')
