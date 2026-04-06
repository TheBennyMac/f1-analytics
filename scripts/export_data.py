"""
Data export pipeline.

Exports pre-computed DataFrames from notebook state to data/computed/ as
Parquet files. Uses atomic writes (stage to .tmp, then rename) to prevent
partial files from being read by the site layer. Updates manifest.json
after each successful export.

Usage (from a notebook export cell):
    import importlib, sys
    sys.path.insert(0, '..')  # if running from notebooks/
    import scripts.export_data as exp

    exp.export(
        results_2022_2025=results_df,
        results_2026=results_2026_df,
        retirement_by_era=retirement_df,
        overtake_index_by_race=race_oi_df,
        sc_summary_by_race=sc_impact_df,
        pit_excitement_by_race=pit_excitement_df,
        championship_trajectory=gap_df,
    )

Each keyword arg must match a key in SCHEMAS (below). Any DataFrame that
is not provided is skipped — partial exports are allowed (e.g. updating
only results_2026 after a new race).
"""

import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import fastf1
import pandas as pd


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

COMPUTED_DIR = Path(__file__).parent.parent / "data" / "computed"
MANIFEST_PATH = COMPUTED_DIR / "manifest.json"

# Schema: required columns and their expected dtypes (coerced on export).
# Dtype values use pandas dtype strings understood by DataFrame.astype().
SCHEMAS: dict[str, dict[str, str]] = {
    "results_2022_2025": {
        "season": "int64",
        "round": "int64",
        "race_name": "object",
        "driver_id": "object",
        "driver_name": "object",
        "constructor_id": "object",
        "constructor_name": "object",
        "grid_position": "float64",
        "finish_position": "float64",
        "points": "float64",
        "status": "object",
    },
    "results_2026": {
        "season": "int64",
        "round": "int64",
        "race_name": "object",
        "driver_id": "object",
        "driver_name": "object",
        "constructor_id": "object",
        "constructor_name": "object",
        "grid_position": "float64",
        "finish_position": "float64",
        "points": "float64",
        "status": "object",
    },
    "retirement_by_era": {
        "era_year": "int64",
        "races": "int64",
        "mean_starters": "float64",
        "total_first_lap_dnfs": "int64",
        "mean_dnf_rate": "float64",
    },
    "overtake_index_by_race": {
        "season": "int64",
        "round": "int64",
        "race_name": "object",
        "starters": "int64",
        "finishers": "int64",
        "positions_gained": "int64",
        "mean_abs_delta": "float64",
        "overtake_index": "float64",
    },
    "sc_summary_by_race": {
        "season": "int64",
        "round": "int64",
        "race_name": "object",
        "sc_count": "int64",
        "vsc_count": "int64",
        "red_flag_count": "int64",
        "any_intervention": "bool",
        "overtake_index": "float64",
        "positions_gained": "int64",
        "finishers": "int64",
    },
    "pit_excitement_by_race": {
        "season": "int64",
        "round": "int64",
        "split_lap": "float64",
        "pre_positions_gained_per_lap": "float64",
        "post_positions_gained_per_lap": "float64",
        "pre_laps": "int64",
        "post_laps": "int64",
    },
    "championship_trajectory": {
        "season": "int64",
        "round": "int64",
        "constructor_id": "object",
        "constructor_name": "object",
        "round_points": "float64",
        "cumulative_points": "float64",
        "leader_points": "float64",
        "gap_to_leader": "float64",
    },
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _validate(name: str, df: pd.DataFrame) -> None:
    """Raise ValueError if df is missing required columns for this export."""
    schema = SCHEMAS[name]
    missing = set(schema.keys()) - set(df.columns)
    if missing:
        raise ValueError(
            f"[{name}] DataFrame is missing required columns: {sorted(missing)}"
        )


def _coerce_dtypes(name: str, df: pd.DataFrame) -> pd.DataFrame:
    """Cast columns to their declared schema dtypes where possible."""
    schema = SCHEMAS[name]
    df = df.copy()
    for col, dtype in schema.items():
        if col not in df.columns:
            continue
        try:
            if dtype == "bool":
                df[col] = df[col].astype(bool)
            else:
                df[col] = pd.to_numeric(df[col], errors="ignore").astype(dtype)
        except (TypeError, ValueError):
            # Non-fatal: leave as-is; schema check already confirmed presence
            pass
    return df


def _atomic_write(df: pd.DataFrame, dest: Path) -> None:
    """Write df to dest as Parquet using a temp file + rename for atomicity."""
    tmp_fd, tmp_path_str = tempfile.mkstemp(
        suffix=".parquet.tmp", dir=dest.parent
    )
    tmp_path = Path(tmp_path_str)
    try:
        os.close(tmp_fd)
        df.to_parquet(tmp_path, index=False, engine="pyarrow")
        shutil.move(str(tmp_path), str(dest))
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise


def _load_manifest() -> dict:
    """Load existing manifest or return an empty structure."""
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {"exports": {}, "fastf1_version": None, "last_updated": None}


def _save_manifest(manifest: dict) -> None:
    """Write manifest atomically."""
    tmp_fd, tmp_path_str = tempfile.mkstemp(
        suffix=".json.tmp", dir=MANIFEST_PATH.parent
    )
    tmp_path = Path(tmp_path_str)
    try:
        os.close(tmp_fd)
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        shutil.move(str(tmp_path), str(MANIFEST_PATH))
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def export(**dataframes: pd.DataFrame) -> None:
    """Export one or more DataFrames to data/computed/ as Parquet files.

    Args:
        **dataframes: Keyword arguments where the key is the export name
                      (must be a key in SCHEMAS) and the value is the
                      DataFrame to export.

    Raises:
        ValueError: If an unknown export name is provided, or if a DataFrame
                    is missing required columns.

    Side effects:
        - Writes <name>.parquet files to data/computed/ atomically.
        - Updates data/computed/manifest.json with row counts and timestamp.
    """
    unknown = set(dataframes.keys()) - set(SCHEMAS.keys())
    if unknown:
        raise ValueError(
            f"Unknown export name(s): {sorted(unknown)}. "
            f"Valid names: {sorted(SCHEMAS.keys())}"
        )

    COMPUTED_DIR.mkdir(parents=True, exist_ok=True)

    manifest = _load_manifest()
    now_utc = datetime.now(timezone.utc).isoformat()

    try:
        ff1_version = fastf1.__version__
    except AttributeError:
        ff1_version = "unknown"

    exported: list[str] = []
    for name, df in dataframes.items():
        print(f"  Exporting {name} ({len(df):,} rows)...", end=" ")
        _validate(name, df)
        df_out = _coerce_dtypes(name, df)
        dest = COMPUTED_DIR / f"{name}.parquet"
        _atomic_write(df_out, dest)
        manifest["exports"][name] = {
            "rows": len(df_out),
            "columns": list(df_out.columns),
            "exported_at": now_utc,
        }
        exported.append(name)
        print("done.")

    if exported:
        manifest["fastf1_version"] = ff1_version
        manifest["last_updated"] = now_utc
        _save_manifest(manifest)
        print(f"\nmanifest.json updated ({len(exported)} file(s) exported).")


def read(name: str) -> pd.DataFrame:
    """Read a single exported Parquet file from data/computed/.

    Args:
        name: Export name (key in SCHEMAS), without .parquet extension.

    Returns:
        DataFrame read from data/computed/<name>.parquet.

    Raises:
        FileNotFoundError: If the Parquet file does not exist.
        ValueError: If the name is not a recognised export.
    """
    if name not in SCHEMAS:
        raise ValueError(
            f"Unknown export name '{name}'. "
            f"Valid names: {sorted(SCHEMAS.keys())}"
        )
    path = COMPUTED_DIR / f"{name}.parquet"
    if not path.exists():
        raise FileNotFoundError(
            f"Export not found: {path}. Run export({name}=...) first."
        )
    return pd.read_parquet(path, engine="pyarrow")


def manifest_summary() -> None:
    """Print a human-readable summary of the current manifest."""
    if not MANIFEST_PATH.exists():
        print("No manifest found. Run export(...) first.")
        return
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        m = json.load(f)
    print(f"FastF1 version : {m.get('fastf1_version', 'unknown')}")
    print(f"Last updated   : {m.get('last_updated', 'unknown')}")
    print()
    exports = m.get("exports", {})
    if not exports:
        print("No exports recorded.")
        return
    for name, meta in sorted(exports.items()):
        print(
            f"  {name:<35} {meta['rows']:>7,} rows   "
            f"exported {meta['exported_at']}"
        )
