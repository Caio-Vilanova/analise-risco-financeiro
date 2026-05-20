"""
FinScan - Pipeline Serial de Análise de Risco de Portfólio
Trabalho Acadêmico - Computação Paralela e Distribuída | Unieuro
Aluno: Matheus Nery Walkowicz

Fase 1: Execução SERIALIZADA com instrumentação de tempo por etapa.
Objetivo: estabelecer baseline para comparação com versão paralela.

Ativos analisados:
  B3:    PETR4, VALE3, ITUB4, BBDC4, MGLU3
  Crypto: BTC-USD, ETH-USD, BNB-USD, SOL-USD, ADA-USD
"""

import time
import json
import math
import random
import statistics
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Optional

# ─────────────────────────────────────────────
# Configuração
# ─────────────────────────────────────────────
ASSETS_B3 = ["PETR4", "VALE3", "ITUB4", "BBDC4", "MGLU3"]
ASSETS_CRYPTO = ["BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "ADA-USD"]
ALL_ASSETS = ASSETS_B3 + ASSETS_CRYPTO

LOOKBACK_DAYS = 252          # ~1 ano de pregões
VAR_CONFIDENCE = 0.95        # Value at Risk 95%
PORTFOLIO_VALUE = 100_000.0  # R$ 100.000
SIMULATED_FETCH_DELAY = 0.3  # simula latência de API por ativo (seg)
RANDOM_SEED = 42

random.seed(RANDOM_SEED)


# ─────────────────────────────────────────────
# Estruturas de dados
# ─────────────────────────────────────────────
@dataclass
class PriceHistory:
    ticker: str
    prices: list[float]
    dates: list[str]
    source: str


@dataclass
class AssetMetrics:
    ticker: str
    total_return: float        # retorno acumulado %
    annualized_return: float   # retorno anualizado %
    volatility: float          # desvio padrão anualizado %
    sharpe_ratio: float        # Sharpe (rf = 0.1075 SELIC)
    max_drawdown: float        # drawdown máximo %
    var_95: float              # Value at Risk 95% (R$)
    cvar_95: float             # CVaR/Expected Shortfall 95% (R$)
    beta: float                # beta vs benchmark simulado


@dataclass
class CorrelationMatrix:
    tickers: list[str]
    matrix: list[list[float]]


@dataclass
class PortfolioReport:
    generated_at: str
    assets: list[AssetMetrics]
    correlation: CorrelationMatrix
    portfolio_var: float
    portfolio_return: float
    portfolio_volatility: float
    benchmark_info: dict


@dataclass
class BenchmarkResult:
    stage: str
    duration_sec: float
    assets_processed: int
    notes: str = ""


# ─────────────────────────────────────────────
# Gerador de dados sintéticos (substitui API real)
# Usa GBM (Geometric Brownian Motion) — padrão acadêmico
# ─────────────────────────────────────────────
def _gbm_prices(ticker: str, n: int = LOOKBACK_DAYS) -> list[float]:
    """
    Gera série de preços via Geometric Brownian Motion.
    dS = mu*S*dt + sigma*S*dW
    Parâmetros calibrados por classe de ativo.
    """
    crypto_tickers = {"BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "ADA-USD"}
    is_crypto = ticker in crypto_tickers

    # Parâmetros por perfil
    mu_annual = random.uniform(0.15, 0.45) if is_crypto else random.uniform(0.08, 0.25)
    sigma_annual = random.uniform(0.55, 1.20) if is_crypto else random.uniform(0.20, 0.50)
    s0 = random.uniform(10, 80) if not is_crypto else random.uniform(100, 50_000)

    dt = 1 / 252
    mu_dt = (mu_annual - 0.5 * sigma_annual ** 2) * dt
    sigma_dt = sigma_annual * math.sqrt(dt)

    prices = [s0]
    for _ in range(n - 1):
        shock = random.gauss(0, 1)
        new_price = prices[-1] * math.exp(mu_dt + sigma_dt * shock)
        prices.append(new_price)
    return prices


def _dates_series(n: int) -> list[str]:
    end = datetime.today()
    dates = []
    count = 0
    d = end - timedelta(days=n * 2)
    while count < n:
        if d.weekday() < 5:  # seg-sex
            dates.append(d.strftime("%Y-%m-%d"))
            count += 1
        d += timedelta(days=1)
    return dates


# ─────────────────────────────────────────────
# Etapas do pipeline
# ─────────────────────────────────────────────

def stage_fetch(tickers: list[str]) -> tuple[list[PriceHistory], BenchmarkResult]:
    """
    Etapa 1 — Coleta de dados históricos.
    (Serial: um ativo por vez, simulando delay de rede)
    """
    t0 = time.perf_counter()
    results = []
    dates = _dates_series(LOOKBACK_DAYS)

    for ticker in tickers:
        time.sleep(SIMULATED_FETCH_DELAY)  # simula I/O bound
        prices = _gbm_prices(ticker)
        results.append(PriceHistory(
            ticker=ticker,
            prices=prices,
            dates=dates,
            source="GBM-Synthetic (API simulada)"
        ))

    duration = time.perf_counter() - t0
    bench = BenchmarkResult(
        stage="fetch",
        duration_sec=round(duration, 4),
        assets_processed=len(tickers),
        notes=f"delay={SIMULATED_FETCH_DELAY}s/ativo, total={len(tickers)} ativos"
    )
    return results, bench


def _daily_returns(prices: list[float]) -> list[float]:
    return [(prices[i] - prices[i - 1]) / prices[i - 1] for i in range(1, len(prices))]


def _max_drawdown(prices: list[float]) -> float:
    peak = prices[0]
    max_dd = 0.0
    for p in prices:
        if p > peak:
            peak = p
        dd = (peak - p) / peak
        if dd > max_dd:
            max_dd = dd
    return max_dd


def _var_cvar(returns: list[float], confidence: float, portfolio_value: float) -> tuple[float, float]:
    sorted_r = sorted(returns)
    idx = int((1 - confidence) * len(sorted_r))
    var = -sorted_r[idx] * portfolio_value
    cvar = -statistics.mean(sorted_r[:idx + 1]) * portfolio_value if idx > 0 else var
    return var, cvar


def stage_compute_metrics(histories: list[PriceHistory]) -> tuple[list[AssetMetrics], BenchmarkResult]:
    """
    Etapa 2 — Cálculo de métricas individuais por ativo.
    (Serial: CPU-bound, um ativo por vez)
    """
    t0 = time.perf_counter()
    metrics = []
    rf_daily = 0.1075 / 252  # SELIC anualizada → diária

    for h in histories:
        prices = h.prices
        returns = _daily_returns(prices)

        total_r = (prices[-1] - prices[0]) / prices[0]
        ann_r = (1 + total_r) ** (252 / len(prices)) - 1
        vol = statistics.stdev(returns) * math.sqrt(252)
        excess = [r - rf_daily for r in returns]
        sharpe = (statistics.mean(excess) * 252) / (statistics.stdev(excess) * math.sqrt(252) + 1e-9)
        mdd = _max_drawdown(prices)
        var, cvar = _var_cvar(returns, VAR_CONFIDENCE, PORTFOLIO_VALUE / len(histories))

        # beta simulado vs IBOV/BTC benchmark
        bm_returns = [random.gauss(0.0003, 0.01) for _ in returns]
        cov = sum((r - statistics.mean(returns)) * (b - statistics.mean(bm_returns))
                  for r, b in zip(returns, bm_returns)) / len(returns)
        var_bm = statistics.variance(bm_returns)
        beta = cov / var_bm if var_bm > 0 else 1.0

        metrics.append(AssetMetrics(
            ticker=h.ticker,
            total_return=round(total_r * 100, 2),
            annualized_return=round(ann_r * 100, 2),
            volatility=round(vol * 100, 2),
            sharpe_ratio=round(sharpe, 4),
            max_drawdown=round(mdd * 100, 2),
            var_95=round(var, 2),
            cvar_95=round(cvar, 2),
            beta=round(beta, 4)
        ))

    duration = time.perf_counter() - t0
    bench = BenchmarkResult(
        stage="compute_metrics",
        duration_sec=round(duration, 4),
        assets_processed=len(histories)
    )
    return metrics, bench


def stage_correlation(histories: list[PriceHistory]) -> tuple[CorrelationMatrix, BenchmarkResult]:
    """
    Etapa 3 — Matriz de correlação entre todos os ativos.
    (Serial: O(n²) pares)
    """
    t0 = time.perf_counter()
    n = len(histories)
    returns_map = {h.ticker: _daily_returns(h.prices) for h in histories}
    tickers = [h.ticker for h in histories]

    matrix = []
    for ti in tickers:
        row = []
        for tj in tickers:
            ri = returns_map[ti]
            rj = returns_map[tj]
            mean_i = statistics.mean(ri)
            mean_j = statistics.mean(rj)
            cov = sum((a - mean_i) * (b - mean_j) for a, b in zip(ri, rj)) / len(ri)
            std_i = statistics.stdev(ri)
            std_j = statistics.stdev(rj)
            corr = cov / (std_i * std_j + 1e-9)
            row.append(round(corr, 4))
        matrix.append(row)

    duration = time.perf_counter() - t0
    bench = BenchmarkResult(
        stage="correlation",
        duration_sec=round(duration, 4),
        assets_processed=n,
        notes=f"{n*n} pares calculados"
    )
    return CorrelationMatrix(tickers=tickers, matrix=matrix), bench


def stage_portfolio_risk(
    metrics: list[AssetMetrics],
    corr: CorrelationMatrix
) -> tuple[dict, BenchmarkResult]:
    """
    Etapa 4 — Risco agregado do portfólio (pesos iguais).
    Usa matriz de covariância completa: σ_p² = w' Σ w
    """
    t0 = time.perf_counter()
    n = len(metrics)
    w = 1.0 / n  # peso uniforme

    vol_map = {m.ticker: m.volatility / 100 for m in metrics}
    tickers = corr.tickers

    # Matriz de covariância: Σ_ij = ρ_ij * σ_i * σ_j
    port_var = 0.0
    for i, ti in enumerate(tickers):
        for j, tj in enumerate(tickers):
            rho = corr.matrix[i][j]
            port_var += w * w * rho * vol_map.get(ti, 0) * vol_map.get(tj, 0)

    port_vol = math.sqrt(port_var) * math.sqrt(252)
    port_ret = statistics.mean([m.annualized_return for m in metrics])
    port_var_95 = sum(m.var_95 for m in metrics) * w * n  # simplificação linear

    result = {
        "portfolio_return_pct": round(port_ret, 2),
        "portfolio_volatility_pct": round(port_vol * 100, 2),
        "portfolio_var_95_brl": round(port_var_95, 2),
        "weights": {t: round(w, 4) for t in tickers},
        "n_assets": n
    }

    duration = time.perf_counter() - t0
    bench = BenchmarkResult(
        stage="portfolio_risk",
        duration_sec=round(duration, 4),
        assets_processed=n
    )
    return result, bench


def stage_report(
    metrics: list[AssetMetrics],
    corr: CorrelationMatrix,
    portfolio: dict,
    output_path: str = "reports/report_serial.json"
) -> BenchmarkResult:
    """
    Etapa 5 — Geração do relatório final em JSON.
    """
    t0 = time.perf_counter()

    report = {
        "meta": {
            "generated_at": datetime.now().isoformat(),
            "mode": "SERIAL",
            "lookback_days": LOOKBACK_DAYS,
            "portfolio_value_brl": PORTFOLIO_VALUE,
            "var_confidence": VAR_CONFIDENCE,
            "n_assets": len(metrics)
        },
        "assets": [asdict(m) for m in metrics],
        "correlation_matrix": {
            "tickers": corr.tickers,
            "matrix": corr.matrix
        },
        "portfolio": portfolio
    }

    print(json.dumps(report, indent=2, ensure_ascii=False))

    duration = time.perf_counter() - t0
    bench = BenchmarkResult(
        stage="report",
        duration_sec=round(duration, 4),
        assets_processed=len(metrics),
        notes="output via stdout (ambiente online)"
    )
    return bench


# ─────────────────────────────────────────────
# Orquestrador principal
# ─────────────────────────────────────────────

def run_serial_pipeline(tickers: list[str] = ALL_ASSETS) -> dict:
    """
    Executa o pipeline COMPLETO de forma SERIAL.
    Retorna dicionário com resultados e benchmarks de cada etapa.
    """
    print("=" * 60)
    print("  FinScan — Pipeline Serial")
    print(f"  Ativos: {len(tickers)} | Início: {datetime.now():%H:%M:%S}")
    print("=" * 60)

    pipeline_start = time.perf_counter()
    benchmarks: list[BenchmarkResult] = []

    # ── Etapa 1: Coleta ──
    print("\n[1/5] Coletando dados históricos...")
    histories, b1 = stage_fetch(tickers)
    benchmarks.append(b1)
    print(f"      ✓ {b1.duration_sec:.3f}s  ({b1.assets_processed} ativos)")

    # ── Etapa 2: Métricas ──
    print("\n[2/5] Calculando métricas por ativo...")
    metrics, b2 = stage_compute_metrics(histories)
    benchmarks.append(b2)
    print(f"      ✓ {b2.duration_sec:.3f}s  ({b2.assets_processed} ativos)")

    # ── Etapa 3: Correlação ──
    print("\n[3/5] Construindo matriz de correlação...")
    corr, b3 = stage_correlation(histories)
    benchmarks.append(b3)
    print(f"      ✓ {b3.duration_sec:.3f}s  ({b3.notes})")

    # ── Etapa 4: Risco do portfólio ──
    print("\n[4/5] Calculando risco do portfólio...")
    portfolio, b4 = stage_portfolio_risk(metrics, corr)
    benchmarks.append(b4)
    print(f"      ✓ {b4.duration_sec:.3f}s")

    # ── Etapa 5: Relatório ──
    print("\n[5/5] Gerando relatório...")
    b5 = stage_report(metrics, corr, portfolio)
    benchmarks.append(b5)
    print(f"      ✓ {b5.duration_sec:.3f}s  ({b5.notes})")

    total = time.perf_counter() - pipeline_start

    # ── Benchmark summary ──
    print("\n" + "─" * 60)
    print("  BENCHMARK SERIAL")
    print("─" * 60)
    for b in benchmarks:
        pct = (b.duration_sec / total) * 100
        bar = "█" * int(pct / 3)
        print(f"  {b.stage:<20} {b.duration_sec:>7.3f}s  {pct:5.1f}%  {bar}")
    print("─" * 60)
    print(f"  {'TOTAL':<20} {total:>7.3f}s  100.0%")
    print("─" * 60)

    # ── Benchmark JSON ──
    bench_data = {
        "mode": "serial",
        "timestamp": datetime.now().isoformat(),
        "total_sec": round(total, 4),
        "stages": [asdict(b) for b in benchmarks],
        "n_assets": len(tickers)
    }
    print("\n  BENCHMARK JSON:")
    print(json.dumps(bench_data, indent=2))

    return {
        "metrics": metrics,
        "correlation": corr,
        "portfolio": portfolio,
        "benchmarks": benchmarks,
        "total_sec": round(total, 4)
    }


if __name__ == "__main__":
    result = run_serial_pipeline()

    print("\nTop 3 por Sharpe Ratio:")
    top = sorted(result["metrics"], key=lambda m: m.sharpe_ratio, reverse=True)[:3]
    for i, m in enumerate(top, 1):
        print(f"  {i}. {m.ticker:<10} Sharpe={m.sharpe_ratio:.4f}  Ret={m.annualized_return:.1f}%  Vol={m.volatility:.1f}%")

    print(f"\nPortfólio:")
    p = result["portfolio"]
    print(f"  Retorno esperado : {p['portfolio_return_pct']:.2f}%")
    print(f"  Volatilidade     : {p['portfolio_volatility_pct']:.2f}%")
    print(f"  VaR 95% (R$)     : R$ {p['portfolio_var_95_brl']:,.2f}")
