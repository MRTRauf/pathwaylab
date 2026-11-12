"""Independent event-data lane; no GPS joins."""

import argparse
from pathlib import Path

from pathwaylab.event_source import discover, download

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["discover", "download", "analyze"])
    args = parser.parse_args()
    if args.action == "discover":
        print(discover())
    elif args.action == "download":
        download()
    else:
        from pathwaylab.events import run_events

        run_events(report_dir=Path("research"))
