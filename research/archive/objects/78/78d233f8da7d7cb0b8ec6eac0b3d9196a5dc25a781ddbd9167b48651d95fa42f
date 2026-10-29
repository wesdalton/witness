"""Cost-reserved OpenRouter pilot. Dry-run by default; no implicit API calls.

Reservations are intentionally never refunded automatically, including failures.
A token reservation is conditional on the verified billing contract: text input
must fit its byte bound; max_tokens must cap ALL billed output, including reasoning;
and the route must have no additional per-request/tool charges. A dedicated,
non-resetting OpenRouter key limit supplies an independent provider-side cap.
Neither this program nor an API key can guarantee a provider's billing correctness.
"""

from __future__ import annotations

import argparse
import asyncio
import fcntl
import hashlib
import json
import math
import os
import re
import time
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from importlib.metadata import version
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from swarm_lab.experiment import SYSTEM, Config, InspectPolicy, Reply, load_case, run

CEILING = Decimal("100")
MILLION = Decimal("1000000")
FIXTURES = ("honest_fix", "pytest_module_shadow")
TREATMENTS = ("reports", "ancestry", "reserved")
PILOT_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
REASONING_REFERENCE = "https://openrouter.ai/docs/guides/best-practices/reasoning-tokens"


class BudgetError(RuntimeError):
    """Stop dispatch without exposing request headers or provider exception text."""


def money(value) -> Decimal:
    try:
        result = Decimal(str(value))
    except InvalidOperation as error:
        raise ValueError("Invalid monetary amount") from error
    if not result.is_finite() or result < 0:
        raise ValueError("Monetary amounts must be finite and nonnegative")
    return result


@dataclass(frozen=True)
class Billing:
    model: str
    provider: str
    input_per_million: str
    output_per_million: str
    price_as_of: str
    reference: str
    max_input_tokens: int = 16384
    max_output_tokens: int = 256
    bounds_confirmed: bool = False
    reasoning_effort: str = "none"
    min_request_interval: float = 0

    def __post_init__(self):
        if not self.model.startswith("openrouter/") or self.model.count("/") < 2:
            raise ValueError("Use an explicit openrouter/vendor/model identifier")
        if not re.fullmatch(r"[A-Za-z0-9_./:-]+", self.model) or not self.provider:
            raise ValueError("Invalid model or provider")
        if not self.reference.startswith("https://"):
            raise ValueError("Supply a primary HTTPS billing reference")
        if date.fromisoformat(self.price_as_of) > datetime.now(UTC).date():
            raise ValueError("Pricing date cannot be in the future")
        money(self.input_per_million)
        money(self.output_per_million)
        if self.reasoning_effort not in {"none", "low"}:
            raise ValueError("Pilot reasoning_effort must be none or low")
        if (
            type(self.min_request_interval) not in {int, float}
            or not math.isfinite(self.min_request_interval)
            or not 0 <= self.min_request_interval <= 60
        ):
            raise ValueError("Request pacing must be between zero and 60 seconds")
        for value, lower, upper in [
            (self.max_input_tokens, 4096, 262144),
            (self.max_output_tokens, 64, 4096),
        ]:
            if type(value) is not int or not lower <= value <= upper:
                raise ValueError("Invalid token reservation")

    @property
    def per_call(self) -> Decimal:
        return (
            self.max_input_tokens * money(self.input_per_million)
            + self.max_output_tokens * money(self.output_per_million)
        ) / MILLION

    @property
    def routing(self) -> dict:
        return {
            "only": [self.provider],
            "allow_fallbacks": False,
            "require_parameters": True,
            "max_price": {
                "prompt": float(money(self.input_per_million)),
                "completion": float(money(self.output_per_million)),
            },
        }

    @property
    def model_settings(self) -> dict:
        reasoning = (
            {"enabled": False}
            if self.reasoning_effort == "none"
            else {
                "enabled": True,
                "effort": self.reasoning_effort,
            }
        )
        return {
            "max_tokens": self.max_output_tokens,
            "reasoning": reasoning,
            "provider": self.routing,
            "cache_prompt": False,
            "inspect_max_retries": 0,
            "sdk_max_retries": 0,
            "timeout_seconds": 90,
            "sampling_parameters": "provider defaults; no API sampling seed supplied",
            "minimum_request_interval_seconds": self.min_request_interval,
        }


def live_contract(billing: Billing) -> dict:
    """Only model/provider/settings combinations whose output billing bounds were reviewed."""
    contracts = {
        "openrouter/openai/gpt-6-luna": (
            "openai",
            "none",
            64,
            "https://developers.openai.com/api/docs/models/gpt-6-luna",
        ),
        "openrouter/openai/gpt-6.1-sol": (
            "openai",
            "low",
            1024,
            "https://developers.openai.com/api/docs/models/gpt-6.1-sol",
        ),
        "openrouter/anthropic/claude-haiku-5.5": (
            "anthropic",
            "none",
            64,
            "https://platform.claude.com/docs/en/models/haiku-5-5/whats-new-haiku-5-5",
        ),
    }
    if billing.model not in contracts:
        raise BudgetError("No verified live billing contract for this model; use dry-run only")
    provider, effort, minimum_output, reference = contracts[billing.model]
    if billing.provider != provider or billing.reasoning_effort != effort:
        raise BudgetError(f"This model requires provider {provider} and reasoning effort {effort}")
    if billing.max_output_tokens < minimum_output:
        raise BudgetError(f"This model requires at least {minimum_output} total output tokens")
    if billing.model.endswith("claude-haiku-5.5") and billing.max_input_tokens >= 100000:
        raise BudgetError("Haiku live pilot must stay below its 100,000-token pricing tier")
    return {
        "model_reference": reference,
        "routing_reference": REASONING_REFERENCE,
        "output_bound_includes_reasoning": True,
        "verified_as_of": "2026-10-18",
    }


def input_bound(view: dict) -> int:
    """One token per serialized byte, plus 1024 framing tokens; never chars/4.

    This is an explicit bound assumption, not a universal provider tokenizer.
    JSON's ASCII escapes conservatively expand non-ASCII text before counting.
    """
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": json.dumps(view)},
    ]
    return max(4096, len(json.dumps(messages, ensure_ascii=True).encode("utf-8")) + 1024)


class Ledger:
    """Append-only reservations, locked across processes and fsynced before calls."""

    def __init__(self, path: Path):
        self.path = path

    @contextmanager
    def transaction(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(self.path, os.O_RDWR | os.O_CREAT, 0o600)
        with os.fdopen(fd, "r+", encoding="utf-8") as stream:
            fcntl.flock(stream, fcntl.LOCK_EX)
            try:
                raw = stream.read()
                if raw and not raw.endswith("\n"):
                    raise BudgetError("Incomplete ledger; reconcile it before any further calls")
                try:
                    events = [json.loads(line) for line in raw.splitlines()]
                except json.JSONDecodeError as error:
                    raise BudgetError("Invalid ledger; no calls permitted") from error
                if events and events[0] != {
                    "type": "authorization",
                    "usd": str(CEILING),
                    "schema": "witness.budget.v1",
                }:
                    raise BudgetError("Unrecognized budget ledger")

                def append(event):
                    stream.seek(0, os.SEEK_END)
                    stream.write(json.dumps(event, allow_nan=False) + "\n")
                    stream.flush()
                    os.fsync(stream.fileno())
                    events.append(event)

                if not events:
                    append(
                        {
                            "type": "authorization",
                            "usd": str(CEILING),
                            "schema": "witness.budget.v1",
                        }
                    )
                yield events, append
            finally:
                fcntl.flock(stream, fcntl.LOCK_UN)

    def reserve_batch(
        self, batch: str, calls: int, billing: Billing, batch_ceiling: Decimal, metadata: dict
    ) -> Decimal:
        if type(calls) is not int or calls < 1 or not 0 < batch_ceiling <= CEILING:
            raise BudgetError("Invalid batch limit")
        amount = calls * billing.per_call
        if amount > batch_ceiling:
            raise BudgetError("Worst-case batch reservation exceeds the batch ceiling")
        with self.transaction() as (events, append):
            if any(e.get("batch") == batch for e in events):
                raise BudgetError(
                    "Batch already exists; live batches are never automatically rerun"
                )
            total = sum(
                (money(e["usd"]) for e in events if e["type"] == "batch_reserved"), Decimal(0)
            )
            if total + amount > CEILING:
                raise BudgetError("Cumulative reservations exceed the authorized US$100")
            append(
                {
                    "type": "batch_reserved",
                    "batch": batch,
                    "calls": calls,
                    "usd": str(amount),
                    "per_call_usd": str(billing.per_call),
                    "billing": asdict(billing),
                    "metadata": metadata,
                    "at": datetime.now(UTC).isoformat(),
                }
            )
        return amount

    def start_request(self, batch: str, request: str, bound: int) -> None:
        with self.transaction() as (events, append):
            reservation = next(
                (e for e in events if e["type"] == "batch_reserved" and e["batch"] == batch), None
            )
            if not reservation:
                raise BudgetError("Request has no prepaid batch reservation")
            started = [e for e in events if e["type"] == "request_reserved" and e["batch"] == batch]
            if len(started) >= reservation["calls"]:
                raise BudgetError("Batch call ceiling reached")
            if any(e.get("batch") == batch and e.get("request") == request for e in events):
                raise BudgetError("Request already dispatched; retries are disabled")
            if bound > reservation["billing"]["max_input_tokens"]:
                raise BudgetError("Input exceeds its preallocated token bound")
            append(
                {
                    "type": "request_reserved",
                    "batch": batch,
                    "request": request,
                    "input_bound": bound,
                    "usd": reservation["per_call_usd"],
                    "at": datetime.now(UTC).isoformat(),
                }
            )

    def finish_request(self, batch: str, request: str, event: dict) -> None:
        with self.transaction() as (events, append):
            if not any(
                e["type"] == "request_reserved" and e["batch"] == batch and e["request"] == request
                for e in events
            ):
                raise BudgetError("Cannot reconcile an unreserved request")
            if any(
                e["type"] == "request_completed" and e["batch"] == batch and e["request"] == request
                for e in events
            ):
                raise BudgetError("Request already reconciled")
            append(
                {
                    "type": "request_completed",
                    "batch": batch,
                    "request": request,
                    "reservation_retained": True,
                    **event,
                }
            )


def load_key(env_file: Path = Path(".env")) -> str | None:
    """Read only a literal OPENROUTER_API_KEY; never execute or expand .env text."""
    value = os.environ.get("OPENROUTER_API_KEY")
    if not value and env_file.exists():
        values = []
        for line in env_file.read_text().splitlines():
            match = re.match(r"^\s*(?:export\s+)?OPENROUTER_API_KEY\s*=\s*(.*?)\s*$", line)
            if match:
                candidate = match.group(1)
                if len(candidate) >= 2 and candidate[0] == candidate[-1] and candidate[0] in "\"'":
                    candidate = candidate[1:-1]
                values.append(candidate)
        if len(values) > 1:
            raise BudgetError("Duplicate OPENROUTER_API_KEY entries; use one literal value")
        value = values[0] if values else None
    if value and not re.fullmatch(r"[A-Za-z0-9_-]+", value):
        raise BudgetError("OPENROUTER_API_KEY must be a literal token")
    return value or None


def validate_key_limits(data: dict, required: Decimal) -> dict:
    try:
        limit, remaining = money(data["limit"]), money(data["limit_remaining"])
        if not 0 < limit <= CEILING or remaining > limit or remaining < required:
            raise BudgetError("Use a dedicated key capped at US$100 or less with enough remaining")
        if "limit_reset" not in data or data["limit_reset"] is not None:
            raise BudgetError("The dedicated key spending limit must not reset")
    except (KeyError, TypeError, ValueError) as error:
        raise BudgetError("Key budget metadata is incomplete or invalid") from error
    # Never retain or print the API's label, owner, hash, or key itself.
    return {
        "limit_usd": str(limit),
        "remaining_usd": str(remaining),
        "reset": None,
        "include_byok_in_limit": data.get("include_byok_in_limit") is True,
        "byok_note": (
            "Local reservations apply to all calls; the provider key cap "
            "may exclude external BYOK charges."
        ),
    }


def preflight_key(key: str, required: Decimal) -> dict:
    class NoRedirect(HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    request = Request(
        "https://openrouter.ai/api/v1/key", headers={"Authorization": f"Bearer {key}"}
    )
    try:
        with build_opener(NoRedirect).open(request, timeout=20) as response:
            data = json.load(response)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        raise BudgetError("OpenRouter key preflight failed; no paid requests dispatched") from None
    return validate_key_limits(data.get("data", {}), required)


class OpenRouterPolicy(InspectPolicy):
    def __init__(self, billing: Billing, key: str):
        from inspect_ai.model import GenerateConfig, get_model

        live_contract(billing)
        self.requested_model = billing.model
        self.config = GenerateConfig(
            max_tokens=billing.max_output_tokens,
            max_retries=0,
            timeout=90,
            cache_prompt=False,
            reasoning_effort=None
            if billing.reasoning_effort == "none"
            else billing.reasoning_effort,
        )
        self.model = get_model(
            billing.model,
            config=self.config,
            api_key=key,
            base_url="https://openrouter.ai/api/v1",
            provider=billing.routing,
            reasoning_enabled=billing.reasoning_effort != "none",
            max_retries=0,
        )


def safe_provider_error(error: BaseException) -> dict:
    """Unwrap retry envelopes without retaining error messages, headers, or bodies."""
    result = {"error_type": type(error).__name__}
    seen = set()
    current = error
    for _ in range(4):
        if id(current) in seen:
            break
        seen.add(id(current))
        result["underlying_error_type"] = type(current).__name__
        status = getattr(current, "status_code", None)
        if type(status) is int and 100 <= status <= 599:
            result["http_status"] = status
        attempt = getattr(current, "last_attempt", None)
        if attempt is not None:
            number = getattr(attempt, "attempt_number", None)
            if type(number) is int:
                result["attempt_number"] = number
            try:
                cause = attempt.exception()
            except Exception:
                cause = None
        else:
            cause = current.__cause__
        if not isinstance(cause, BaseException):
            break
        current = cause
    return result


class GuardedPolicy(InspectPolicy):
    """Reserve before dispatch and retain cost uncertainty; stop after any anomaly."""

    def __init__(self, delegate, ledger: Ledger, batch: str, billing: Billing):
        self.delegate, self.ledger, self.batch, self.billing = delegate, ledger, batch, billing
        self.requested_model = billing.model
        self.run_id = "unset"
        self.stopped = False
        self.last_dispatch_at: float | None = None

    async def decide(self, view: dict) -> Reply:
        if self.stopped:
            raise BudgetError("Pilot stopped after an unresolved request")
        if self.last_dispatch_at is not None and self.billing.min_request_interval:
            delay = self.billing.min_request_interval - (time.monotonic() - self.last_dispatch_at)
            if delay > 0:
                await asyncio.sleep(delay)
        request = f"{self.run_id}:{view['round']}:{view['agent']}"
        try:
            self.ledger.start_request(self.batch, request, input_bound(view))
        except Exception:
            self.stopped = True
            raise
        try:
            self.last_dispatch_at = time.monotonic()
            reply = await self.delegate.decide(view)
        except BaseException as error:
            self.stopped = True
            self.ledger.finish_request(
                self.batch,
                request,
                {"status": "unknown_charge", **safe_provider_error(error)},
            )
            raise
        usage = reply.usage if isinstance(reply.usage, dict) else {}
        fields = ("input_tokens", "output_tokens")
        complete = all(type(usage.get(k)) is int and usage[k] >= 0 for k in fields)
        inputs = usage.get("input_tokens", 0) if complete else 0
        for key in ("input_tokens_cache_read", "input_tokens_cache_write"):
            value = usage.get(key)
            if value is not None:
                complete = complete and type(value) is int and value >= 0
                if type(value) is int:
                    inputs += value
        outputs = usage.get("output_tokens", 0)
        if not complete:
            status, estimated = "unknown_usage", None
        elif inputs > self.billing.max_input_tokens or outputs > self.billing.max_output_tokens:
            status, estimated = "token_bound_exceeded", None
        else:
            estimated = (
                inputs * money(self.billing.input_per_million)
                + outputs * money(self.billing.output_per_million)
            ) / MILLION
            status = "usage_recorded"
        reported = usage.get("total_cost")
        try:
            reported_cost = money(reported) if reported is not None else None
        except ValueError:
            reported_cost = None
            status = "invalid_reported_cost"
        if reported_cost is not None and reported_cost > self.billing.per_call:
            status = "cost_bound_exceeded"
        if status != "usage_recorded":
            self.stopped = True
        self.ledger.finish_request(
            self.batch,
            request,
            {
                "status": status,
                "usage": usage,
                "priced_token_cost_usd": str(estimated) if estimated is not None else None,
                "provider_reported_cost_usd": str(reported_cost)
                if reported_cost is not None
                else None,
            },
        )
        return reply


def plan(
    billing: Billing,
    population=8,
    rounds=8,
    seed=42,
    fixtures=FIXTURES,
    treatments=TREATMENTS,
    max_calls=384,
    parse_mode="strict",
) -> dict:
    if (
        not fixtures
        or not treatments
        or len(set(fixtures)) != len(fixtures)
        or len(set(treatments)) != len(treatments)
        or any(f not in FIXTURES for f in fixtures)
        or any(t not in TREATMENTS for t in treatments)
    ):
        raise ValueError("Use distinct supported fixtures and treatments")
    configs = [
        Config(
            population=population,
            rounds=rounds,
            seed=seed,
            treatment=t,
            max_calls=population * rounds,
            max_output_tokens=billing.max_output_tokens,
            concurrency=1,
            parse_mode=parse_mode,
        )
        for t in treatments
    ]
    calls = len(fixtures) * sum(c.population * c.rounds for c in configs)
    if type(max_calls) is not int or not 1 <= max_calls <= 12800 or calls > max_calls:
        raise BudgetError("Planned calls exceed the explicit pilot call ceiling")
    return {
        "schema": "witness.pilot.v1",
        "model": billing.model,
        "billing": asdict(billing),
        "model_settings": billing.model_settings,
        "pilot_sha256": PILOT_SHA256,
        "inspect_version": version("inspect-ai"),
        "fixtures": list(fixtures),
        "configs": [asdict(c) for c in configs],
        "planned_calls": calls,
        "reserved_usd": str(calls * billing.per_call),
        "global_authorization_usd": str(CEILING),
        "automatic_refunds": False,
        "input_bound": "serialized ASCII JSON bytes + 1024 framing; floor 4096",
        "billing_limitations": (
            "Requires verified model token/output bounds and no extra fees; "
            "provider-side key limit is also required."
        ),
    }


async def execute(
    plan_record: dict,
    billing: Billing,
    key: str,
    ledger: Ledger,
    out: Path,
    fixtures: Path,
    batch_ceiling: Decimal,
) -> dict:
    if not billing.bounds_confirmed:
        raise BudgetError("Verify model-specific token/output billing bounds before --live")
    contract = live_contract(billing)
    required = money(plan_record["reserved_usd"])
    if required > batch_ceiling:
        raise BudgetError("Planned reservation exceeds the batch ceiling; reduce the pilot first")
    if out.exists():
        raise BudgetError("Output directory exists; choose a new --out before reserving")
    key_limits = preflight_key(key, required)
    batch = str(uuid.uuid4())
    manifest = {
        **plan_record,
        "batch": batch,
        "key_limits": key_limits,
        "live_contract": contract,
        "started_at": datetime.now(UTC).isoformat(),
        "status": "started",
    }
    ledger.reserve_batch(
        batch,
        plan_record["planned_calls"],
        billing,
        batch_ceiling,
        {"output": str(out.resolve()), "key_limits": key_limits},
    )
    out.mkdir(parents=True, exist_ok=False)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    policy = GuardedPolicy(OpenRouterPolicy(billing, key), ledger, batch, billing)
    results = []
    for fixture in plan_record["fixtures"]:
        for config in plan_record["configs"]:
            c = Config(**config)
            policy.run_id = f"{fixture}-{c.treatment}"
            result = await run(
                c, load_case(fixtures, fixture), policy, out / f"{policy.run_id}.jsonl"
            )
            (out / f"{policy.run_id}.json").write_text(json.dumps(result, indent=2) + "\n")
            results.append({"run": policy.run_id, "status": result["status"]})
            if policy.stopped or result["status"] != "success":
                break
        if policy.stopped or results[-1]["status"] != "success":
            break
    summary = {
        "batch": batch,
        "status": "success"
        if len(results) == len(plan_record["fixtures"]) * len(plan_record["configs"])
        and all(r["status"] == "success" for r in results)
        and not policy.stopped
        else "stopped",
        "runs": results,
        "reservation_retained_usd": str(required),
        "finished_at": datetime.now(UTC).isoformat(),
    }
    (out / "completion.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--provider", required=True, help="Pinned OpenRouter provider slug")
    parser.add_argument("--input-price", required=True, help="USD per million input tokens")
    parser.add_argument("--output-price", required=True, help="USD per million output tokens")
    parser.add_argument("--price-as-of", required=True, help="ISO date pricing was verified")
    parser.add_argument("--billing-reference", required=True)
    parser.add_argument("--max-input-tokens", type=int, default=16384)
    parser.add_argument("--max-output-tokens", type=int, default=256)
    parser.add_argument("--reasoning-effort", choices=["none", "low"], default="none")
    parser.add_argument(
        "--min-request-interval",
        type=float,
        default=0,
        help="Optional seconds between request starts; no automatic retries",
    )
    parser.add_argument("--population", type=int, default=8)
    parser.add_argument("--rounds", type=int, default=8)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--fixture", action="append", choices=FIXTURES)
    parser.add_argument("--treatment", action="append", choices=TREATMENTS)
    parser.add_argument("--max-calls", type=int, default=384)
    parser.add_argument(
        "--parse-mode",
        choices=["strict", "lenient"],
        default="strict",
        help="lenient accepts a leading JSON object and flags the format violation",
    )
    parser.add_argument("--batch-ceiling", default="5")
    parser.add_argument("--ledger", type=Path, default=Path("research/swarm/pilot-budget.jsonl"))
    parser.add_argument("--out", type=Path, default=Path("research/swarm/live-pilot"))
    parser.add_argument(
        "--fixtures", type=Path, default=Path("research/pilots/scorer_integrity_results.json")
    )
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--billing-bounds-confirmed", action="store_true")
    parser.add_argument(
        "--live", action="store_true", help="Explicitly dispatch reserved paid calls"
    )
    args = parser.parse_args()
    try:
        billing = Billing(
            args.model,
            args.provider,
            args.input_price,
            args.output_price,
            args.price_as_of,
            args.billing_reference,
            args.max_input_tokens,
            args.max_output_tokens,
            args.billing_bounds_confirmed,
            args.reasoning_effort,
            args.min_request_interval,
        )
        planned = plan(
            billing,
            args.population,
            args.rounds,
            args.seed,
            args.fixture or FIXTURES,
            args.treatment or TREATMENTS,
            args.max_calls,
            args.parse_mode,
        )
        ceiling = money(args.batch_ceiling)
        if not 0 < ceiling <= CEILING or money(planned["reserved_usd"]) > ceiling:
            raise BudgetError("Worst-case plan exceeds the batch ceiling")
        if not args.live:
            print(
                json.dumps(
                    {**planned, "mode": "dry_run", "batch_ceiling_usd": str(ceiling)}, indent=2
                )
            )
            return
        key = load_key(args.env_file)
        if not key:
            raise BudgetError("Configure OPENROUTER_API_KEY in the environment or local .env")
        result = asyncio.run(
            execute(planned, billing, key, Ledger(args.ledger), args.out, args.fixtures, ceiling)
        )
        print(json.dumps(result))
    except (BudgetError, ValueError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
