from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt
from rich.table import Table

from finanalise.analytics import analyze_asset, compare_assets
from finanalise.benchmarks import benchmark_analysis
from finanalise.data import generate_demo_prices
from finanalise.database import FinanaliseDB
from finanalise.ingestion.bcb import BCB_CATALOG_SEARCHES, BCB_SGS_SERIES, BCBClient
from finanalise.ingestion.kaggle import load_price_files
from finanalise.models import AssetAnalysis
from finanalise.visualization import plot_asset_prices


class FinanaliseCLI:
    def __init__(
        self,
        db_path: str | Path = "data/finanalise.db",
        workspace_path: str | Path = ".",
    ) -> None:
        self.console = Console()
        self.db = FinanaliseDB(db_path)
        self.workspace_path = Path(workspace_path)
        self.bootstrap_max_files = 8
        self.bootstrap_rows_per_file = 500

    def run(self) -> None:
        inserted = self.ensure_ready()
        if inserted:
            self.console.print(f"[green]Pronto para uso:[/green] banco criado com {inserted} registros.")
        while True:
            self.console.print(
                Panel.fit(
                    "[bold]Finanalise[/bold]\nPainel financeiro local",
                    border_style="cyan",
                )
            )
            table = Table(show_header=False)
            table.add_row("1", "Ver ativos")
            table.add_row("2", "Analisar ativo")
            table.add_row("3", "Comparar ativos")
            table.add_row("4", "Resumo da carteira")
            table.add_row("5", "Gerar grafico PNG")
            table.add_row("6", "Consultar Banco Central")
            table.add_row("7", "Recarregar dados de demonstracao")
            table.add_row("0", "Sair")
            self.console.print(table)

            choice = Prompt.ask("Escolha", default="1")
            actions = {
                "1": self.show_symbols,
                "2": self.show_asset_analysis,
                "3": self.show_comparison,
                "4": self.show_portfolio_summary,
                "5": self.create_chart,
                "6": self.show_bcb_catalog,
                "7": self.import_demo,
                "0": None,
            }
            action = actions.get(choice)
            if choice == "0":
                self.console.print("[green]Ate logo.[/green]")
                return
            if action is None:
                self.console.print("[red]Opcao invalida.[/red]")
                continue
            try:
                action()
            except Exception as exc:
                self.console.print(f"[red]Erro:[/red] {exc}")

    def ensure_ready(self) -> int:
        self.db.initialize()
        if self.db.list_symbols():
            return 0
        frame = self.load_workspace_prices()
        if not frame.empty:
            return self.db.import_prices(frame)
        frame = generate_demo_prices(["AAPL", "MSFT", "PETR4", "BTC"], days=180)
        return self.db.import_prices(frame)

    def load_workspace_prices(self):
        return load_price_files(
            self.workspace_path,
            max_files=self.bootstrap_max_files,
            rows_per_file=self.bootstrap_rows_per_file,
        )

    def initialize(self) -> None:
        self.db.initialize()
        self.console.print("[green]Banco inicializado.[/green]")

    def import_demo(self) -> None:
        days = IntPrompt.ask("Quantidade de dias historicos", default=365)
        symbols = Prompt.ask("Ativos separados por virgula", default="AAPL,MSFT,PETR4,BTC")
        frame = generate_demo_prices([item.strip().upper() for item in symbols.split(",") if item.strip()], days=days)
        inserted = self.db.import_prices(frame)
        self.console.print(f"[green]{inserted} registros importados.[/green]")

    def show_bcb_catalog(self) -> None:
        table = Table(title="Banco Central")
        table.add_column("Opcao")
        table.add_column("Acao")
        table.add_row("1", "Buscar datasets no catalogo")
        table.add_row("2", "Consultar serie SGS")
        self.console.print(table)
        choice = Prompt.ask("Escolha", default="1")
        if choice == "2":
            self.show_bcb_sgs_series()
            return

        query = self.ask_from_options("Buscar no catalogo do BCB", BCB_CATALOG_SEARCHES)["query"]
        client = BCBClient()
        datasets = client.search_datasets(query, rows=8)
        table = Table(title="Datasets BCB")
        table.add_column("Nome")
        table.add_column("Titulo")
        table.add_column("Modificado")
        for item in datasets:
            table.add_row(item.get("name", ""), item.get("title", ""), item.get("metadata_modified", ""))
        self.console.print(table)

    def show_bcb_sgs_series(self) -> None:
        selected = self.ask_from_options("Serie SGS", BCB_SGS_SERIES)
        days = IntPrompt.ask("Ultimos dias", default=30)
        client = BCBClient()
        frame = client.fetch_sgs_series(selected["series_id"])
        frame = frame.tail(days)
        table = Table(title=selected["label"])
        table.add_column("Data")
        table.add_column("Valor")
        for row in frame.to_dict("records"):
            table.add_row(str(row.get("data", "")), str(row.get("valor", "")))
        self.console.print(table)

    def show_symbols(self) -> None:
        symbols = self.db.list_symbols()
        if not symbols:
            self.console.print("[yellow]Nenhum ativo importado ainda.[/yellow]")
            return
        self.console.print(Panel(", ".join(symbols), title="Ativos"))

    def show_asset_analysis(self) -> None:
        symbol = self.ask_symbol("Ativo")
        result = analyze_asset(self.db.load_prices([symbol]), symbol)
        self._print_analysis_table([result], f"Analise de {symbol}")

    def show_comparison(self) -> None:
        symbols = [item.strip().upper() for item in Prompt.ask("Ativos separados por virgula").split(",") if item.strip()]
        results = compare_assets(self.db.load_prices(symbols), symbols)
        self._print_analysis_table(results, "Comparacao de ativos")

    def show_portfolio_summary(self) -> None:
        symbols = self.db.list_symbols()
        if not symbols:
            self.console.print("[yellow]Nenhum dado disponivel ainda.[/yellow]")
            return
        result = benchmark_analysis(self.db.load_prices(symbols), symbols)
        table = Table(title="Resumo da carteira")
        table.add_column("Ativos")
        table.add_column("Tempo de analise")
        table.add_column("Otimizacao")
        table.add_row(
            str(result.asset_count),
            f"{result.parallel_seconds:.4f}s",
            f"{result.speedup:.2f}x",
        )
        self.console.print(table)

    def create_chart(self) -> None:
        symbol = self.ask_symbol("Ativo")
        path = plot_asset_prices(self.db.load_prices([symbol]), symbol)
        self.console.print(f"[green]Grafico salvo em:[/green] {path}")

    def ask_symbol(self, title: str) -> str:
        symbols = self.db.list_symbols()
        options = {str(index): {"label": symbol, "symbol": symbol} for index, symbol in enumerate(symbols, start=1)}
        return self.ask_from_options(title, options)["symbol"]

    def ask_from_options(self, title: str, options: dict[str, dict]) -> dict:
        table = Table(title=title)
        table.add_column("Opcao")
        table.add_column("Valor")
        for key, value in options.items():
            table.add_row(key, str(value["label"]))
        table.add_row("outro", "Digitar outro valor")
        self.console.print(table)
        choice = Prompt.ask("Escolha", default="1")
        return self.resolve_choice(options, choice)

    def resolve_choice(self, options: dict[str, dict], choice: str) -> dict:
        if not choice:
            choice = "1"
        if choice in options:
            return options[choice]
        return {"label": choice, "query": choice, "symbol": choice.upper()}

    def _print_analysis_table(self, results: list[AssetAnalysis], title: str) -> None:
        table = Table(title=title)
        for column in ["symbol", "rows", "start_date", "end_date", "total_return_pct", "volatility_pct", "total_volume"]:
            table.add_column(column)
        for result in results:
            values = asdict(result)
            table.add_row(
                values["symbol"],
                str(values["rows"]),
                values["start_date"],
                values["end_date"],
                f"{values['total_return_pct']:.2f}%",
                f"{values['volatility_pct']:.2f}%",
                str(values["total_volume"]),
            )
        self.console.print(table)
