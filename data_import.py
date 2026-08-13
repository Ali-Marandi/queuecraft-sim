"""QueueCraft data ingestion and quality assurance.

The importer accepts either event-level data (one row per arrival with a time
column) or pre-aggregated bucket data (timestamp + arrival count). It never
silently repairs invalid records: every exclusion, normalization and missing
bucket is disclosed in the quality report returned to the caller.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd

SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024
MAX_ROWS = 1_000_000
TIMESTAMP_CANDIDATES = ("timestamp", "arrival_time", "datetime", "date_time", "date", "time")
COUNT_CANDIDATES = ("arrivals", "arrival_count", "count", "volume", "jobs", "job_count")


class DataImportError(ValueError):
    """Raised for a file that cannot be safely used for a queue simulation."""


@dataclass(frozen=True)
class ImportOptions:
    timestamp_column: str | None = None
    count_column: str | None = None
    frequency: str = "h"
    max_file_size_bytes: int = MAX_FILE_SIZE_BYTES
    max_rows: int = MAX_ROWS


@dataclass(frozen=True)
class QualityReport:
    source_file: str
    source_format: str
    input_rows: int
    accepted_rows: int
    excluded_rows: int
    excluded_missing_timestamp: int
    excluded_invalid_timestamp: int
    excluded_invalid_count: int
    excluded_negative_count: int
    duplicate_timestamp_rows: int
    inferred_timestamp_column: str
    inferred_count_column: str | None
    generated_event_counts: bool
    frequency: str
    missing_buckets_filled: int
    date_range_start: str
    date_range_end: str
    quality_score_pct: float
    warnings: list[str]


@dataclass(frozen=True)
class ImportedArrivalData:
    historical_counts: list[float]
    bucket_starts: list[str]
    quality: QualityReport
    preview: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "historical_counts": self.historical_counts,
            "bucket_starts": self.bucket_starts,
            "quality": asdict(self.quality),
            "preview": self.preview,
        }


def _normalize_column_name(name: object) -> str:
    return str(name).strip().lower().replace(" ", "_").replace("-", "_")


def _read_source(path: Path, options: ImportOptions) -> pd.DataFrame:
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise DataImportError("only CSV, XLSX and XLS files are supported")
    if not path.exists() or not path.is_file():
        raise DataImportError("selected data file does not exist")
    if path.stat().st_size > options.max_file_size_bytes:
        raise DataImportError(
            f"file exceeds the configured {options.max_file_size_bytes // (1024 * 1024)} MB size limit"
        )

    try:
        if path.suffix.lower() == ".csv":
            try:
                frame = pd.read_csv(path, encoding="utf-8-sig", nrows=options.max_rows + 1)
            except UnicodeDecodeError:
                frame = pd.read_csv(path, encoding="utf-8", nrows=options.max_rows + 1)
        else:
            frame = pd.read_excel(path, nrows=options.max_rows + 1)
    except (OSError, UnicodeError, ValueError, ImportError) as error:
        raise DataImportError(f"unable to read data file: {error}") from error

    if len(frame) > options.max_rows:
        raise DataImportError(f"file exceeds the configured {options.max_rows:,} row limit")
    if frame.empty:
        raise DataImportError("data file contains no rows")
    return frame


def _canonicalize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = [_normalize_column_name(column) for column in frame.columns]
    if len(set(normalized)) != len(normalized):
        raise DataImportError("column names become ambiguous after normalization")
    copy = frame.copy()
    copy.columns = normalized
    return copy


def _resolve_column(columns: list[str], requested: str | None, candidates: tuple[str, ...], label: str) -> str | None:
    if requested:
        normalized = _normalize_column_name(requested)
        if normalized not in columns:
            raise DataImportError(f"configured {label} column '{requested}' was not found")
        return normalized
    return next((candidate for candidate in candidates if candidate in columns), None)


def import_arrival_data(path: str | Path, options: ImportOptions | dict[str, Any] | None = None) -> ImportedArrivalData:
    """Import data, report quality issues, and return chronological arrival buckets.

    Event-level files require a timestamp column and are treated as one arrival
    per accepted row. Aggregated files additionally provide a recognized count
    column. Invalid timestamps, non-numeric counts and negative counts are
    excluded from the analysis and recorded in the report.
    """
    active_options = (
        options
        if isinstance(options, ImportOptions)
        else ImportOptions(**(options or {}))
    )
    if not active_options.frequency or not isinstance(active_options.frequency, str):
        raise DataImportError("frequency must be a valid pandas offset alias such as 'h' or 'D'")

    source = Path(path).expanduser().resolve()
    raw = _canonicalize_columns(_read_source(source, active_options))
    columns = list(raw.columns)
    timestamp_column = _resolve_column(columns, active_options.timestamp_column, TIMESTAMP_CANDIDATES, "timestamp")
    if not timestamp_column:
        raise DataImportError(
            "no timestamp column found; use one of timestamp, arrival_time, datetime, date_time, date or time"
        )
    count_column = _resolve_column(columns, active_options.count_column, COUNT_CANDIDATES, "count")

    working = pd.DataFrame({"timestamp_raw": raw[timestamp_column]})
    working["timestamp"] = pd.to_datetime(working["timestamp_raw"], errors="coerce")
    missing_timestamp = int(working["timestamp_raw"].isna().sum())
    invalid_timestamp = int((working["timestamp_raw"].notna() & working["timestamp"].isna()).sum())

    generated_event_counts = count_column is None
    if generated_event_counts:
        working["count"] = 1.0
        invalid_count = 0
        negative_count = 0
    else:
        numeric_count = pd.to_numeric(raw[count_column], errors="coerce")
        invalid_count = int((raw[count_column].notna() & numeric_count.isna()).sum())
        negative_count = int((numeric_count < 0).fillna(False).sum())
        working["count"] = numeric_count

    valid = working[working["timestamp"].notna() & working["count"].notna() & (working["count"] >= 0)].copy()
    if valid.empty:
        raise DataImportError("no valid arrival records remain after quality validation")

    duplicate_timestamp_rows = int(valid.duplicated(subset=["timestamp"], keep=False).sum())
    try:
        valid["bucket_start"] = valid["timestamp"].dt.floor(active_options.frequency)
    except ValueError as error:
        raise DataImportError(f"invalid aggregation frequency '{active_options.frequency}': {error}") from error
    grouped = valid.groupby("bucket_start", sort=True)["count"].sum()
    complete_index = pd.date_range(grouped.index.min(), grouped.index.max(), freq=active_options.frequency)
    buckets = grouped.reindex(complete_index, fill_value=0.0)
    missing_buckets = int(len(buckets) - len(grouped))

    input_rows = int(len(raw))
    accepted_rows = int(len(valid))
    excluded_rows = input_rows - accepted_rows
    warnings: list[str] = []
    if excluded_rows:
        warnings.append(f"{excluded_rows} row(s) were excluded; see quality counters for the reason.")
    if missing_buckets:
        warnings.append(f"{missing_buckets} missing time bucket(s) were added with zero arrivals.")
    if duplicate_timestamp_rows:
        warnings.append("Duplicate timestamps were retained and aggregated; they may represent simultaneous arrivals.")
    if generated_event_counts:
        warnings.append("No arrival-count column was detected; every accepted row was treated as one arrival event.")

    quality_score = round(100.0 * accepted_rows / input_rows, 2) if input_rows else 0.0
    report = QualityReport(
        source_file=source.name,
        source_format=source.suffix.lower().lstrip("."),
        input_rows=input_rows,
        accepted_rows=accepted_rows,
        excluded_rows=excluded_rows,
        excluded_missing_timestamp=missing_timestamp,
        excluded_invalid_timestamp=invalid_timestamp,
        excluded_invalid_count=invalid_count,
        excluded_negative_count=negative_count,
        duplicate_timestamp_rows=duplicate_timestamp_rows,
        inferred_timestamp_column=timestamp_column,
        inferred_count_column=count_column,
        generated_event_counts=generated_event_counts,
        frequency=active_options.frequency,
        missing_buckets_filled=missing_buckets,
        date_range_start=buckets.index.min().isoformat(),
        date_range_end=buckets.index.max().isoformat(),
        quality_score_pct=quality_score,
        warnings=warnings,
    )
    preview = [
        {"bucket_start": index.isoformat(), "arrivals": float(value)}
        for index, value in buckets.head(12).items()
    ]
    return ImportedArrivalData(
        historical_counts=[float(value) for value in buckets.tolist()],
        bucket_starts=[index.isoformat() for index in buckets.index],
        quality=report,
        preview=preview,
    )
