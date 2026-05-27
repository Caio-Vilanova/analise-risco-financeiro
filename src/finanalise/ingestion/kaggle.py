from __future__ import annotations

from io import BytesIO
from pathlib import Path
from zipfile import BadZipFile, ZipFile

import pandas as pd

from finanalise.data import read_price_csv, read_price_csv_buffer


def download_kaggle_dataset(dataset_slug: str) -> Path:
    import kagglehub

    return Path(kagglehub.dataset_download(dataset_slug))


def _symbol_from_name(name: str) -> str:
    return Path(name).stem.upper().replace(".US", "")


def _read_zip_csvs(
    path: Path,
    max_files: int | None = None,
    rows_per_file: int | None = None,
) -> list[pd.DataFrame]:
    frames = []
    imported_files = 0
    try:
        with ZipFile(path) as zip_file:
            for member in sorted(zip_file.namelist()):
                if max_files is not None and imported_files >= max_files:
                    break
                suffix = Path(member).suffix.lower()
                if member.endswith("/") or suffix not in {".csv", ".txt"}:
                    continue
                with zip_file.open(member) as csv_file:
                    payload = BytesIO(csv_file.read())
                try:
                    frame = read_price_csv_buffer(
                        payload,
                        symbol=_symbol_from_name(member),
                        source="zip",
                        nrows=rows_per_file,
                    )
                except Exception:
                    continue
                frames.append(frame)
                imported_files += 1
    except BadZipFile:
        return []
    return frames


def load_price_files(
    folder: str | Path,
    max_files: int | None = None,
    rows_per_file: int | None = None,
) -> pd.DataFrame:
    root = Path(folder)
    frames = []
    ignored_parts = {".venv", ".pytest_cache", "__pycache__", "data"}
    imported_files = 0

    for path in sorted(root.rglob("*.csv")):
        if max_files is not None and imported_files >= max_files:
            break
        if ignored_parts.intersection(path.parts):
            continue
        try:
            frames.append(read_price_csv(path, source="csv", nrows=rows_per_file))
            imported_files += 1
        except Exception:
            continue

    for path in sorted(root.rglob("*.zip")):
        if max_files is not None and imported_files >= max_files:
            break
        if ignored_parts.intersection(path.parts):
            continue
        remaining = None if max_files is None else max_files - imported_files
        zip_frames = _read_zip_csvs(path, max_files=remaining, rows_per_file=rows_per_file)
        frames.extend(zip_frames)
        imported_files += len(zip_frames)

    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def load_kaggle_price_files(folder: str | Path, limit_files: int | None = None) -> pd.DataFrame:
    frame = load_price_files(folder)
    if limit_files:
        symbols = sorted(frame["symbol"].dropna().unique())[:limit_files]
        return frame[frame["symbol"].isin(symbols)].copy()
    return frame
