import pandas as pd

from finanalise.analytics import analyze_asset, compare_assets


def sample_prices():
    return pd.DataFrame(
        [
            {"symbol": "AAA", "date": "2024-01-01", "close": 10.0, "volume": 100},
            {"symbol": "AAA", "date": "2024-01-02", "close": 11.0, "volume": 120},
            {"symbol": "AAA", "date": "2024-01-03", "close": 12.0, "volume": 130},
            {"symbol": "BBB", "date": "2024-01-01", "close": 20.0, "volume": 200},
            {"symbol": "BBB", "date": "2024-01-02", "close": 18.0, "volume": 210},
            {"symbol": "BBB", "date": "2024-01-03", "close": 21.0, "volume": 220},
        ]
    )


def test_analyze_asset_returns_financial_statistics():
    result = analyze_asset(sample_prices(), "AAA")

    assert result.symbol == "AAA"
    assert result.rows == 3
    assert result.start_price == 10.0
    assert result.end_price == 12.0
    assert round(result.total_return_pct, 2) == 20.0
    assert result.max_close == 12.0
    assert result.min_close == 10.0
    assert result.total_volume == 350


def test_compare_assets_orders_by_return_descending():
    results = compare_assets(sample_prices(), ["AAA", "BBB"])

    assert [item.symbol for item in results] == ["AAA", "BBB"]
    assert results[0].total_return_pct > results[1].total_return_pct
