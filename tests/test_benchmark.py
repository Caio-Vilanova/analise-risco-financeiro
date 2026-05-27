import pandas as pd

from finanalise.benchmarks import benchmark_analysis


def test_portfolio_timing_runs_with_multiple_assets():
    data = pd.DataFrame(
        [
            {"symbol": symbol, "date": f"2024-01-0{day}", "close": 10 + day, "volume": 100}
            for symbol in ["AAA", "BBB"]
            for day in range(1, 4)
        ]
    )

    result = benchmark_analysis(data, ["AAA", "BBB"], max_workers=2)

    assert result.sequential_seconds >= 0
    assert result.parallel_seconds >= 0
    assert result.asset_count == 2
    assert result.speedup >= 0
