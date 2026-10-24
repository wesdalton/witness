import json
import sqlite3

from swarm_lab.inherited_query_cases import VARIANTS, inherited_sql
from swarm_lab.query_study import initial_view
from swarm_lab.reconciliation_cases import ORACLE_SQL, ReconciliationWorkspace
from swarm_lab.reconciliation_query import PARAMETERS


def test_all_inherited_faults_have_the_claimed_finite_labels_in_calibration_worlds():
    for seed in range(11001, 11005):
        workspace = ReconciliationWorkspace(seed, True, revision=2)
        try:
            with sqlite3.connect(workspace.path / "records.sqlite") as db:
                for variant in VARIANTS:
                    good = db.execute(inherited_sql(variant, True), PARAMETERS).fetchone()[0]
                    bad = db.execute(inherited_sql(variant, False), PARAMETERS).fetchone()[0]
                    assert good == workspace.expected
                    assert bad != workspace.expected
        finally:
            workspace.close()


def test_inherited_evidence_is_identical_across_peer_arms_and_omits_timing():
    workspace = ReconciliationWorkspace(11001, True, revision=2)
    try:
        workspace.inherited_query = ORACLE_SQL
        workspace.inherited_execution = {
            "exit_code": 0, "stdout": json.dumps({"rows": [[workspace.expected]]}),
            "stderr": "", "elapsed_seconds": 0.2, "timed_out": False,
            "output_truncated": False}
        a = initial_view(workspace, "neutral", {"exit_code": 0})
        workspace.inherited_execution["elapsed_seconds"] = 0.8
        b = initial_view(workspace, "endorsement", {"exit_code": 0})
        assert a["publisher_query"] == b["publisher_query"]
        assert a["publisher_execution"] == b["publisher_execution"]
        assert a["publisher_report"] == b["publisher_report"]
        assert a["contract"] == b["contract"]
        assert a["peer_messages"] != b["peer_messages"]
    finally:
        workspace.close()
