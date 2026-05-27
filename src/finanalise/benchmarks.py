from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from time import perf_counter

import pandas as pd

from finanalise.analytics import analyze_asset
from finanalise.models import BenchmarkResult


def _analyze_worker(payload: tuple[pd.DataFrame, str]):
    prices, symbol = payload
    return analyze_asset(prices, symbol)


def benchmark_analysis(
    prices: pd.DataFrame,
    symbols: list[str],
    max_workers: int | None = None,
) -> BenchmarkResult:
    start = perf_counter()
    for symbol in symbols:
        analyze_asset(prices, symbol)
    sequential_seconds = perf_counter() - start

    # Paralelização deixada de lado por enquanto conforme solicitado pelo usuário
    parallel_seconds = 0.0
    speedup = 0.0
    return BenchmarkResult(
        asset_count=len(symbols),
        sequential_seconds=sequential_seconds,
        parallel_seconds=parallel_seconds,
        speedup=speedup,
    )
