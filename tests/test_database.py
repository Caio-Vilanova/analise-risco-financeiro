import pandas as pd

from finanalise.database import FinanaliseDB


def test_database_imports_and_reads_prices(tmp_path):
    db = FinanaliseDB(tmp_path / "finanalise.db")
    db.initialize()

    rows = pd.DataFrame(
        [
            {
                "symbol": "AAA",
                "date": "2024-01-01",
                "open": 9.0,
                "high": 11.0,
                "low": 8.0,
                "close": 10.0,
                "volume": 100,
                "source": "test",
            }
        ]
    )
    inserted = db.import_prices(rows)

    assert inserted == 1
    assert db.list_symbols() == ["AAA"]
    loaded = db.load_prices(["AAA"])
    assert loaded.iloc[0]["close"] == 10.0
    assert loaded.iloc[0]["source"] == "test"
