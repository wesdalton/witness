import json
from decimal import Decimal

import pytest

from swarm_lab.agent_budget import PhaseBudget
from swarm_lab.pilot import BudgetError
from swarm_lab.portfolio import TOOLS, stop_after_episode, unattempted_specs
from swarm_lab.research_client import ResponsesClient


def test_continuation_keeps_started_failures_and_excludes_every_attempted_spec(tmp_path):
    specs = [{"id": f"episode-{i:03d}"} for i in range(1, 4)]
    (tmp_path / "manifest.json").write_text(json.dumps({"episodes": specs}))
    (tmp_path / "completion.json").write_text(json.dumps(
        {"status": "stopped_for_review", "attempted_episodes": 2}))
    for i in (1, 2):
        (tmp_path / f"episode-{i:03d}.jsonl").write_text("{}\n")
        (tmp_path / f"episode-{i:03d}.json").write_text("{}")
    _, remaining = unattempted_specs(tmp_path)
    assert remaining == [specs[2]]
    (tmp_path / "episode-002.json").unlink()
    with pytest.raises(ValueError, match="Unfinished"):
        unattempted_specs(tmp_path)


def test_expanded_limit_still_blocks_oversized_payload_before_reservation(tmp_path):
    ledger = PhaseBudget(tmp_path / "ledger")
    client = ResponsesClient("test", "openai/gpt-6-luna", ledger, "batch", Decimal(1),
                             Decimal(".000000125"), Decimal(".0000005"), tools=TOOLS,
                             responses_input_limit=256000)
    messages = [{"role": "system", "content": "system"},
                {"role": "user", "content": "x"*256000}]
    with pytest.raises(BudgetError, match="short-context ceiling"):
        client.generate(messages)
    assert not (tmp_path / "ledger").exists()
    assert client.calls == 0


def test_expanded_luna_reservation_accounts_for_full_payload():
    class ReachedReservation(Exception):
        pass

    class RecordingBudget:
        def reserve(self, request, batch, amount, limit):
            self.amount = amount
            raise ReachedReservation

    ledger = RecordingBudget()
    client = ResponsesClient("test", "openai/gpt-6-luna", ledger, "batch", Decimal(1),
                             Decimal(".000000125"), Decimal(".0000005"), tools=TOOLS,
                             responses_input_limit=256000, max_tokens=4096)
    messages = [{"role": "system", "content": "system"},
                {"role": "user", "content": "x"*170000}]
    with pytest.raises(ReachedReservation):
        client.generate(messages)
    assert ledger.amount > Decimal(170000)*Decimal(".000000125")
    assert ledger.amount < Decimal(256000)*Decimal(".000000125") + Decimal(".002048")
    assert client.calls == 0


def test_unreviewed_model_cannot_use_expanded_limit(tmp_path):
    with pytest.raises(BudgetError, match="only for Luna"):
        ResponsesClient("test", "openai/gpt-6.1-sol", PhaseBudget(tmp_path / "ledger"),
                        "batch", Decimal(1), Decimal(".0000025"), Decimal(".00001"),
                        tools=TOOLS, responses_input_limit=256000)


def test_continuing_model_errors_never_continues_infrastructure_or_truncation():
    assert stop_after_episode("invalid_action")
    assert not stop_after_episode("invalid_action", True)
    assert not stop_after_episode("completed", True)
    for status in ("infrastructure_error", "truncated_output", "turn_limit", "unknown"):
        assert stop_after_episode(status, True)
