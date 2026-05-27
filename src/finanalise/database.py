from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


class FinanaliseDB:
    def __init__(self, path: str | Path = "data/finanalise.db") -> None:
        self.path = Path(path)

    def connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(self.path)

    def initialize(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS prices (
                    symbol TEXT NOT NULL,
                    date TEXT NOT NULL,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL NOT NULL,
                    volume INTEGER DEFAULT 0,
                    source TEXT NOT NULL,
                    PRIMARY KEY (symbol, date, source)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS macro_series (
                    series_id TEXT NOT NULL,
                    date TEXT NOT NULL,
                    value REAL NOT NULL,
                    source TEXT NOT NULL,
                    PRIMARY KEY (series_id, date)
                )
                """
            )

    def import_prices(self, rows: pd.DataFrame) -> int:
        required = {"symbol", "date", "close", "source"}
        missing = required - set(rows.columns)
        if missing:
            raise ValueError(f"Colunas obrigatorias ausentes: {', '.join(sorted(missing))}")

        frame = rows.copy()
        for column in ["open", "high", "low", "volume"]:
            if column not in frame:
                frame[column] = 0
        frame = frame[["symbol", "date", "open", "high", "low", "close", "volume", "source"]]
        frame["date"] = pd.to_datetime(frame["date"]).dt.date.astype(str)

        with self.connect() as conn:
            before = conn.total_changes
            frame.to_sql("prices_temp", conn, if_exists="replace", index=False)
            conn.execute(
                """
                INSERT OR REPLACE INTO prices
                SELECT symbol, date, open, high, low, close, volume, source
                FROM prices_temp
                """
            )
            conn.execute("DROP TABLE prices_temp")
            return conn.total_changes - before - len(frame)

    def import_macro_series(self, series_id: str, rows: pd.DataFrame, source: str = "bcb") -> int:
        frame = rows.rename(columns={"data": "date", "valor": "value"}).copy()
        frame["series_id"] = series_id
        frame["source"] = source
        frame["date"] = pd.to_datetime(frame["date"], dayfirst=True, errors="coerce").dt.date.astype(str)
        frame["value"] = pd.to_numeric(frame["value"].astype(str).str.replace(",", "."), errors="coerce")
        frame = frame.dropna(subset=["date", "value"])[["series_id", "date", "value", "source"]]

        with self.connect() as conn:
            before = conn.total_changes
            frame.to_sql("macro_temp", conn, if_exists="replace", index=False)
            conn.execute("INSERT OR REPLACE INTO macro_series SELECT * FROM macro_temp")
            conn.execute("DROP TABLE macro_temp")
            return conn.total_changes - before - len(frame)

    def list_symbols(self) -> list[str]:
        with self.connect() as conn:
            rows = conn.execute("SELECT DISTINCT symbol FROM prices ORDER BY symbol").fetchall()
        return [row[0] for row in rows]

    def load_prices(self, symbols: list[str] | None = None) -> pd.DataFrame:
        with self.connect() as conn:
            if not symbols:
                return pd.read_sql_query("SELECT * FROM prices ORDER BY symbol, date", conn)

            placeholders = ",".join("?" for _ in symbols)
            return pd.read_sql_query(
                f"SELECT * FROM prices WHERE symbol IN ({placeholders}) ORDER BY symbol, date",
                conn,
                params=symbols,
            )
