"""Bounded official StatsBomb discovery/download, pinned to one cached upstream commit."""

import concurrent.futures
import hashlib
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RAW = Path("data/raw/statsbomb")


def fetch(path: str, sha: str, root: Path = RAW) -> object:
    """Cache original bytes; parse JSON before atomic write; retry public requests only."""
    target = root / path
    if target.exists():
        content = target.read_bytes()
    else:
        url = f"https://raw.githubusercontent.com/hudl/open-data/{sha}/" + urllib.parse.quote(path)
        for attempt in range(3):
            try:
                request = urllib.request.Request(url, headers={"User-Agent": "PathwayLab-research"})
                with urllib.request.urlopen(request, timeout=60) as response:
                    content = response.read()
                if not content:
                    raise ValueError("Empty download")
                if path.endswith(".json"):
                    json.loads(content)
                target.parent.mkdir(parents=True, exist_ok=True)
                temporary = target.with_suffix(target.suffix + ".part")
                temporary.write_bytes(content)
                temporary.replace(target)
                break
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(attempt + 1)
    return json.loads(content) if path.endswith(".json") else content


def discover(root: Path = RAW) -> dict:
    """Inspect both candidate competitions before deciding which match files to fetch."""
    root.mkdir(parents=True, exist_ok=True)
    pin = root / "upstream.json"
    if not pin.exists():
        request = urllib.request.Request(
            "https://api.github.com/repos/hudl/open-data/commits/master",
            headers={"User-Agent": "PathwayLab-research"},
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            sha = json.load(response)["sha"]
        pin.write_text(json.dumps({"sha": sha}))
    sha = json.loads(pin.read_text())["sha"]
    for documentation in [
        "README.md",
        "LICENSE.pdf",
        "doc/Open Data Matches v3.0.0.pdf",
        "doc/Open Data Lineups v2.0.0.pdf",
        "doc/Open Data Events v4.0.0.pdf",
    ]:
        fetch(documentation, sha, root)
    competitions = fetch("data/competitions.json", sha, root)
    if not isinstance(competitions, list) or not all(
        "season_id" in c and "competition_id" in c for c in competitions
    ):
        raise ValueError("Invalid competition metadata")
    coverage = []
    candidates = [
        c for c in competitions if c["competition_name"] in ["FA Women's Super League", "La Liga"]
    ]
    # All WSL seasons, and two most recent La Liga seasons, bound metadata discovery.
    alternatives = sorted(
        [c for c in candidates if c["competition_name"] == "La Liga"],
        key=lambda c: c["season_name"],
        reverse=True,
    )[:2]
    for c in [x for x in candidates if x["competition_name"] != "La Liga"] + alternatives:
        matches = fetch(f"data/matches/{c['competition_id']}/{c['season_id']}.json", sha, root)
        teams = {m[side][f"{side}_id"] for m in matches for side in ["home_team", "away_team"]}
        coverage.append(
            {
                **c,
                "matches": len(matches),
                "teams": len(teams),
                "start": min(m["match_date"] for m in matches),
                "end": max(m["match_date"] for m in matches),
            }
        )
    result = {"sha": sha, "coverage": coverage}
    (root / "discovery.json").write_text(json.dumps(result, indent=2))
    return result


def download(root: Path = RAW) -> dict:
    """Select all available Arsenal fixtures in two earliest adjacent WSL seasons."""
    discovery = discover(root)
    sha = discovery["sha"]
    seasons = sorted(
        [c for c in discovery["coverage"] if c["competition_name"] == "FA Women's Super League"],
        key=lambda c: c["season_name"],
    )[:2]
    selected = []
    for c in seasons:
        matches = fetch(f"data/matches/{c['competition_id']}/{c['season_id']}.json", sha, root)
        for m in matches:
            if any("Arsenal" in m[s][f"{s}_name"] for s in ["home_team", "away_team"]):
                selected.append(
                    {
                        "competition_id": c["competition_id"],
                        "season_id": c["season_id"],
                        "season_name": c["season_name"],
                        "match": m,
                    }
                )
    plan = {
        "sha": sha,
        "cohort": "All metadata-available Arsenal fixtures in the two earliest WSL seasons",
        "discovery": discovery["coverage"],
        "selected": selected,
    }
    (root / "selection.json").write_text(json.dumps(plan, indent=2))
    jobs = [
        f"data/{kind}/{r['match']['match_id']}.json"
        for r in selected
        for kind in ["events", "lineups"]
    ]
    rows = []

    def worker(path):
        try:
            obj = fetch(path, sha, root)
            if not isinstance(obj, list) or not obj:
                raise ValueError("Expected nonempty JSON list")
            return {
                "path": path,
                "status": "ok",
                "sha256": hashlib.sha256((root / path).read_bytes()).hexdigest(),
            }
        except Exception as error:
            return {"path": path, "status": "failed", "error": str(error)}

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(worker, jobs))
    for row in rows:
        row.update(
            url=f"https://raw.githubusercontent.com/hudl/open-data/{sha}/{row['path']}",
            retrieved=datetime.now(timezone.utc).isoformat(),
            upstream_sha=sha,
            match_id=int(Path(row["path"]).stem),
        )
    plan["files"] = rows
    plan["metadata_hashes"] = {
        str(p.relative_to(root)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in root.rglob("*")
        if p.is_file()
        and (
            p.suffix == ".pdf"
            or p.name in ["README.md", "competitions.json"]
            or "matches" in p.parts
        )
    }
    (root / "source_manifest.json").write_text(json.dumps(plan, indent=2))
    print(
        f"StatsBomb {sha}: {len(selected)} matches; "
        f"{sum(r['status'] == 'ok' for r in rows)}/{len(rows)} files OK"
    )
    return plan
