"""OpenRouter access: credential loading, key preflight, catalog pricing and bounded
Chat Completions / Responses clients that reserve and settle through PhaseBudget."""

from __future__ import annotations

import json
import os
import re
import time
import uuid
from decimal import Decimal
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from swarm_lab.core.budget import BudgetError, money
from swarm_lab.core.records import digest

MODEL_ROUTES = {"openai/gpt-6-luna": "openai", "anthropic/claude-haiku-5.5": "anthropic"}
KEY_LIMIT_CAP = Decimal("100")


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def get_json(url: str):
    with build_opener(NoRedirect()).open(url, timeout=30) as response:
        return json.load(response)


def model_catalog(model: str):
    if model not in MODEL_ROUTES:
        raise ValueError("Model needs a reviewed native-tool and billing contract")
    row = next((m for m in get_json("https://openrouter.ai/api/v1/models")["data"]
                if m["id"] == model), None)
    if row is None or not {"tools", "tool_choice"} <= set(row["supported_parameters"]):
        raise BudgetError("Reviewed model or tool support unavailable")
    pricing = row["pricing"]
    if money(pricing.get("request", 0)) != 0:
        raise BudgetError("Per-request charges need a separate contract")
    # No provider-hosted tools, cache control, prompt caches, or reasoning requested.
    # Include cache-write rates anyway to make input reservations conservative.
    input_price = max(money(pricing.get(k, 0)) for k in
                      ("prompt", "input_cache_write", "input_cache_write_1h"))
    output_price = money(pricing["completion"])
    if input_price > Decimal("0.0000002") or output_price > Decimal("0.0000005"):
        raise BudgetError("Catalog exceeds reviewed pilot price ceiling")
    return row, input_price, output_price


class Client:
    def __init__(self, key, model, budget, batch, batch_limit, input_price, output_price,
                 max_tokens=1024, interval=3.2, tools=None, input_limit=60000):
        if not 1 <= input_limit <= 160000 or (
                input_limit > 60000 and model != "openai/gpt-6-luna"):
            raise BudgetError("Input ceiling lacks a reviewed model contract")
        self.key, self.model, self.budget = key, model, budget
        self.batch, self.batch_limit = batch, batch_limit
        self.input_price, self.output_price = input_price, output_price
        self.max_tokens, self.interval = max_tokens, interval
        self.input_limit = input_limit
        self.tools = list(tools or [])
        self.last_request = 0.0
        self.calls = 0

    def generate(self, messages: list, final: bool = False):
        payload = {
            "model": self.model, "messages": messages, "tools": self.tools,
            "tool_choice": {"type": "function", "function": {"name": "submit"}}
            if final else "required",
            "max_tokens": self.max_tokens, "reasoning": {"enabled": False},
            "provider": {"only": [MODEL_ROUTES[self.model]], "allow_fallbacks": False,
                         "require_parameters": True,
                         "max_price": {"prompt": 0.2, "completion": 0.5}},
        }
        body = json.dumps(payload, ensure_ascii=True, allow_nan=False).encode()
        bound = len(body) + 4096
        if bound > self.input_limit:
            raise BudgetError("Context exceeds reviewed conservative input bound")
        reserve = bound * self.input_price + self.max_tokens * self.output_price
        request_id = uuid.uuid4().hex
        self.budget.reserve(request_id, self.batch, reserve, self.batch_limit)
        time.sleep(max(0, self.interval - (time.monotonic() - self.last_request)))
        self.last_request = time.monotonic()
        self.calls += 1
        request = Request("https://openrouter.ai/api/v1/chat/completions", data=body,
                          headers={"Authorization": f"Bearer {self.key}",
                                   "Content-Type": "application/json"})
        started = time.monotonic()
        try:
            with build_opener(NoRedirect()).open(request, timeout=90) as response:
                result = json.load(response)
        except Exception as exc:
            status = f"http_{exc.code}" if isinstance(exc, HTTPError) else type(exc).__name__
            self.budget.complete(request_id, "provider_error:" + status)
            raise AssertionError("unreachable") from None
        usage = result.get("usage", {})
        cost = usage.get("cost")
        valid_usage = all(type(usage.get(k)) is int and 0 <= usage[k] for k in
                          ("prompt_tokens", "completion_tokens", "total_tokens"))
        valid_usage = valid_usage and usage["prompt_tokens"] <= bound
        valid_usage = valid_usage and usage["completion_tokens"] <= self.max_tokens
        self.budget.complete(request_id, "ok" if valid_usage and cost is not None else
                             "unknown_or_excess_usage", cost, usage, result.get("id"))
        if not result.get("choices"):
            raise ValueError("Provider returned no choice")
        choice = result["choices"][0]
        raw = choice.get("message", {})
        # Public trace preserves the answer and function calls, not private reasoning.
        message = {k: raw[k] for k in ("role", "content", "tool_calls") if k in raw}
        return message, {
            "request_id": request_id, "response_id": result.get("id"),
            "model": result.get("model"), "provider": result.get("provider"),
            "usage": usage, "finish_reason": choice.get("finish_reason"),
            "native_finish_reason": choice.get("native_finish_reason"),
            "elapsed_seconds": round(time.monotonic() - started, 4),
            "input_bound": bound, "reserved_usd": str(reserve),
            "request_sha256": digest(body), "message": message,
        }


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
        if not 0 < limit <= KEY_LIMIT_CAP or remaining > limit or remaining < required:
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
    request = Request(
        "https://openrouter.ai/api/v1/key", headers={"Authorization": f"Bearer {key}"}
    )
    try:
        with build_opener(NoRedirect()).open(request, timeout=20) as response:
            data = json.load(response)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        raise BudgetError("OpenRouter key preflight failed; no paid requests dispatched") from None
    return validate_key_limits(data.get("data", {}), required)


def catalog(model):
    if model != "openai/gpt-6.1-sol":
        return model_catalog(model)
    row = next(m for m in get_json("https://openrouter.ai/api/v1/models")["data"]
               if m["id"] == model)
    rates = row["pricing"]
    input_price = max(money(rates.get(k, 0))
                      for k in ("prompt", "input_cache_write", "input_cache_write_1h"))
    output_price = money(rates["completion"])
    if (input_price > Decimal("0.0000025") or output_price > Decimal("0.00001")
            or money(rates.get("request", 0)) != 0):
        raise BudgetError("Stronger model exceeds reviewed standard-rate contract")
    return row, input_price, output_price


class ResponsesClient(Client):
    """Stateless provider endpoint; full native output items stay in the next request."""

    def __init__(self, *args, reasoning="medium", responses_input_limit=160000, **kwargs):
        super().__init__(*args, **kwargs)
        if responses_input_limit not in (160000, 256000):
            raise BudgetError("Unreviewed Responses input ceiling")
        if responses_input_limit > 160000 and self.model != "openai/gpt-6-luna":
            raise BudgetError("Expanded short-context contract reviewed only for Luna")
        self.history = []
        self.consumed = 0
        self.reasoning = reasoning
        self.responses_input_limit = responses_input_limit

    def payload(self, messages, final):
        if len(messages) == 2:
            self.history, self.consumed = [], 0
        for message in messages[self.consumed:]:
            if message["role"] == "tool":
                self.history.append({"type": "function_call_output",
                                     "call_id": message["tool_call_id"],
                                     "output": message["content"]})
            elif message["role"] in ("system", "user"):
                self.history.append({"role": message["role"], "content": message["content"]})
            else:
                raise ValueError("Native response history lost synchronization")
        self.consumed = len(messages) + 1  # runner appends the normalized assistant message
        return {
            "model": self.model, "input": list(self.history), "store": False,
            "tools": [{"type": "function", **t["function"], "strict": False}
                      for t in self.tools],
            "tool_choice": {"type": "function", "name": "submit"} if final else "required",
            "reasoning": {"effort": self.reasoning}, "max_output_tokens": self.max_tokens,
            "provider": {"only": ["openai"], "allow_fallbacks": False,
                         "require_parameters": True,
                         "max_price": {"prompt": float(self.input_price * 1000000),
                                       "completion": float(self.output_price * 1000000)}},
        }

    def generate(self, messages, final=False):
        body = json.dumps(self.payload(messages, final), ensure_ascii=True,
                          allow_nan=False).encode()
        bound = len(body) + 4096
        if bound > self.responses_input_limit:
            raise BudgetError(f"Responses input exceeds reviewed short-context ceiling: "
                              f"{bound} > {self.responses_input_limit}")
        reserve = bound * self.input_price + self.max_tokens * self.output_price
        request_id = uuid.uuid4().hex
        self.budget.reserve(request_id, self.batch, reserve, self.batch_limit)
        time.sleep(max(0, self.interval - (time.monotonic()-self.last_request)))
        self.last_request = time.monotonic()
        self.calls += 1
        request = Request("https://openrouter.ai/api/v1/responses", data=body,
                          headers={"Authorization": f"Bearer {self.key}",
                                   "Content-Type": "application/json"})
        started = time.monotonic()
        try:
            with build_opener(NoRedirect()).open(request, timeout=90) as response:
                result = json.load(response)
        except Exception as exc:
            status = f"http_{exc.code}" if isinstance(exc, HTTPError) else type(exc).__name__
            self.budget.complete(request_id, "provider_error:" + status)
            raise AssertionError("unreachable") from None
        usage = result.get("usage", {})
        inputs, outputs = usage.get("input_tokens"), usage.get("output_tokens")
        valid = (type(inputs) is int and type(outputs) is int
                 and 0 <= inputs <= bound and 0 <= outputs <= self.max_tokens)
        self.budget.complete(request_id, "ok" if valid and usage.get("cost") is not None
                             else "unknown_or_excess_usage", usage.get("cost"), usage,
                             result.get("id"))
        items = result.get("output", [])
        self.history.extend(items)
        calls = [{"id": item["call_id"], "type": "function",
                  "function": {"name": item["name"], "arguments": item["arguments"]}}
                 for item in items if item.get("type") == "function_call"]
        content = "\n".join(c.get("text", "") for item in items
                            if item.get("type") == "message" for c in item.get("content", []))
        message = {"role": "assistant", "content": content or None, "tool_calls": calls}
        finish = "tool_calls" if calls else "stop"
        if result.get("status") == "incomplete":
            finish = "length" if result.get("incomplete_details", {}).get("reason") in (
                "max_output_tokens", "length") else "incomplete"
        # Reasoning items are retained for the API in memory, but not published as private text.
        output_metadata = [{"type": item.get("type"), "id": item.get("id"),
                            "sha256": digest(json.dumps(item, sort_keys=True).encode())}
                           for item in items]
        return message, {
            "request_id": request_id, "response_id": result.get("id"),
            "model": result.get("model"), "provider": result.get("provider"),
            "api": "responses", "usage": usage, "finish_reason": finish,
            "native_finish_reason": result.get("status"),
            "elapsed_seconds": round(time.monotonic()-started, 4),
            "input_bound": bound, "reserved_usd": str(reserve),
            "request_sha256": digest(body), "output_metadata": output_metadata,
            "message": message,
        }
