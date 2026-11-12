"""Retrieve original public research files directly from Zenodo with integrity checks.

The source record currently has no explicit license text in its public Rights section;
do not redistribute these files until reuse rights are independently confirmed.
"""

import argparse
import hashlib
import urllib.request
from pathlib import Path

RECORD = "https://zenodo.org/records/18986229"
FILES = {
    "DataSetTMr.csv": "864bfbc3f78a736f60bba764de8d4f4d",
    "DataDictionary.xlsx": "10959d59ba0ad221a0b783d618d27d53",
}
DEST = Path("data/raw")


def verify(path: Path, expected: str):
    got = hashlib.md5(
        path.read_bytes()
    ).hexdigest()  # Integrity against Zenodo's published MD5, not security signature
    if got != expected:
        raise SystemExit(
            f"Checksum mismatch for {path}: expected {expected}, got {got}. Verify record {RECORD}."
        )
    print(f"CHECKSUM OK: {path} (md5 {got})")


def download(name: str, expected: str):
    target = DEST / name
    url = f"{RECORD}/files/{name}?download=1"
    request = urllib.request.Request(
        url, headers={"User-Agent": "PathwayLabResearch/0.2 (academic research; public data)"}
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as res:
            content = res.read()
    except Exception as e:
        raise SystemExit(
            f"Unable to download {name} from Zenodo ({e}). Save original file manually at {target}."
        ) from e
    got = hashlib.md5(content).hexdigest()
    if got != expected:
        raise SystemExit(f"Checksum mismatch for download {name}: {got} != {expected}")
    target.write_bytes(content)
    print(f"Downloaded {target} ({len(content):,} bytes); matches original Zenodo MD5")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--with-dictionary", action="store_true", help="Download original XLSX data dictionary too"
    )
    ap.add_argument(
        "--verify-only", action="store_true", help="Verify local files without network access"
    )
    args = ap.parse_args()
    DEST.mkdir(parents=True, exist_ok=True)
    names = list(FILES) if args.with_dictionary else ["DataSetTMr.csv"]
    for name in names:
        if args.verify_only:
            path = DEST / name
            if not path.exists():
                raise SystemExit(f"Missing {path}; download first from {RECORD}")
            verify(path, FILES[name])
        else:
            download(name, FILES[name])
    print("Source:", RECORD)
    print("Review original dictionary and rights before research/public redistribution.")


if __name__ == "__main__":
    main()
