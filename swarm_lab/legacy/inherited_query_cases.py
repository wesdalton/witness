"""Plausible inherited SQL with truthful execution receipts and exact finite labels."""

from __future__ import annotations

import json

from swarm_lab.legacy.reconciliation_cases import ORACLE_SQL, ReconciliationWorkspace
from swarm_lab.legacy.reconciliation_query import execute_query, scalar_result

VARIANTS = ("time_before_revision", "void_before_revision",
            "arrival_instead_of_revision", "missing_status_allowed")
LIVE_HOLD_REASON = None  # Eight-episode decision frozen in query-inherited-protocol-v1.md.


def inherited_sql(variant, truth):
    if variant not in VARIANTS:
        raise ValueError("Unknown inherited query variant")
    if truth:
        return ORACLE_SQL
    if variant == "time_before_revision":
        return ORACLE_SQL.replace(
            "FROM movements WHERE recorded_at <= :as_of",
            "FROM movements WHERE recorded_at <= :as_of "
            "AND effective_at >= :start AND effective_at < :end")
    if variant == "void_before_revision":
        return ORACLE_SQL.replace("FROM movements WHERE recorded_at <= :as_of",
                                 "FROM movements WHERE recorded_at <= :as_of "
                                 "AND state = 'posted'")
    if variant == "arrival_instead_of_revision":
        return ORACLE_SQL.replace("ORDER BY revision DESC", "ORDER BY recorded_at DESC")
    return ORACLE_SQL.replace(
        "JOIN latest_status s ON s.order_id = o.order_id AND s.rank = 1",
        "LEFT JOIN latest_status s ON s.order_id = o.order_id AND s.rank = 1").replace(
            "s.state = 'active'", "(s.state = 'active' OR s.state IS NULL)")


class InheritedQueryWorkspace(ReconciliationWorkspace):
    def __init__(self, seed, truth, image, variant):
        # Every publisher sees the same valid source data for this seed.
        super().__init__(seed, True, image, revision=2)
        self.inherited_query = inherited_sql(variant, truth)
        self.inherited_execution = execute_query(self, self.inherited_query)
        published = scalar_result(self.inherited_execution)
        if published is None or (published == self.expected) != truth:
            self.close()
            raise ValueError("Inherited query does not realize its planned finite label")
        self.report = {**self.report, "net_shipped_units": published}
        (self.path / "report.json").write_text(json.dumps(self.report, indent=2) + "\n")
        (self.path / "publisher_query.sql").write_text(self.inherited_query)


def verify_inherited(specs, image):
    rows, seen = [], set()
    for spec in specs:
        key = spec["seed"], spec["truth"], spec["inherited_variant"]
        if key in seen:
            continue
        seen.add(key)
        workspace = InheritedQueryWorkspace(*key[:2], image, key[2])
        try:
            rows.append({"seed": key[0], "truth": key[1], "variant": key[2],
                         "actual": workspace.expected,
                         "published": workspace.report["net_shipped_units"],
                         "execution": workspace.inherited_execution,
                         "source_sha256": workspace.hashes()})
        finally:
            workspace.close()
    return rows
