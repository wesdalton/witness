"""Free mutation audit of the authored reconciliation generator, not an LLM run."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from swarm_lab.legacy.reconciliation_cases import (  # noqa: E402
    AS_OF,
    END,
    ORACLE_SQL,
    SCHEMA,
    START,
    generate,
)


def alternatives():
    substitutions = {
        "ignore_movement_as_of": ("FROM movements WHERE recorded_at <= :as_of",
                                 "FROM movements"),
        "ignore_status_as_of": ("FROM order_status WHERE recorded_at <= :as_of",
                               "FROM order_status"),
        "filter_time_before_latest": (
            "FROM movements WHERE recorded_at <= :as_of",
            "FROM movements WHERE recorded_at <= :as_of "
            "AND effective_at >= :start AND effective_at < :end"),
        "filter_void_before_latest": (
            "FROM movements WHERE recorded_at <= :as_of",
            "FROM movements WHERE recorded_at <= :as_of AND state = 'posted'"),
        "count_every_movement_revision": ("m.rank = 1 AND ", ""),
        "count_every_status_revision": ("AND s.rank = 1", ""),
        "returns_count_positive": (
            "CASE WHEN m.kind = 'shipment' THEN m.quantity ELSE -m.quantity END",
            "m.quantity"),
        "ignore_movement_state": ("AND m.state = 'posted'", ""),
        "ignore_order_state": ("AND s.state = 'active'", ""),
        "ignore_warehouse": ("o.warehouse = 'north' AND ", ""),
        "exclude_start_boundary": ("m.effective_at >= :start", "m.effective_at > :start"),
        "include_end_boundary": ("m.effective_at < :end", "m.effective_at <= :end"),
        "exclude_as_of_boundary": ("recorded_at <= :as_of", "recorded_at < :as_of"),
        "latest_by_recorded_time": ("ORDER BY revision DESC", "ORDER BY recorded_at DESC"),
        "include_missing_status": (
            "JOIN latest_status s ON s.order_id = o.order_id AND s.rank = 1",
            "LEFT JOIN latest_status s ON s.order_id = o.order_id AND s.rank = 1"),
    }
    queries = {name: ORACLE_SQL.replace(before, after)
               for name, (before, after) in substitutions.items()}
    queries["include_missing_status"] = queries["include_missing_status"].replace(
        "s.state = 'active'", "(s.state = 'active' OR s.state IS NULL)")
    return queries


def audit(seeds, revision=1):
    import sqlite3

    queries = alternatives()
    results = {name: {"distinguished": 0, "worlds": 0, "examples": []} for name in queries}
    for seed in seeds:
        for truth in (True, False):
            orders, statuses, movements, _, expected = generate(seed, truth, revision)
            with sqlite3.connect(":memory:") as db:
                db.executescript(SCHEMA)
                db.executemany("INSERT INTO orders VALUES (?,?)", orders)
                db.executemany("INSERT INTO order_status VALUES (?,?,?,?)", statuses)
                db.executemany("INSERT INTO movements VALUES (?,?,?,?,?,?,?,?)", movements)
                params = {"as_of": AS_OF, "start": START, "end": END}
                assert db.execute(ORACLE_SQL, params).fetchone()[0] == expected
                for name, query in queries.items():
                    actual = db.execute(query, params).fetchone()[0]
                    row = results[name]
                    row["worlds"] += 1
                    if actual != expected:
                        row["distinguished"] += 1
                        if len(row["examples"]) < 2:
                            row["examples"].append({"seed": seed, "truth": truth,
                                                    "expected": expected, "actual": actual})
    return {"schema": "witness.reconciliation-reference-mutations.v1",
            "generator_revision": revision,
            "results": results,
            "interpretation": "Authored incorrect SQL implementations, not learned "
            "agent programs. Distinguishing these does not prove exhaustive coverage."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--revision", type=int, choices=[1, 2], default=1)
    args = parser.parse_args()
    result = audit(args.seeds, args.revision)
    with args.out.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps({k: [v["distinguished"], v["worlds"]]
                      for k, v in result["results"].items()}))


if __name__ == "__main__":
    main()
