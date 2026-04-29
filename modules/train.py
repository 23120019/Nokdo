"""학습 실행 스크립트 - `modules.ml_pipeline`를 사용한 간단한 실험용 엔트리포인트.

예:
  python modules/train.py --symbol 005930.KS --start 2020-01-01 --end 2023-01-01 --out models/samsung.joblib
"""
from pathlib import Path
import argparse
from modules.ml_pipeline import example_run


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--symbol', required=False, default='005930.KS')
    parser.add_argument('--start', required=False, default='2018-01-01')
    parser.add_argument('--end', required=False, default='2024-01-01')
    parser.add_argument('--out', required=False, default='models/model.joblib')
    args = parser.parse_args()

    out = example_run(symbol=args.symbol, start=args.start, end=args.end)
    model = out['model']
    metrics = out['metrics']
    print('Training finished. Metrics:')
    print(metrics)
    p = Path(args.out)
    p.parent.mkdir(parents=True, exist_ok=True)
    import joblib
    joblib.dump(model, str(p))
    print('Saved model to', p)


if __name__ == '__main__':
    main()
