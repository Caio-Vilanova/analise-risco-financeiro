from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def plot_asset_prices(prices: pd.DataFrame, symbol: str, output_dir: str | Path = "data/processed") -> Path:
    frame = prices[prices["symbol"] == symbol].copy()
    if frame.empty:
        raise ValueError(f"Ativo nao encontrado: {symbol}")

    frame["date"] = pd.to_datetime(frame["date"])
    frame = frame.sort_values("date")
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    path = output / f"{symbol.lower()}_prices.png"

    plt.figure(figsize=(10, 5))
    plt.plot(frame["date"], frame["close"], label=symbol)
    plt.title(f"Historico de fechamento - {symbol}")
    plt.xlabel("Data")
    plt.ylabel("Preco de fechamento")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    return path
