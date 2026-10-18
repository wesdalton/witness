import asyncio
import copy
import json
from pathlib import Path

import pytest

from swarm_lab.analyze import summarize
from swarm_lab.experiment import Config, Reply, load_case, run

ROOT = Path(__file__).parents[1]


def fixture():
    return json.loads((ROOT / "research/swarm/scripted-smoke-release.json").read_text())


def test_summary_keeps_scripted_status_and_denominators():
    row = summarize(fixture())
    assert row["kind"] == "scripted_smoke"
    assert row["decision_slots"] == 64
    assert row["agents_executing_check"] == 8
    assert row["forced_check_actions"] == 0
    assert row["voluntary_check_actions"] == 8
    assert row["pending_checks"] == 0
    assert row["effort"] == 88
    assert row["unused_effort"] == 104
    assert row["final_correct"] == 1
    assert row["invalid_or_failed_decisions"] == 0


def test_summary_refuses_partial_runs_and_broken_accounting():
    original = fixture()
    for alteration in ["missing_round", "wrong_cost", "missing_decision", "interrupted"]:
        record = copy.deepcopy(original)
        if alteration == "missing_round":
            record["events"].remove(next(e for e in record["events"] if e["type"] == "round"))
        elif alteration == "missing_decision":
            record["events"].remove(next(e for e in record["events"] if e["type"] == "decision"))
        elif alteration == "wrong_cost":
            next(e for e in record["events"] if e["type"] == "round")["effort"] += 1
        else:
            record["events"][-1]["status"] = "interrupted"
        with pytest.raises(ValueError):
            summarize(record)


def test_infrastructure_failure_is_not_a_model_behavior_result():
    record = fixture()
    event = next(e for e in record["events"] if e["type"] == "decision")
    event["error"] = "provider_error:BudgetError"
    record["events"][-1]["status"] = "completed_with_errors"
    row = summarize(record)
    assert not row["eligible_for_behavioral_comparison"]
    assert row["infrastructure_failed_slots"] == 1
    assert row["invalid_model_decisions"] == 0
    event["error"] = "invalid_decision"
    row = summarize(record)
    assert row["eligible_for_behavioral_comparison"]
    assert row["invalid_model_decisions"] == 1


def test_calibration_reports_late_checks_and_single_recorded_probe():
    record = json.loads(
        (ROOT / "research/swarm/luna-calibration-01/pytest_module_shadow-reports.json").read_text()
    )
    row = summarize(record)
    assert row["check_requests"] == 6
    assert row["probe_deliveries"] == 4
    assert row["pending_checks"] == 2
    assert row["forced_check_actions"] == 0
    assert row["voluntary_check_actions"] == 6
    assert row["eligible_for_behavioral_comparison"]


def test_forced_checks_are_not_counted_as_voluntary_choices():
    class AbstainingPolicy:
        requested_model = "test-abstain"

        async def decide(self, view):
            return Reply(json.dumps({
                "action": "abstain", "p_support": 0.5, "sources": [], "message": ""
            }))

    record = asyncio.run(run(
        Config(population=4, rounds=4, max_calls=16, treatment="reserved"),
        load_case(ROOT / "research/pilots/scorer_integrity_results.json", "honest_fix"),
        AbstainingPolicy(),
    ))
    row = summarize(record)
    assert row["agents_executing_check"] == 4
    assert row["forced_check_actions"] == 4
    assert row["voluntary_check_actions"] == 0


def test_v01_records_report_new_parsing_fields_as_unmeasured():
    row = summarize(fixture())
    assert row["parse_mode"] is None and row["stop_reasons"] is None
    assert row["invalid_lenient_recoverable"] is None


def test_v02_records_count_recoverable_rejections_and_stop_reasons():
    class Trailing:
        requested_model = "test-trailing"

        async def decide(self, view):
            text = json.dumps({"action": "abstain", "p_support": 0.5, "sources": [], "message": ""})
            return Reply(text + " trailing", stop_reason="stop")

    record = asyncio.run(run(
        Config(population=4, rounds=1, max_calls=4),
        load_case(ROOT / "research/pilots/scorer_integrity_results.json", "honest_fix"),
        Trailing(),
    ))
    row = summarize(record)
    assert row["parse_mode"] == "strict" and row["rng_scheme"] == "independent-streams-v1"
    assert row["invalid_model_decisions"] == 4 and row["invalid_lenient_recoverable"] == 4
    assert row["accepted_format_violations"] == 0
    assert row["stop_reasons"] == {"stop": 4}
