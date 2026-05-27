from __future__ import annotations

import pandas as pd
import requests


BCB_CATALOG_SEARCHES = {
    "1": {"label": "Selic", "query": "selic"},
    "2": {"label": "Cambio", "query": "cambio"},
    "3": {"label": "Inflacao", "query": "inflacao"},
    "4": {"label": "PIB", "query": "pib"},
    "5": {"label": "Expectativas de mercado", "query": "expectativas"},
}

BCB_SGS_SERIES = {
    "1": {"label": "Selic diaria", "series_id": 11},
    "2": {"label": "IPCA mensal", "series_id": 433},
    "3": {"label": "Dolar comercial venda", "series_id": 1},
    "4": {"label": "Meta Selic", "series_id": 432},
}


class BCBClient:
    CKAN_URL = "https://dadosabertos.bcb.gov.br/api/3/action/package_search"
    SGS_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{series_id}/dados"

    def __init__(self, get=requests.get) -> None:
        self.get = get

    def search_datasets(self, query: str = "selic", rows: int = 10) -> list[dict]:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        response = self.get(self.CKAN_URL, params={"q": query, "rows": rows, "sort": "metadata_modified desc"}, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json().get("result", {}).get("results", [])

    def latest_dataset(self, query: str = "selic") -> dict | None:
        datasets = self.search_datasets(query, rows=1)
        return datasets[0] if datasets else None

    def fetch_sgs_series(self, series_id: int | str, start: str | None = None, end: str | None = None) -> pd.DataFrame:
        params = {"formato": "json"}
        if start:
            params["dataInicial"] = start
        if end:
            params["dataFinal"] = end
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        response = self.get(self.SGS_URL.format(series_id=series_id), params=params, headers=headers, timeout=30)
        response.raise_for_status()
        return pd.DataFrame(response.json())
