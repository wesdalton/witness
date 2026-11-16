"""Index, check, pack or restore immutable experiment bundles."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from witness.core.archive import Archive  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("audit", help="Verify every sealed bundle, including packed files")
    sub.add_parser("index", help="Regenerate the derived experiment index, then audit")
    pack = sub.add_parser("pack", help="Move sealed folders into the content-addressed store")
    pack.add_argument("--id", required=True)
    pack.add_argument("folders", nargs="+")
    restore = sub.add_parser("restore", help="Rebuild packed files; never overwrites")
    restore.add_argument("--prefix", default="research/")
    restore.add_argument("--to", type=Path, help="Destination root (default: repository)")
    args = parser.parse_args()
    archive = Archive(ROOT)
    if args.action == "pack":
        record = archive.pack(args.id, args.folders)
        result = {**archive.audit(), "packed_now": len(record["files"])}
    elif args.action == "restore":
        restored = archive.restore(args.prefix, args.to)
        print(json.dumps({"restored": len(restored)}, indent=2))
        return 0
    else:
        if args.action == "index":
            archive.build_index()
        result = archive.audit()
    print(json.dumps(result, indent=2))
    return bool(result["errors"])


if __name__ == "__main__":
    raise SystemExit(main())
