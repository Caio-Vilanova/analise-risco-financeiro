from zipfile import ZipFile

from finanalise.cli import FinanaliseCLI


def test_cli_imports_workspace_zips_when_database_is_empty(tmp_path):
    with ZipFile(tmp_path / "prices.zip", "w") as zip_file:
        zip_file.writestr(
            "AAA.csv",
            "Date,Open,High,Low,Close,Volume\n2024-01-01,9,11,8,10,100\n",
        )

    cli = FinanaliseCLI(tmp_path / "finanalise.db", workspace_path=tmp_path)

    inserted = cli.ensure_ready()

    assert inserted == 1
    assert cli.db.list_symbols() == ["AAA"]


def test_cli_does_not_seed_demo_data_twice(tmp_path):
    with ZipFile(tmp_path / "prices.zip", "w") as zip_file:
        zip_file.writestr(
            "AAA.csv",
            "Date,Open,High,Low,Close,Volume\n2024-01-01,9,11,8,10,100\n",
        )

    cli = FinanaliseCLI(tmp_path / "finanalise.db", workspace_path=tmp_path)

    first = cli.ensure_ready()
    second = cli.ensure_ready()

    assert first > 0
    assert second == 0


def test_cli_uses_demo_data_only_when_workspace_has_no_csv_or_zip(tmp_path):
    cli = FinanaliseCLI(tmp_path / "finanalise.db", workspace_path=tmp_path)

    inserted = cli.ensure_ready()

    assert inserted > 0
    assert cli.db.list_symbols() == ["AAPL", "BTC", "MSFT", "PETR4"]
