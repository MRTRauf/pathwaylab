"""Run Phase 03 only, from the installed PathwayLab project."""

import argparse
from pathlib import Path

from pathwaylab.inference import run_inference

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=Path("data/raw/DataSetTMr.csv"))
    parser.add_argument("--out", type=Path, default=Path("outputs/inference"))
    parser.add_argument("--report", type=Path, default=Path("research/LONGITUDINAL_FINDINGS.md"))
    args = parser.parse_args()
    run_inference(args.raw, args.out, args.report)
