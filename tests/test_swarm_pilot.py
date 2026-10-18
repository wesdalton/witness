"""Offline checks for durable spending limits; these tests never contact an API."""

import asyncio
import json
from decimal import Decimal

import pytest

from swarm_lab.experiment import Reply
from swarm_lab.pilot import (
    Billing,
    BudgetError,
    GuardedPolicy,
    Ledger,
    OpenRouterPolicy,
    input_bound,
    live_contract,
    load_key,
    plan,
    safe_provider_error,
    validate_key_limits,
)


def billing(**overrides):
    values = dict(
        model="openrouter/openai/gpt-6-luna",
        provider="openai",
        input_per_million="0.1",
        output_per_million="0.5",
        price_as_of="2026-10-18",
        reference="https://openrouter.ai/api/v1/models",
    )
    return Billing(**(values | overrides))


def test_whole_batch_is_preallocated_and_expensive_plans_fail(tmp_path):
    ledger = Ledger(tmp_path / "budget.jsonl")
    b = billing()
    p = plan(b)
    assert p["planned_calls"] == 384
    assert Decimal(p["reserved_usd"]) == Decimal("0.6782976")
    ledger.reserve_batch("one", 384, b, Decimal("5"), {})
    with pytest.raises(BudgetError, match="already exists"):
        ledger.reserve_batch("one", 384, b, Decimal("5"), {})
    with pytest.raises(BudgetError, match="batch ceiling"):
        ledger.reserve_batch("two", 384, billing(input_per_million="20"), Decimal("5"), {})


def test_cumulative_authorization_survives_process_reopen(tmp_path):
    path = tmp_path / "budget.jsonl"
    b = billing(input_per_million="100", output_per_million="0", max_input_tokens=10000)
    Ledger(path).reserve_batch("one", 60, b, Decimal("100"), {})
    with pytest.raises(BudgetError, match="Cumulative"):
        Ledger(path).reserve_batch("two", 41, b, Decimal("100"), {})


def test_requests_require_prior_reservation_and_cannot_repeat(tmp_path):
    ledger = Ledger(tmp_path / "budget.jsonl")
    with pytest.raises(BudgetError):
        ledger.start_request("one", "r1", 4096)
    ledger.reserve_batch("one", 1, billing(), Decimal("5"), {})
    ledger.start_request("one", "r1", 4096)
    with pytest.raises(BudgetError):
        ledger.start_request("one", "r1", 4096)
    with pytest.raises(BudgetError):
        ledger.start_request("one", "r2", 4096)
    ledger.finish_request("one", "r1", {"status": "unknown_charge"})
    with pytest.raises(BudgetError):
        ledger.finish_request("one", "r1", {"status": "unknown_charge"})
    records = [json.loads(line) for line in ledger.path.read_text().splitlines()]
    assert records[-1]["reservation_retained"] is True


def test_corrupt_ledger_fails_closed(tmp_path):
    path = tmp_path / "budget.jsonl"
    path.write_text('{"partial":')
    with pytest.raises(BudgetError, match="Incomplete"):
        Ledger(path).reserve_batch("one", 1, billing(), Decimal("5"), {})


def test_request_ids_are_unique_within_each_batch_not_across_experiments(tmp_path):
    path = tmp_path / "budget.jsonl"
    request = "honest_fix-reports:1:0"
    b = billing()
    for batch in ["first-model-seed42", "second-model-seed42"]:
        ledger = Ledger(path)
        ledger.reserve_batch(batch, 2, b, Decimal("5"), {})
        ledger.start_request(batch, request, 4096)
        ledger.finish_request(batch, request, {"status": "usage_recorded"})
        # Spare call capacity ensures this rejects the duplicate itself,
        # rather than accidentally passing because the call ceiling was reached.
        with pytest.raises(BudgetError, match="already dispatched"):
            ledger.start_request(batch, request, 4096)
    events = [json.loads(line) for line in path.read_text().splitlines()]
    starts = [e for e in events if e["type"] == "request_reserved"]
    assert [(e["batch"], e["request"]) for e in starts] == [
        ("first-model-seed42", request),
        ("second-model-seed42", request),
    ]
    assert sum(Decimal(e["usd"]) for e in events if e["type"] == "batch_reserved") == 4 * b.per_call


def test_serialized_byte_bound_handles_unicode_and_large_inputs():
    assert input_bound({"message": "hi"}) >= 4096
    assert input_bound({"message": "😀" * 1000}) > 10000


@pytest.mark.parametrize(
    "usage,status",
    [
        ({}, "unknown_usage"),
        ({"input_tokens": "100", "output_tokens": 20}, "unknown_usage"),
        ({"input_tokens": 20000, "output_tokens": 20}, "token_bound_exceeded"),
        ({"input_tokens": 100, "output_tokens": 20, "total_cost": 10}, "cost_bound_exceeded"),
    ],
)
def test_usage_anomaly_stops_further_paid_calls_and_retains_reservation(tmp_path, usage, status):
    class Fake:
        calls = 0

        async def decide(self, view):
            self.calls += 1
            return Reply("{}", usage=usage)

    b = billing()
    ledger = Ledger(tmp_path / "budget.jsonl")
    ledger.reserve_batch("one", 2, b, Decimal("5"), {})
    fake = Fake()
    policy = GuardedPolicy(fake, ledger, "one", b)
    asyncio.run(policy.decide({"round": 1, "agent": 0}))
    with pytest.raises(BudgetError):
        asyncio.run(policy.decide({"round": 1, "agent": 1}))
    assert fake.calls == 1
    last = json.loads(ledger.path.read_text().splitlines()[-1])
    assert last["status"] == status and last["reservation_retained"]


def test_cached_input_is_counted_in_bound(tmp_path):
    class Fake:
        async def decide(self, view):
            return Reply(
                "{}",
                usage={"input_tokens": 10, "input_tokens_cache_read": 17000, "output_tokens": 20},
            )

    b = billing()
    ledger = Ledger(tmp_path / "budget.jsonl")
    ledger.reserve_batch("one", 1, b, Decimal("5"), {})
    policy = GuardedPolicy(Fake(), ledger, "one", b)
    asyncio.run(policy.decide({"round": 1, "agent": 0}))
    assert policy.stopped


def test_large_input_is_rejected_before_provider_dispatch(tmp_path):
    class Never:
        async def decide(self, view):
            raise AssertionError("Must not dispatch")

    b = billing()
    ledger = Ledger(tmp_path / "budget.jsonl")
    ledger.reserve_batch("one", 1, b, Decimal("5"), {})
    policy = GuardedPolicy(Never(), ledger, "one", b)
    with pytest.raises(BudgetError, match="Input exceeds"):
        asyncio.run(policy.decide({"round": 1, "agent": 0, "text": "x" * 20000}))


def test_key_metadata_is_scrubbed_and_nonresetting_cap_enforced():
    data = {
        "limit": 100,
        "limit_remaining": 100,
        "limit_reset": None,
        "include_byok_in_limit": False,
        "label": "SECRET",
    }
    public = validate_key_limits(data, Decimal("1"))
    assert "SECRET" not in json.dumps(public)
    assert public["include_byok_in_limit"] is False
    for change in [
        {"limit": None},
        {"limit": 101},
        {"limit_reset": "monthly"},
        {"limit_remaining": 0},
    ]:
        with pytest.raises(BudgetError):
            validate_key_limits(data | change, Decimal("1"))


def test_env_reader_never_executes_or_expands_text(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    path = tmp_path / ".env"
    path.write_text("IGNORED=$(touch NEVER)\nOPENROUTER_API_KEY='test-literal'\n")
    assert load_key(path) == "test-literal"
    path.write_text("OPENROUTER_API_KEY=$(touch NEVER)\n")
    with pytest.raises(BudgetError):
        load_key(path)
    assert not (tmp_path / "NEVER").exists()


def test_first_calibration_is_exactly_eight_calls():
    p = plan(
        billing(),
        population=4,
        rounds=2,
        fixtures=["pytest_module_shadow"],
        treatments=["reports"],
        max_calls=8,
    )
    assert p["planned_calls"] == 8 and Decimal(p["reserved_usd"]) < Decimal("0.02")
    with pytest.raises(BudgetError):
        plan(billing(), max_calls=383)


def test_provider_can_observe_durable_reservation_before_dispatch(tmp_path):
    ledger = Ledger(tmp_path / "budget.jsonl")
    b = billing()
    ledger.reserve_batch("one", 1, b, Decimal("5"), {})

    class Fake:
        async def decide(self, view):
            event = json.loads(ledger.path.read_text().splitlines()[-1])
            assert event["type"] == "request_reserved"
            return Reply("{}", usage={"input_tokens": 100, "output_tokens": 20})

    policy = GuardedPolicy(Fake(), ledger, "one", b)
    asyncio.run(policy.decide({"round": 1, "agent": 0}))
    assert not policy.stopped


def test_live_adapter_pins_routing_and_disables_all_retries_without_network():
    policy = OpenRouterPolicy(billing(), "fake-key-never-sent")
    assert policy.config.max_retries == 0
    assert policy.config.cache_prompt is False
    assert policy.model.api.provider == billing().routing
    assert policy.model.api.reasoning_enabled is False
    assert policy.model.api.client.max_retries == 0


def test_dry_run_never_opens_key_file_or_network(tmp_path, monkeypatch, capsys):
    from swarm_lab import pilot

    def forbidden(*args, **kwargs):
        raise AssertionError("Dry-run must not touch credentials or network")

    monkeypatch.setattr(pilot, "load_key", forbidden)
    monkeypatch.setattr(pilot, "preflight_key", forbidden)
    monkeypatch.setattr(
        "sys.argv",
        [
            "pilot",
            "--model",
            "openrouter/openai/gpt-6-luna",
            "--provider",
            "openai",
            "--input-price",
            "0.1",
            "--output-price",
            "0.5",
            "--price-as-of",
            "2026-10-18",
            "--billing-reference",
            "https://openrouter.ai/api/v1/models",
        ],
    )
    pilot.main()
    result = json.loads(capsys.readouterr().out)
    assert result["mode"] == "dry_run"


def test_sol_uses_low_reasoning_and_total_output_cap_without_network():
    b = billing(
        model="openrouter/openai/gpt-6.1-sol",
        reasoning_effort="low",
        max_output_tokens=1024,
        input_per_million="2",
        output_per_million="10",
    )
    policy = OpenRouterPolicy(b, "fake-key-never-sent")
    params = policy.model.api.completion_params(policy.config, tools=False)
    assert params["extra_body"]["reasoning"] == {"effort": "low", "enabled": True}
    assert policy.config.max_tokens == 1024
    for bad in [billing(model=b.model), billing(model=b.model, reasoning_effort="low")]:
        with pytest.raises(BudgetError):
            live_contract(bad)


def test_haiku_uses_disabled_thinking_without_sending_invalid_none_effort():
    b = billing(model="openrouter/anthropic/claude-haiku-5.5", provider="anthropic")
    policy = OpenRouterPolicy(b, "fake-key-never-sent")
    params = policy.model.api.completion_params(policy.config, tools=False)
    assert params["extra_body"]["reasoning"] == {"enabled": False}
    assert policy.config.cache_prompt is False
    with pytest.raises(BudgetError):
        live_contract(billing(model=b.model, provider="anthropic", max_input_tokens=100000))


def test_plan_records_source_hash_and_generation_settings():
    p = plan(billing())
    assert len(p["pilot_sha256"]) == 64
    assert p["model_settings"]["reasoning"] == {"enabled": False}
    assert p["model_settings"]["minimum_request_interval_seconds"] == 0
    assert p["inspect_version"]


def test_retry_error_diagnostics_retain_status_without_secret_text():
    from concurrent.futures import Future

    from tenacity import RetryError

    class HTTPFailure(Exception):
        status_code = 429

    future = Future()
    future.attempt_number = 1
    future.set_exception(HTTPFailure("SECRET_BODY_AND_KEY"))
    diagnostic = safe_provider_error(RetryError(future))
    assert diagnostic == {
        "error_type": "RetryError",
        "underlying_error_type": "HTTPFailure",
        "http_status": 429,
        "attempt_number": 1,
    }
    assert "SECRET" not in json.dumps(diagnostic)


def test_unsupported_live_models_remain_blocked():
    for model in ["openrouter/anthropic/claude-sonnet-5.5", "openrouter/google/gemini-3.8-flash"]:
        with pytest.raises(BudgetError, match="No verified"):
            live_contract(billing(model=model))


def test_existing_output_directory_blocks_before_any_reservation(tmp_path, monkeypatch):
    from swarm_lab import pilot

    def forbidden(*args, **kwargs):
        raise AssertionError("Must not contact the provider")

    monkeypatch.setattr(pilot, "preflight_key", forbidden)
    out = tmp_path / "exists"
    out.mkdir()
    ledger = Ledger(tmp_path / "budget.jsonl")
    b = billing(bounds_confirmed=True)
    p = plan(b, population=4, rounds=1, fixtures=["honest_fix"], treatments=["reports"])
    with pytest.raises(BudgetError, match="Output directory exists"):
        asyncio.run(pilot.execute(p, b, "k", ledger, out, tmp_path / "f.json", Decimal("5")))
    assert not ledger.path.exists()


def test_plan_carries_parse_mode_into_episode_configs():
    p = plan(billing(), parse_mode="lenient")
    assert {c["parse_mode"] for c in p["configs"]} == {"lenient"}
