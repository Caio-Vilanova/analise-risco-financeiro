from zipfile import ZipFile

from finanalise.ingestion.kaggle import load_price_files


def test_load_price_files_reads_csv_inside_zip(tmp_path):
    archive = tmp_path / "prices.zip"
    with ZipFile(archive, "w") as zip_file:
        zip_file.writestr(
            "stocks/AAA.csv",
            "Date,Open,High,Low,Close,Volume\n2024-01-01,9,11,8,10,100\n",
        )
        zip_file.writestr(
            "stocks/BBB.csv",
            "Date,Open,High,Low,Close,Volume\n2024-01-01,19,21,18,20,200\n",
        )

    frame = load_price_files(tmp_path)

    assert sorted(frame["symbol"].unique()) == ["AAA", "BBB"]
    assert len(frame) == 2
    assert set(frame["source"]) == {"zip"}


def test_load_price_files_reads_all_csvs_without_limit(tmp_path):
    (tmp_path / "AAA.csv").write_text(
        "Date,Open,High,Low,Close,Volume\n2024-01-01,9,11,8,10,100\n",
        encoding="utf-8",
    )
    (tmp_path / "BBB.csv").write_text(
        "Date,Open,High,Low,Close,Volume\n2024-01-01,19,21,18,20,200\n",
        encoding="utf-8",
    )

    frame = load_price_files(tmp_path)

    assert sorted(frame["symbol"].unique()) == ["AAA", "BBB"]
    assert len(frame) == 2


def test_load_price_files_reads_txt_csv_inside_zip(tmp_path):
    archive = tmp_path / "stocks.zip"
    with ZipFile(archive, "w") as zip_file:
        zip_file.writestr(
            "Data/Stocks/aapl.us.txt",
            "Date,Open,High,Low,Close,Volume,OpenInt\n2024-01-01,9,11,8,10,100,0\n",
        )

    frame = load_price_files(tmp_path)

    assert frame.iloc[0]["symbol"] == "AAPL"
    assert frame.iloc[0]["close"] == 10


def test_load_price_files_converts_unix_timestamp_to_date(tmp_path):
    archive = tmp_path / "crypto.zip"
    with ZipFile(archive, "w") as zip_file:
        zip_file.writestr(
            "btcusd_1-min_data.csv",
            "Timestamp,Open,High,Low,Close,Volume\n1704067200,9,11,8,10,100\n",
        )

    frame = load_price_files(tmp_path)

    assert frame.iloc[0]["symbol"] == "BTCUSD_1-MIN_DATA"
    assert frame.iloc[0]["date"] == "2024-01-01"


def test_load_price_files_skips_empty_files_inside_zip(tmp_path):
    archive = tmp_path / "stocks.zip"
    with ZipFile(archive, "w") as zip_file:
        zip_file.writestr("empty.csv", "")
        zip_file.writestr(
            "AAA.csv",
            "Date,Open,High,Low,Close,Volume\n2024-01-01,9,11,8,10,100\n",
        )

    frame = load_price_files(tmp_path)

    assert len(frame) == 1
    assert frame.iloc[0]["symbol"] == "AAA"


def test_load_price_files_can_limit_files_and_rows(tmp_path):
    archive = tmp_path / "stocks.zip"
    with ZipFile(archive, "w") as zip_file:
        zip_file.writestr(
            "AAA.csv",
            "Date,Open,High,Low,Close,Volume\n2024-01-01,9,11,8,10,100\n2024-01-02,9,11,8,10,100\n",
        )
        zip_file.writestr(
            "BBB.csv",
            "Date,Open,High,Low,Close,Volume\n2024-01-01,19,21,18,20,200\n",
        )

    frame = load_price_files(tmp_path, max_files=1, rows_per_file=1)

    assert len(frame) == 1
    assert frame.iloc[0]["symbol"] == "AAA"
