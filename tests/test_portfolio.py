"""Offline validity gates for the portfolio experiment; no inference requests."""

import copy
import json
from decimal import Decimal

import pytest

from swarm_lab.agent_budget import PhaseBudget
from swarm_lab.pilot import BudgetError
from swarm_lab.portfolio import (
    ARMS,
    TOOLS,
    main,
    make_portfolio,
    run_episode,
    score,
    validate_calls,
    validate_submission,
    view,
)
from swarm_lab.portfolio_cases import FAMILIES, TARGET_PATHS, CaseWorkspace
from swarm_lab.portfolio_v2_cases import ContractWorkspace
from swarm_lab.research_client import ResponsesClient


def call(cid, command="ls", call_id="call-1"):
    return {"id": call_id, "function": {"name": "inspect_case", "arguments": json.dumps(
        {"claim_id": cid, "command": command})}}


def setup():
    portfolio = make_portfolio(1001)
    evidence = {c["id"]: {f"report:{c['id']}"} for c in portfolio["cases"]}
    return portfolio, set(evidence), evidence


def submission(portfolio):
    return {"assessments": [
        {"claim_id": c["id"], "verdict": "supported" if c["truth"] else "refuted",
         "p_support": int(c["truth"]), "evidence_ids": [f"report:{c['id']}"],
         "justification": "Test assessment."} for c in portfolio["cases"]]}


def test_truth_is_absent_from_initial_evidence_and_matched_across_arms():
    portfolio, _, _ = setup()
    changed = copy.deepcopy(portfolio)
    for c in changed["cases"]:
        if c["family"] != "control":
            c["truth"] = not c["truth"]
    for arm in ARMS:
        assert view(changed, arm, 2) == view(portfolio, arm, 2)
        assert view(portfolio, arm, 2)["claims"] == view(portfolio, "no_peers", 2)["claims"]
    assert "target" not in view(portfolio, "no_peers", 2)
    assert make_portfolio(1001) == portfolio
    assert make_portfolio(1002) != portfolio


def test_native_bundles_charge_unique_cases_and_revisits_are_free():
    _, ids, evidence = setup()
    calls = [call("C1"), call("C1", call_id="two"), call("C2", call_id="three")]
    assert len(validate_calls(calls, ids, evidence, set(), 2, 0)) == 3
    assert validate_calls([call("C1")], ids, evidence, {"C1", "C2"}, 2, 3)
    with pytest.raises(ValueError, match="investigation budget"):
        validate_calls([call("C3")], ids, evidence, {"C1", "C2"}, 2, 3)
    with pytest.raises(ValueError, match="Command limit"):
        validate_calls(calls, ids, evidence, set(), 2, 23)
    with pytest.raises(ValueError, match="duplicate"):
        validate_calls([call("C1"), call("C2")], ids, evidence, set(), 2, 0)


def test_invalid_bundle_executes_nothing(tmp_path, monkeypatch):
    class FakeClient:
        def generate(self, messages, final=False):
            calls = [call(f"C{i}", call_id=str(i)) for i in (1, 2, 3)]
            message = {"role": "assistant", "tool_calls": calls}
            return message, {"finish_reason": "tool_calls", "message": message}

    def forbidden(*args):
        raise AssertionError("Invalid bundle must not create a workspace")

    monkeypatch.setattr("swarm_lab.portfolio.CaseWorkspace", forbidden)
    monkeypatch.setattr("swarm_lab.portfolio.ControlWorkspace", forbidden)
    record = run_episode({"id": "unit", "seed": 1001, "budget": 2, "arm": "no_peers"},
                         tmp_path, FakeClient(), "unused")
    assert record["status"] == "invalid_action"
    assert not any(e["type"] == "tool" for e in record["events"])


def test_cross_case_citations_and_missing_assessments_rejected():
    portfolio, ids, evidence = setup()
    answer = submission(portfolio)
    validate_submission(answer, ids, evidence)
    answer["assessments"][0]["evidence_ids"] = ["report:C2"]
    with pytest.raises(ValueError, match="another case"):
        validate_submission(answer, ids, evidence)
    answer = submission(portfolio)
    answer["assessments"].pop()
    with pytest.raises(ValueError, match="Every claim"):
        validate_submission(answer, ids, evidence)


@pytest.mark.parametrize("invalid", [True, float("nan"), float("inf"), -0.01, 1.01])
def test_invalid_probabilities_rejected(invalid):
    portfolio, ids, evidence = setup()
    answer = submission(portfolio)
    answer["assessments"][0]["p_support"] = invalid
    with pytest.raises(ValueError, match="probability"):
        validate_submission(answer, ids, evidence)


def test_brier_baselines_and_incomplete_denominator():
    portfolio, _, _ = setup()
    answer = submission(portfolio)
    assert score(portfolio, answer, set())["brier"] == 0
    assert score(portfolio, None, set()) is None
    for case, assessment in zip(portfolio["cases"], answer["assessments"], strict=True):
        if case["family"] != "control":
            assessment["p_support"] = 0.5
            assessment["verdict"] = "uncertain"
    result = score(portfolio, answer, {portfolio["target"]})
    assert result["brier"] == pytest.approx(5/24)
    assert result["uncertain_verdicts"] == 5
    assert result["correct_verdicts"] == 1
    assert result["target_investigated"]


@pytest.mark.parametrize("family", FAMILIES)
def test_paired_candidates_differ_only_in_the_historical_source_file(family):
    good, bad = CaseWorkspace(family, True), CaseWorkspace(family, False)
    try:
        a, b = good.hashes(), bad.hashes()
        assert a.keys() == b.keys()
        assert [p for p in a if a[p] != b[p]] == [TARGET_PATHS[family]]
        assert not any("reference" in p or ".env" in p or ".git/" in p for p in a)
    finally:
        good.close()
        bad.close()


def test_responses_history_retains_native_items_and_resets_between_episodes(tmp_path):
    client = ResponsesClient("test", "openai/gpt-6.1-sol", PhaseBudget(tmp_path / "ledger"),
                             "test", Decimal(4), Decimal(".0000025"), Decimal(".00001"),
                             tools=TOOLS)
    messages = [{"role": "system", "content": "system"}, {"role": "user", "content": "case"}]
    first = client.payload(messages, False)
    assert first["tools"][0]["name"] == "inspect_case"
    native = [{"type": "reasoning", "id": "opaque", "encrypted_content": "test-only"},
              {"type": "function_call", "call_id": "native1", "name": "inspect_case",
               "arguments": '{"claim_id":"C1","command":"ls"}'}]
    client.history.extend(native)
    messages.extend([{"role": "assistant", "tool_calls": [call("C1")]},
                     {"role": "tool", "tool_call_id": "native1", "content": "result"}])
    second = client.payload(messages, True)
    assert second["input"][2:4] == native
    assert second["input"][-1] == {"type": "function_call_output", "call_id": "native1",
                                   "output": "result"}
    assert second["tool_choice"] == {"type": "function", "name": "submit"}
    assert first["input"] == messages[:2]  # no alias mutated the earlier payload
    assert client.payload(messages[:2], False)["input"] == messages[:2]


def test_invalid_reference_gate_stops_before_any_new_run(tmp_path, monkeypatch):
    output = tmp_path / "must-not-exist"
    monkeypatch.setattr("sys.argv", ["portfolio", "--live", "--out", str(output)])
    with pytest.raises(BudgetError, match="invalid positive labels"):
        main()
    assert not output.exists()


@pytest.mark.parametrize("family", ("multipart", "callbacks"))
def test_v2_preserves_residual_negatives_and_repairs_only_target_source(family):
    original = CaseWorkspace(family, True)
    residual = ContractWorkspace(family, False, variant="residual")
    repaired = ContractWorkspace(family, True)
    try:
        old, bad, good = original.hashes(), residual.hashes(), repaired.hashes()
        path = TARGET_PATHS[family]
        assert old[path] == bad[path]
        assert old[path] != good[path]
        assert [p for p in good if good[p] != bad[p]] == [path]
        compile((repaired.path / path).read_text(), path, "exec")
    finally:
        original.close()
        residual.close()
        repaired.close()


def test_v2_variant_and_truth_are_not_in_initial_view():
    portfolio = make_portfolio(1001, "v2")
    changed = copy.deepcopy(portfolio)
    for case in changed["cases"]:
        if case["family"] != "control":
            case["truth"] = not case["truth"]
            case["variant"] = "residual" if case["variant"] == "historical" else "historical"
    for arm in ARMS:
        assert view(portfolio, arm, 2, "v2") == view(changed, arm, 2, "v2")
    assert "PROMPT" in json.dumps(view(portfolio, "no_peers", 2, "v2"))
    assert portfolio["target"] == make_portfolio(1001)["target"]
