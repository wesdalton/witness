"""Bounded Responses API adapter for the stronger-model difficulty calibration."""

from __future__ import annotations

import json
import time
import uuid
from decimal import Decimal
from urllib.error import HTTPError
from urllib.request import Request, build_opener

from swarm_lab.agent_study import Client, NoRedirect, digest, get_json, model_catalog
from swarm_lab.pilot import BudgetError, money


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
