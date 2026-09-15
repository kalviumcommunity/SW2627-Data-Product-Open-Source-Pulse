"""Run the contributor retention pipeline."""

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

from src.data_pipeline.pipeline import run_pipeline


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("--raw-dir", default="data/raw")
	parser.add_argument("--output-dir", default="output")
	args = parser.parse_args()
	journey = run_pipeline(args.raw_dir, args.output_dir)
	print(f"Wrote contributor journey for {len(journey)} first-time contributors")


if __name__ == "__main__":
	main()
