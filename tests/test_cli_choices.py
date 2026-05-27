from finanalise.cli import FinanaliseCLI


def test_choice_table_returns_default_for_empty_value(tmp_path):
    cli = FinanaliseCLI(tmp_path / "finanalise.db", workspace_path=tmp_path)
    options = {"1": {"label": "Selic", "query": "selic"}}

    selected = cli.resolve_choice(options, "")

    assert selected["query"] == "selic"


def test_choice_table_accepts_custom_value(tmp_path):
    cli = FinanaliseCLI(tmp_path / "finanalise.db", workspace_path=tmp_path)
    options = {"1": {"label": "Selic", "query": "selic"}}

    selected = cli.resolve_choice(options, "cambio")

    assert selected["query"] == "cambio"
    assert selected["label"] == "cambio"
