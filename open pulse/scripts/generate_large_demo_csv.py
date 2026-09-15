"""Generate a large contributor journey CSV for dashboard testing."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.analytics.demo_data import build_demo_data


def main():
    destination = PROJECT_ROOT / "data" / "raw" / "contributor_journey_large.csv"
    destination.parent.mkdir(parents=True, exist_ok=True)
    build_demo_data(1000)["journey"].to_csv(destination, index=False)
    print(f"Generated {destination}")


if __name__ == "__main__":
    main()