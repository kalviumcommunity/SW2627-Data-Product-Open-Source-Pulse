"""Launch the Streamlit dashboard.

Resolves the app path relative to this file, so the dashboard starts from any
working directory:

    python scripts/run_dashboard.py
"""

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP = PROJECT_ROOT / "src" / "dashboard" / "app.py"


def main():
    """Start Streamlit on the dashboard entry point."""
    if not APP.exists():
        raise SystemExit(f"Dashboard entry point not found: {APP}")

    command = [sys.executable, "-m", "streamlit", "run", str(APP)]
    print(f"Launching: {' '.join(command)}")
    raise SystemExit(subprocess.call(command, cwd=PROJECT_ROOT))


if __name__ == "__main__":
    main()
