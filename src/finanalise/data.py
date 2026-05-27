from __future__ import annotations

from pathlib import Path
from typing import IO

import numpy as np
import pandas as pd


def generate_demo_prices(symbols: list[str] | None = None, days: int = 365, seed: int = 42) -> pd.DataFrame:
    symbols = symbols or ["AAPL", "MSFT", "PETR4", "BTC"]
    rng = np.random.default_rng(seed)
    dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=days)
    rows = []

    for symbol in symbols:
        price = float(rng.uniform(20, 250))
        for date in dates:
            daily_return = rng.normal(0.0008, 0.025)
            open_price = price
            close = max(0.5, open_price * (1 + daily_return))
            high = max(open_price, close) * (1 + abs(rng.normal(0.004, 0.004)))
            low = min(open_price, close) * (1 - abs(rng.normal(0.004, 0.004)))
            volume = int(rng.integers(50_000, 5_000_000))
            rows.append(
                {
                    "symbol": symbol,
                    "date": date.date().isoformat(),
                    "open": round(open_price, 4),
                    "high": round(high, 4),
                    "low": round(low, 4),
                    "close": round(close, 4),
                    "volume": volume,
                    "source": "demo",
                }
            )
            price = close

    return pd.DataFrame(rows)


def normalize_price_frame(
    frame: pd.DataFrame,
    symbol: str | None = None,
    source: str = "csv",
) -> pd.DataFrame:
    lower = {column.lower(): column for column in frame.columns}

    rename = {}
    for expected in ["date", "open", "high", "low", "close", "volume", "symbol"]:
        if expected in lower:
            rename[lower[expected]] = expected
    if "timestamp" in lower and "date" not in rename.values():
        rename[lower["timestamp"]] = "date"
    frame = frame.rename(columns=rename)

    if "date" in frame:
        numeric_date = pd.to_numeric(frame["date"], errors="coerce")
        if numeric_date.notna().mean() > 0.9:
            frame["date"] = pd.to_datetime(numeric_date, unit="s", errors="coerce").dt.date.astype(str)

    if "symbol" not in frame:
        frame["symbol"] = symbol
    if "source" not in frame:
        frame["source"] = source
    return frame


def read_price_csv(
    path: str | Path,
    symbol: str | None = None,
    source: str = "csv",
    nrows: int | None = None,
) -> pd.DataFrame:
    frame = pd.read_csv(path, nrows=nrows)
    return normalize_price_frame(frame, symbol=symbol or Path(path).stem.upper(), source=source)


def read_price_csv_buffer(
    buffer: IO[bytes],
    symbol: str,
    source: str = "zip",
    nrows: int | None = None,
) -> pd.DataFrame:
    frame = pd.read_csv(buffer, nrows=nrows)
    return normalize_price_frame(frame, symbol=symbol, source=source)
