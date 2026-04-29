"""실거래(또는 시뮬) 통합용 샘플 실행기.

기능:
 - `modules.strategy.choose_signal`를 호출하여 최근 가격으로 매매 신호를 생성
 - 로컬 dry-run 모드 제공 (실제 주문 호출 없음)
 - CLI로 심볼과 루프 주기 지정 가능
"""
from __future__ import annotations

import time
from typing import List, Dict, Any

import yfinance as yf

from modules.strategy import choose_signal


def fetch_recent_prices(symbol: str, period: str = '60d', interval: str = '1d') -> List[Dict[str, Any]]:
    df = yf.download(symbol, period=period, interval=interval, progress=False)
    # yfinance may return MultiIndex columns; normalize to simple lowercase strings
    new_cols = []
    for c in df.columns:
        if isinstance(c, tuple):
            new_cols.append(str(c[0]).lower())
        else:
            new_cols.append(str(c).lower())
    df.columns = new_cols
    df = df.dropna()
    prices = []
    for _, row in df.iterrows():
        prices.append({'close': float(row['close']), 'volume': int(row['volume'])})
    return prices


def sample_run_with_prices(prices: List[Dict[str, Any]]) -> str:
    """테스트용: 외부 네트워크 없이도 동작 확인 가능"""
    return choose_signal(prices)


def run_loop(symbol: str = '005930.KS', period: str = '60d', interval: str = '1d', interval_seconds: int = 60, dry_run: bool = True):
    """주기적으로 시그널을 계산하고(실거래일 경우 주문 로직을 연결)"""
    print('Starting trading loop', 'dry_run=' + str(dry_run))
    try:
        while True:
            try:
                prices = fetch_recent_prices(symbol, period=period, interval=interval)
                if not prices:
                    print('No prices fetched')
                else:
                    signal = choose_signal(prices)
                    print(time.strftime('%Y-%m-%d %H:%M:%S'), symbol, 'signal=', signal)
                    if not dry_run:
                        # TODO: 실제 주문 연결 지점
                        print('Executing order for signal:', signal)
            except Exception as e:
                print('Error in loop:', type(e).__name__, e)
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print('Loop stopped')


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--symbol', default='005930.KS')
    parser.add_argument('--period', default='60d')
    parser.add_argument('--interval', default='1d')
    parser.add_argument('--interval-seconds', type=int, default=60)
    parser.add_argument('--dry-run', action='store_true', default=True)
    args = parser.parse_args()
    run_loop(symbol=args.symbol, period=args.period, interval=args.interval, interval_seconds=args.interval_seconds, dry_run=args.dry_run)
from modules.api_client import call_api

def fn_kt10000(token, params):  # 매수 주문
    return call_api(token, '/api/dostk/ordr', 'kt10000', params)

def fn_credit_order(token, params):  # 신용주문
    return call_api(token, '/api/dostk/ordr', 'kt10001', params)