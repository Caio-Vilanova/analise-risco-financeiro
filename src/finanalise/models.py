from dataclasses import dataclass


@dataclass(frozen=True)
class AssetAnalysis:
    symbol: str
    rows: int
    start_date: str
    end_date: str
    start_price: float
    end_price: float
    total_return_pct: float
    mean_daily_return_pct: float
    volatility_pct: float
    min_close: float
    max_close: float
    total_volume: int


@dataclass(frozen=True)
class BenchmarkResult:
    asset_count: int
    sequential_seconds: float
    parallel_seconds: float
    speedup: float
