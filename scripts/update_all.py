"""
Post-race rebuild orchestrator.

Runs the full pipeline after a new race is available in FastF1:
  1. Execute notebook 02 (2026 data) headlessly — refreshes results_2026.parquet
  2. Execute notebook 04 (narrative testing) headlessly — refreshes all other parquets
  3. Run `quarto render site/` to regenerate the static site
  4. Stage site/docs/ and data/computed/manifest.json for commit

Usage:
    python scripts/update_all.py --season 2026 --round 4

    --season   Season year (e.g. 2026)
    --round    Round number just completed (e.g. 4)
    --skip-nb  Skip notebook execution (use existing parquet files)
    --skip-render  Skip quarto render (useful for testing notebook step only)

After running:
    1. Inspect site/ visually: quarto preview site/
    2. Commit: git add -A && git commit -m "data: post-race update YYYY R<N>"
    3. Push: git push origin main
    4. Verify live site at GitHub Pages URL
"""

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).parent.parent
NOTEBOOKS_DIR = ROOT / "notebooks"
SITE_DIR = ROOT / "site"
DOCS_DIR = SITE_DIR / "docs"
MANIFEST_PATH = ROOT / "data" / "computed" / "manifest.json"

NOTEBOOK_02 = NOTEBOOKS_DIR / "02_2026_era_year1.ipynb"
NOTEBOOK_04 = NOTEBOOKS_DIR / "04_narrative_testing.ipynb"

PYTHON = sys.executable  # same interpreter that's running this script


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(cmd: list[str], label: str) -> None:
    """Run a subprocess, streaming output. Raises on non-zero exit."""
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    start = time.time()
    result = subprocess.run(cmd, cwd=ROOT)
    elapsed = time.time() - start
    if result.returncode != 0:
        print(f"\n[FAILED] {label} — exit code {result.returncode}")
        sys.exit(result.returncode)
    print(f"\n[OK] {label} completed in {elapsed:.0f}s")


def _execute_notebook(notebook_path: Path) -> None:
    """Execute a notebook in-place via nbconvert, overwriting outputs."""
    _run(
        [
            PYTHON, "-m", "jupyter", "nbconvert",
            "--to", "notebook",
            "--execute",
            "--inplace",
            "--ExecutePreprocessor.timeout=600",
            str(notebook_path),
        ],
        label=f"Execute {notebook_path.name}",
    )


def _quarto_render() -> None:
    """Run quarto render on the site directory."""
    quarto = shutil.which("quarto")
    if quarto is None:
        print("\n[ERROR] quarto not found on PATH.")
        print("  Add C:\\Program Files\\Quarto\\bin to PATH and retry.")
        sys.exit(1)
    _run([quarto, "render"], label="quarto render site/")


def _stage_for_commit(season: int, round_: int) -> None:
    """Stage site/docs/ and manifest.json, print commit instruction."""
    print(f"\n{'='*60}")
    print("  Staging files for commit")
    print(f"{'='*60}")

    # Force-add site/docs/ (gitignored except .gitkeep)
    subprocess.run(
        ["git", "add", "-f", str(DOCS_DIR)],
        cwd=ROOT,
        check=True,
    )
    # Add manifest (always committed)
    if MANIFEST_PATH.exists():
        subprocess.run(
            ["git", "add", str(MANIFEST_PATH)],
            cwd=ROOT,
            check=True,
        )

    # Show what's staged
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    print(result.stdout)

    print("[OK] Files staged.")
    print()
    print("Next steps:")
    print(f'  git commit -m "data: post-race update {season} R{round_}"')
    print("  git push origin main")
    print("  Verify live site at GitHub Pages URL")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Post-race site rebuild pipeline.")
    parser.add_argument("--season", type=int, required=True, help="Season year, e.g. 2026")
    parser.add_argument("--round", dest="round_", type=int, required=True, help="Round number completed")
    parser.add_argument("--skip-nb", action="store_true", help="Skip notebook execution")
    parser.add_argument("--skip-render", action="store_true", help="Skip quarto render")
    args = parser.parse_args()

    print(f"\nF1 Analytics — post-race rebuild")
    print(f"Season {args.season}, Round {args.round_}")
    print(f"Python: {PYTHON}")
    print(f"Root:   {ROOT}")

    start_total = time.time()

    if not args.skip_nb:
        _execute_notebook(NOTEBOOK_02)
        _execute_notebook(NOTEBOOK_04)
    else:
        print("\n[SKIP] Notebook execution skipped (--skip-nb)")

    if not args.skip_render:
        _quarto_render()
    else:
        print("\n[SKIP] Quarto render skipped (--skip-render)")

    _stage_for_commit(args.season, args.round_)

    total = time.time() - start_total
    print(f"\nTotal time: {total:.0f}s")


if __name__ == "__main__":
    main()
