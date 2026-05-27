from __future__ import annotations

import pandas as pd

from finanalise.models import AssetAnalysis


def _prepare_asset_frame(prices: pd.DataFrame, symbol: str) -> pd.DataFrame:
    frame = prices[prices["symbol"] == symbol].copy()
    if frame.empty:
        raise ValueError(f"Ativo nao encontrado: {symbol}")

    frame["date"] = pd.to_datetime(frame["date"])
    frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
    frame["volume"] = pd.to_numeric(frame.get("volume", 0), errors="coerce").fillna(0)
    frame = frame.dropna(subset=["close"]).sort_values("date")
    if frame.empty:
        raise ValueError(f"Ativo sem precos validos: {symbol}")
    return frame


def analyze_asset(prices: pd.DataFrame, symbol: str) -> AssetAnalysis:
    frame = _prepare_asset_frame(prices, symbol)
    returns = frame["close"].pct_change().dropna()
    start_price = float(frame["close"].iloc[0])
    end_price = float(frame["close"].iloc[-1])
    total_return = ((end_price / start_price) - 1) * 100 if start_price else 0.0

    return AssetAnalysis(
        symbol=symbol,
        rows=int(len(frame)),
        start_date=frame["date"].iloc[0].date().isoformat(),
        end_date=frame["date"].iloc[-1].date().isoformat(),
        start_price=start_price,
        end_price=end_price,
        total_return_pct=float(total_return),
        mean_daily_return_pct=float(returns.mean() * 100) if not returns.empty else 0.0,
        volatility_pct=float(returns.std(ddof=0) * 100) if not returns.empty else 0.0,
        min_close=float(frame["close"].min()),
        max_close=float(frame["close"].max()),
        total_volume=int(frame["volume"].sum()),
    )


def compare_assets(prices: pd.DataFrame, symbols: list[str]) -> list[AssetAnalysis]:
    results = [analyze_asset(prices, symbol) for symbol in symbols]
    return sorted(results, key=lambda item: item.total_return_pct, reverse=True)
