"""Meaningful environment invariants; no provider keys or network calls."""

import asyncio
import json
from pathlib import Path

import pytest

from swarm_lab.experiment import (
    Case,
    Config,
    InspectPolicy,
    Reply,
    ScriptedPolicy,
    load_case,
    parse_decision,
    run,
    visible_evidence,
)

FIXTURES = Path(__file__).parents[1] / "research/pilots/scorer_integrity_results.json"


def test_matched_reports_do_not_reveal_truth():
    honest = load_case(FIXTURES, "honest_fix")
    shadow = load_case(FIXTURES, "pytest_module_shadow")
    assert honest.report == shadow.report
    assert honest.truth and not shadow.truth
    assert honest.probe != shadow.probe


def test_call_ceiling_rejected_before_execution():
    with pytest.raises(ValueError, match="max-calls"):
        Config(population=16, rounds=10, max_calls=159)


@pytest.mark.parametrize("truth", [True, False])
def test_scripted_smoke_checks_arrive_after_delay_and_budgets_balance(truth):
    fixture = "honest_fix" if truth else "pytest_module_shadow"
    result = asyncio.run(run(Config(), load_case(FIXTURES, fixture), ScriptedPolicy()))
    rounds = [e for e in result["events"] if e["type"] == "round"]
    assert rounds[0]["probe_deliveries"] == rounds[1]["probe_deliveries"] == 0
    assert rounds[2]["probe_deliveries"] == 8
    for event in rounds:
        assert event["effort"] == event["check_requests"] * 4 + event["messages"]
    assert rounds[-1]["wrong"] == 0 and rounds[-1]["uncertain"] == 0
    assert all(a["budget"] >= 0 for a in result["final_agents"])
    assert result["kind"] == "scripted_smoke"


def test_invalid_citations_and_nonfinite_confidence_rejected():
    view = {"evidence": [], "budget": 24, "pending": False}
    base = {"action": "relay", "p_support": 0.8, "sources": [], "message": "Claim"}
    for update in [
        {"sources": ["invented"]},
        {"p_support": float("nan")},
        {"p_support": True},
        {"action": "execute_shell"},
        {"action": []},
        {"sources": [[]]},
    ]:
        with pytest.raises(ValueError):
            parse_decision(json.dumps(base | update), view)


def test_truth_and_fixture_identity_never_enter_model_views():
    class Observer:
        async def decide(self, view):
            serialized = json.dumps(view)
            assert "SECRET" not in serialized
            assert "truth" not in view
            assert "root_ids" not in serialized
            return Reply(
                json.dumps({"action": "abstain", "p_support": 0.5, "sources": [], "message": ""})
            )

    case = Case("SECRET_CASE", "A claim", "A report", "SECRET_PROBE", False, "hash")
    result = asyncio.run(run(Config(), case, Observer()))
    assert all(e["error"] is None for e in result["events"] if e["type"] == "decision")


def test_invalid_policy_fails_closed_and_preserves_raw_output():
    class Invalid:
        async def decide(self, view):
            return Reply("this is not JSON")

    result = asyncio.run(run(Config(rounds=1), load_case(FIXTURES, "honest_fix"), Invalid()))
    decisions = [e for e in result["events"] if e["type"] == "decision"]
    assert all(e["error"] == "invalid_decision" for e in decisions)
    assert all(e["executed_action"] == "abstain" for e in decisions)
    assert all(e["raw_output"] == "this is not JSON" for e in decisions)
    assert result["events"][-1]["final_metrics"]["effort"] == 0
    assert result["status"] == "completed_with_errors"


def test_no_same_round_messages_leak_into_views():
    class Relay:
        async def decide(self, view):
            for item in view["evidence"]:
                if item["kind"] == "peer":
                    assert int(item["id"].split(":")[1]) < view["round"]
            return Reply(
                json.dumps(
                    {"action": "relay", "p_support": 0.5, "sources": [], "message": "Assessment"}
                )
            )

    result = asyncio.run(run(Config(), load_case(FIXTURES, "honest_fix"), Relay()))
    assert all(e["error"] is None for e in result["events"] if e["type"] == "decision")


def test_reserved_policy_charges_for_forced_checks():
    result = asyncio.run(
        run(Config(treatment="reserved"), load_case(FIXTURES, "honest_fix"), ScriptedPolicy())
    )
    first = next(e for e in result["events"] if e["type"] == "round")
    assert first["check_requests"] == 8 and first["effort"] == 32


def test_relay_flood_cannot_evict_latest_direct_probe():
    evidence = [{"id": "old", "kind": "probe"}, {"id": "probe", "kind": "probe"}]
    evidence += [{"id": f"peer:{i}", "kind": "peer"} for i in range(50)]
    visible = visible_evidence(evidence)
    assert len(visible) == 12
    assert visible[0]["id"] == "probe"
    assert visible[-1]["id"] == "peer:49"
    assert not any(e["id"] == "old" for e in visible)


def test_manifest_and_completion_preserve_identity_usage_and_status(tmp_path):
    class Metered:
        requested_model = "offline-test-policy"

        async def decide(self, view):
            return Reply(
                json.dumps({"action": "abstain", "p_support": 0.5, "sources": [], "message": ""}),
                usage={"input_tokens": 12, "output_tokens": 3},
                model="offline-test-policy-v1",
            )

    path = tmp_path / "events.jsonl"
    case = load_case(FIXTURES, "honest_fix")
    result = asyncio.run(run(Config(rounds=1), case, Metered(), path))
    events = [json.loads(line) for line in path.read_text().splitlines()]
    assert events == result["events"]
    manifest, completion = events[0], events[-1]
    assert manifest["fixture"] == case.id and manifest["truth"] == case.truth
    assert manifest["requested_model"] == "offline-test-policy"
    assert len(manifest["graph"]) == 8 and manifest["planned_calls"] == 8
    assert len(manifest["prompt_sha256"]) == 64
    assert len(manifest["harness_sha256"]) == 64
    assert completion["status"] == "success" and completion["calls"] == 8
    assert completion["usage_totals"] == {"input_tokens": 96, "output_tokens": 24}
    assert completion["decision_errors"] == {}
    assert result["kind"] == "custom_policy"


def test_provider_errors_remain_visible_and_do_not_leak_exception_text():
    class Broken:
        async def decide(self, view):
            raise RuntimeError("SECRET_PROVIDER_HEADER")

    result = asyncio.run(run(Config(rounds=1), load_case(FIXTURES, "honest_fix"), Broken()))
    assert "SECRET_PROVIDER_HEADER" not in json.dumps(result)
    completion = result["events"][-1]
    assert completion["status"] == "completed_with_errors"
    assert completion["decision_errors"] == {"provider_error:RuntimeError": 8}


def test_policy_cannot_mutate_recorded_view_or_create_citable_evidence():
    class Mutating:
        async def decide(self, view):
            view["evidence"].append({"id": "invented", "kind": "probe", "text": "Fake"})
            return Reply(
                json.dumps(
                    {
                        "action": "relay",
                        "p_support": 0.9,
                        "sources": ["invented"],
                        "message": "Fake",
                    }
                )
            )

    result = asyncio.run(run(Config(rounds=1), load_case(FIXTURES, "honest_fix"), Mutating()))
    decisions = [e for e in result["events"] if e["type"] == "decision"]
    assert all(e["error"] == "invalid_decision" for e in decisions)
    assert all(not any(v["id"] == "invented" for v in e["view"]["evidence"]) for e in decisions)


def test_interrupted_run_logs_status_and_started_calls(tmp_path):
    class Interrupted:
        async def decide(self, view):
            raise asyncio.CancelledError

    path = tmp_path / "interrupted.jsonl"
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(run(Config(rounds=1), load_case(FIXTURES, "honest_fix"), Interrupted(), path))
    events = [json.loads(line) for line in path.read_text().splitlines()]
    assert events[-1]["type"] == "completion"
    assert events[-1]["status"] == "interrupted"
    assert events[-1]["calls"] > 0


def test_shared_report_relay_ancestry_keeps_one_root():
    class Citing:
        async def decide(self, view):
            return Reply(
                json.dumps(
                    {
                        "action": "relay",
                        "p_support": 0.8,
                        "sources": [e["id"] for e in view["evidence"]],
                        "message": "Repeating visible reports.",
                    }
                )
            )

    result = asyncio.run(
        run(Config(treatment="ancestry", seed_share=1), load_case(FIXTURES, "honest_fix"), Citing())
    )
    decisions = [e for e in result["events"] if e["type"] == "decision"]
    assert all(e["error"] is None for e in decisions)
    assert all(
        receipt["root_ids"] == ["report:0"]
        for event in decisions
        for receipt in event["view"]["evidence"]
    )


def test_optional_inspect_adapter_works_with_local_mock_provider():
    from inspect_ai.model import ModelOutput, get_model

    text = json.dumps({"action": "abstain", "p_support": 0.5, "sources": [], "message": ""})
    policy = InspectPolicy("mockllm/model", max_tokens=64)
    policy.model = get_model(
        "mockllm/model", custom_outputs=[ModelOutput.from_content("mockllm/model", text)]
    )
    reply = asyncio.run(policy.decide({"claim": "Offline adapter check"}))
    assert reply.text == text
    assert reply.model == "mockllm/model"
    assert isinstance(reply.usage, dict)


def test_graph_and_report_seeding_use_independent_streams():
    from swarm_lab.experiment import network, seeded_agents

    base = Config(population=64, rounds=1, max_calls=64)
    shifted = Config(population=64, rounds=1, max_calls=64, seed_share=0.9)
    # Changing only the report share must not change the network.
    assert network(base) == network(shifted)
    # Seeded agents are not systematically the ones with a small-world shortcut.
    shortcut = {i for i, nbrs in enumerate(network(base)) if len(nbrs) > 4}
    overlaps = []
    for seed in range(40):
        c = Config(population=64, rounds=1, max_calls=64, seed=seed)
        sc = {i for i, nbrs in enumerate(network(c)) if len(nbrs) > 4}
        chosen = seeded_agents(c)
        if chosen:
            overlaps.append(len(set(chosen) & sc) / len(chosen))
    assert 0.2 < sum(overlaps) / len(overlaps) < 0.8
    assert shortcut


def test_positive_report_share_always_seeds_someone_and_zero_is_a_control():
    from swarm_lab.experiment import seeded_agents

    for seed in range(200):
        assert seeded_agents(Config(population=4, rounds=1, max_calls=4, seed=seed))
    assert seeded_agents(Config(population=4, rounds=1, max_calls=4, seed_share=0)) == []


def test_manifest_records_rng_scheme_and_seeded_agents():
    result = asyncio.run(run(Config(rounds=1), load_case(FIXTURES, "honest_fix"), ScriptedPolicy()))
    manifest = result["events"][0]
    assert manifest["rng_scheme"] == "independent-streams-v1"
    assert manifest["seeded_agents"] and manifest["parse_mode"] == "strict"
    first = [e for e in result["events"] if e["type"] == "decision" and e["round"] == 1]
    holders = {
        e["agent"] for e in first if any(x["kind"] == "report" for x in e["view"]["evidence"])
    }
    assert holders == set(manifest["seeded_agents"])


TRAILING = (
    '{"action":"abstain","p_support":0.5,"sources":[],"message":"ok"} \n'
    'assistant to=final\n{"action":"abstain"'
)


def test_strict_rejects_trailing_text_but_flags_it_recoverable():
    class Trailing:
        async def decide(self, view):
            return Reply(TRAILING, stop_reason="max_tokens")

    result = asyncio.run(run(Config(rounds=1), load_case(FIXTURES, "honest_fix"), Trailing()))
    decisions = [e for e in result["events"] if e["type"] == "decision"]
    assert all(e["error"] == "invalid_decision" for e in decisions)
    assert all(e["lenient_recoverable"] and not e["format_violation"] for e in decisions)
    assert all(e["stop_reason"] == "max_tokens" for e in decisions)


def test_lenient_mode_accepts_leading_object_and_records_violation():
    class Trailing:
        async def decide(self, view):
            return Reply(TRAILING)

    c = Config(rounds=1, parse_mode="lenient")
    result = asyncio.run(run(c, load_case(FIXTURES, "honest_fix"), Trailing()))
    decisions = [e for e in result["events"] if e["type"] == "decision"]
    assert all(e["error"] is None and e["format_violation"] for e in decisions)
    fenced = '```json\n{"action":"abstain","p_support":0.5,"sources":[],"message":""}\n```'
    view = {"evidence": [], "budget": 24, "pending": False}
    assert parse_decision(fenced, view, "lenient")["action"] == "abstain"
    with pytest.raises(ValueError):
        parse_decision(fenced, view)
    with pytest.raises(ValueError):
        Config(parse_mode="guess")


def test_reserved_views_disclose_the_forced_first_check():
    seen = []

    class Recorder:
        async def decide(self, view):
            seen.append(view)
            return Reply(
                json.dumps({"action": "abstain", "p_support": 0.5, "sources": [], "message": ""})
            )

    asyncio.run(run(Config(treatment="reserved", rounds=2, max_calls=16),
                    load_case(FIXTURES, "honest_fix"), Recorder()))
    assert all(v["forced_check"] and "protocol_note" in v for v in seen if v["round"] == 1)
    assert all(not v["forced_check"] and "protocol_note" not in v for v in seen if v["round"] == 2)
    plain = []

    class Plain(Recorder):
        async def decide(self, view):
            plain.append(view)
            return await super().decide(view)

    asyncio.run(run(Config(rounds=1), load_case(FIXTURES, "honest_fix"), Plain()))
    assert all("forced_check" not in v for v in plain)
