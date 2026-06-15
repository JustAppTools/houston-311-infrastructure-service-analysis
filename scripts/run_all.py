import argparse
import subprocess
import sys
from pathlib import Path

from project_config import DEFAULT_END_DATE, DEFAULT_MAX_RECORDS, DEFAULT_START_DATE, ensure_directories


SCRIPT_DIR = Path(__file__).resolve().parent


def run(script: str, *args: str) -> None:
    cmd = [sys.executable, str(SCRIPT_DIR / script), *args]
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Houston 311 V3 pipeline.")
    parser.add_argument("--start-date", default=DEFAULT_START_DATE)
    parser.add_argument("--end-date", default=DEFAULT_END_DATE)
    parser.add_argument("--max-records", type=int, default=DEFAULT_MAX_RECORDS)
    parser.add_argument("--skip-fetch", action="store_true", help="Reuse data/raw extract if already present.")
    parser.add_argument("--skip-context", action="store_true", help="Reuse existing boundary and demographic context files.")
    args = parser.parse_args()

    ensure_directories()
    if not args.skip_fetch:
        run(
            "fetch_data.py",
            "--start-date",
            args.start_date,
            "--end-date",
            args.end_date,
            "--max-records",
            str(args.max_records),
        )
    if not args.skip_context:
        run("fetch_boundaries.py")
        run("fetch_context.py")
        run("fetch_demographics.py")
    run("clean_311_requests.py")
    run("analyze_requests.py")
    run("export_gis_layers.py")
    run("make_maps.py")
    run("make_deliverables.py")
    print("Pipeline complete.")


if __name__ == "__main__":
    main()
