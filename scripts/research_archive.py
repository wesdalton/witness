"""Index or check immutable experiment bundles; bootstrap preserves all legacy paths."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from swarm_lab.research_archive import Archive, bootstrap_legacy  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["bootstrap", "audit", "index"])
    args = parser.parse_args()
    archive = Archive(ROOT)
    if args.action == "bootstrap":
        result = bootstrap_legacy(ROOT)
    else:
        if args.action == "index":
            archive.build_index()
        result = archive.audit()
    print(json.dumps(result, indent=2))
    return bool(result["errors"])


if __name__ == "__main__":
    raise SystemExit(main())
