from finanalise.ingestion.bcb import BCBClient, BCB_CATALOG_SEARCHES, BCB_SGS_SERIES


def test_bcb_client_parses_ckan_package_search():
    def fake_get(url, params=None, timeout=30):
        class Response:
            def raise_for_status(self):
                return None

            def json(self):
                return {
                    "result": {
                        "results": [
                            {
                                "name": "selic",
                                "title": "Taxa Selic",
                                "metadata_modified": "2026-01-10T12:00:00",
                            }
                        ]
                    }
                }

        return Response()

    client = BCBClient(get=fake_get)
    datasets = client.search_datasets("selic")

    assert datasets[0]["name"] == "selic"
    assert datasets[0]["title"] == "Taxa Selic"


def test_bcb_presets_include_common_searches_and_sgs_series():
    assert BCB_CATALOG_SEARCHES["1"]["query"] == "selic"
    assert BCB_SGS_SERIES["1"]["series_id"] == 11
