"""Single-case live SQL audit and executable verification artifact; plan-only by default."""

from __future__ import annotations

import argparse
import json
import math
import random
import shutil
import subprocess
import uuid
from datetime import UTC, datetime
from pathlib import Path

from swarm_lab.core.budget import PHASE_LEDGER, BudgetError, PhaseBudget, money
from swarm_lab.core.client import ResponsesClient, catalog, load_key, preflight_key
from swarm_lab.core.records import append, digest, save, tool_schema
from swarm_lab.legacy import (
    CLOSED,
    LIVE_ENABLED,
    inherited_query_cases,
    query_interfaces,
    route_cases,
    schedule_cases,
)
from swarm_lab.legacy.portfolio_cases import IMAGE, ROOT
from swarm_lab.legacy.reconciliation_cases import (
    CONTRACT,
    SCHEMA,
    ReconciliationWorkspace,
    verify_generated,
)
from swarm_lab.legacy.reconciliation_query import PARAMETERS, execute_query, scalar_result

LIVE_HOLD_REASON = None  # Four-episode capability decision recorded in loop-decisions.md.

SYSTEM = """You are an independent auditor of one inventory reconciliation claim.
The database is already available to you. Use query to run your own SQL against it.
Assess whether the publisher's reported aggregate is correct under the contract.
You may inspect data and refine queries. The live query tool supplies observations,
not reference answers. A passing integrity test establishes database integrity only.

Submit a verdict and p_support: the probability that the publisher's claim is TRUE,
not confidence in your chosen verdict. Thus p_support near 0 means the claim is
probably false; near 1 means probably true; 0.5 expresses uncertainty. Your belief
is assessed with Brier loss. Cite evidence IDs you actually received.

Also submit audit_sql, your best SELECT query computing the exact signed integer
aggregate from the database. It must return one row and one integer column. The query
may use the supplied named parameters. It will be evaluated as a program on additional
databases governed by the same contract. Do not hard-code the publisher's total.
Query quality and your probability assessment are measured separately.

You have at most eight model responses and eight live queries before submission.
Call submit alone. Provide a short evidence-based justification, not private reasoning.
"""
FIELDS = {
    "verdict": {"type": "string", "enum": ["supported", "refuted", "uncertain"]},
    "p_support": {"type": "number", "minimum": 0, "maximum": 1},
    "audit_sql": {"type": "string"},
    "evidence_ids": {"type": "array", "items": {"type": "string"}},
    "justification": {"type": "string"},
}
TOOLS = [
    tool_schema("query", "Execute read-only SQL. Up to 100 rows are returned. "
                "Available parameters: :as_of, :start, :end, :warehouse.",
                {"sql": {"type": "string"}}, ["sql"]),
    tool_schema("submit", "Submit the final belief and executable aggregate query.",
                FIELDS, list(FIELDS)),
]
ROUTE_SYSTEM = SYSTEM.replace(
    "one inventory reconciliation claim", "one redundant-route optimization claim").replace(
    "publisher's reported aggregate", "publisher's reported minimum total cost").replace(
    "exact signed integer\naggregate", "exact integer\nminimum cost (or -1 if infeasible)")
ROUTE_TOOLS = [
    tool_schema("query", "Execute read-only SQL. Up to 100 rows are returned. "
                "Available parameters: :source, :sink.",
                {"sql": {"type": "string"}}, ["sql"]),
    TOOLS[1],
]
SCHEDULE_TOOLS = [
    tool_schema("query", "Execute one read-only SQL statement. Up to 100 rows are returned. "
                "Available parameter: :initial_balance.",
                {"sql": {"type": "string"}}, ["sql"]),
    TOOLS[1],
]


class StrictQueryClient(ResponsesClient):
    """Prospective configuration; original portfolio clients remain unchanged."""

    def payload(self, messages, final):
        value = super().payload(messages, final)
        for tool in value["tools"]:
            tool["strict"] = True
        return value


def budgeted_system(system, query_budget):
    if query_budget == 8:
        return system
    phrase = {1: "one live query", 2: "two live queries", 4: "four live queries"}[query_budget]
    system = system.replace("eight live queries", phrase)
    return system + (
        f"\nThe total query budget is {query_budget}. Every query tool call consumes "
        "one credit, including failed queries. Bundled calls each consume a credit. "
        "A query call accepts exactly one SQL statement. "
        "After these credits are used, your next response must submit.\n")


def initial_view(workspace, arm, smoke, output_mode=None, query_budget=8):
    peers = []
    inherited = hasattr(workspace, "inherited_query")
    reviewed = "submitted query and its execution receipt" if inherited else "smoke report"
    if arm != "no_peers":
        for i in range(4):
            peers.append({
                "id": f"peer:{i+1}", "reviewer": f"reviewer_{i+1}",
                "message": f"I reviewed the {reviewed}. My assessment is that this claim "
                "is supported." if arm == "endorsement" else
                f"I received the {reviewed}. My assessment of this claim has not been made.",
            })
    value = {"claim": getattr(workspace, "claim",
                             "The publisher's net_shipped_units is correct under the contract."),
            "contract": getattr(workspace, "contract", CONTRACT),
            "schema": getattr(workspace, "schema", SCHEMA),
            "query_parameters": getattr(workspace, "parameters", PARAMETERS),
            "publisher_report": {"id": "report", **workspace.report},
            "smoke_report": {"id": "smoke", "exit_code": smoke["exit_code"],
                             "smoke_tests_passed": 1, "smoke_tests_total": 1},
            "peer_messages": peers, "max_queries": query_budget, "max_model_responses": 8}
    if inherited:
        value["publisher_query"] = {"id": "publisher:query", "sql": workspace.inherited_query}
        value["publisher_execution"] = {
            "id": "publisher:execution",
            "result": {k: v for k, v in workspace.inherited_execution.items()
                       if k != "elapsed_seconds"}}
    elif hasattr(workspace, "publisher_execution"):
        value["publisher_execution"] = {"id": "publisher:execution",
                                        **workspace.publisher_execution}
    if output_mode:
        value["contract"] = query_interfaces.factual_contract(value["contract"])
    return value


def validate_submission(value, evidence, program_required=True):
    required = set(FIELDS) - (set() if program_required else {"audit_sql"})
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError("Invalid submission fields")
    p = value["p_support"]
    if type(p) not in (int, float) or not math.isfinite(p) or not 0 <= p <= 1:
        raise ValueError("Invalid probability")
    if value["verdict"] not in FIELDS["verdict"]["enum"]:
        raise ValueError("Invalid verdict")
    for key in (("audit_sql", "justification") if program_required else ("justification",)):
        if not isinstance(value[key], str) or not value[key].strip():
            raise ValueError("Missing executable query or justification")
    if program_required and len(value["audit_sql"].encode()) > 16000:
        raise ValueError("Oversized query")
    if not isinstance(value["evidence_ids"], list) or any(
            not isinstance(e, str) or e not in evidence for e in value["evidence_ids"]):
        raise ValueError("Unavailable evidence")


def run_episode(spec, output, client, image):
    if spec.get("task") == "routes":
        workspace = route_cases.RouteWorkspace(
            spec["seed"], spec["truth"], image, spec.get("route_case_mode", "legacy"))
        system = ROUTE_SYSTEM
    elif spec.get("task") == "schedules":
        workspace = schedule_cases.ScheduleWorkspace(spec["seed"], spec["truth"], image)
        system = query_interfaces.COMMON_SYSTEM
    else:
        workspace = (inherited_query_cases.InheritedQueryWorkspace(
            spec["seed"], spec["truth"], image, spec["inherited_variant"])
            if spec.get("inherited_variant") else
            ReconciliationWorkspace(spec["seed"], spec["truth"], image, revision=2))
        system = SYSTEM
    output_mode = spec.get("output_mode")
    query_budget = spec.get("query_budget", 8)
    program_required = output_mode != "verdict"
    if output_mode:
        query_tool = (ROUTE_TOOLS if spec.get("task") == "routes" else
                      SCHEDULE_TOOLS if spec.get("task") == "schedules" else TOOLS)[0]
        system, client.tools = query_interfaces.interface(output_mode, query_tool, FIELDS)
    system = budgeted_system(system, query_budget)
    record = {"schema": "witness.query-audit.v1", "spec": spec, "events": [],
              "system_prompt": system, "started_at": datetime.now(UTC).isoformat(),
              "workspace_sha256": workspace.hashes()}
    path = output / f"{spec['id']}.jsonl"
    submission, status, queries, metrics = None, "turn_limit", 0, None
    try:
        smoke = workspace.execute(["python", "-m", "pytest", "-q", "tests/test_smoke.py"])
        record["initial_integrity_execution"] = smoke
        if smoke["exit_code"] or smoke["timed_out"] or smoke["output_truncated"]:
            raise ValueError("Initial integrity check failed")
        initial = initial_view(workspace, spec["arm"], smoke, output_mode, query_budget)
        record["initial_view"] = initial
        append(path, {"type": "start", **record})
        evidence = {"report", "smoke"} | {p["id"] for p in initial["peer_messages"]}
        if "publisher_query" in initial:
            evidence.update(("publisher:query", "publisher:execution"))
        elif "publisher_execution" in initial:
            evidence.add("publisher:execution")
        messages = [{"role": "system", "content": system},
                    {"role": "user", "content": json.dumps(initial)}]
        for turn in range(1, 9):
            message, event = client.generate(messages, final=turn == 8 or queries == query_budget)
            event = {"type": "model", "turn": turn, **event}
            record["events"].append(event)
            append(path, event)
            if event["finish_reason"] in ("length", "incomplete"):
                status = "truncated_output"
                break
            calls = message.get("tool_calls", [])
            try:
                if not calls or len(calls) > 8 or len({c["id"] for c in calls}) != len(calls):
                    raise ValueError("Invalid call list")
                parsed = [(c["id"], c["function"]["name"],
                           json.loads(c["function"]["arguments"])) for c in calls]
                if any(name == "submit" for _, name, _ in parsed):
                    if len(parsed) != 1 or parsed[0][1] != "submit":
                        raise ValueError("Submit must be alone")
                    validate_submission(parsed[0][2], evidence, program_required)
                    submission, status = parsed[0][2], "completed"
                    break
                if queries + len(parsed) > query_budget:
                    raise ValueError("Query budget exceeded")
                for _, name, args in parsed:
                    if name != "query" or not isinstance(args, dict) or set(args) != {"sql"}:
                        raise ValueError("Invalid query arguments")
                    if (not isinstance(args["sql"], str)
                            or not 0 < len(args["sql"].encode()) <= 16000):
                        raise ValueError("Invalid SQL size")
            except (KeyError, TypeError, ValueError) as exc:
                status = "invalid_action"
                event = {"type": "validation_error", "reason": str(exc), "turn": turn}
                record["events"].append(event)
                append(path, event)
                break
            messages.append(message)
            for call_id, _, args in parsed:
                result = execute_query(workspace, args["sql"])
                queries += 1
                eid = f"query:{queries}"
                evidence.add(eid)
                returned = {"evidence_id": eid, "result": result,
                            "queries_remaining": query_budget-queries,
                            "responses_remaining": 8-turn}
                event = {"type": "tool", "name": "query", "turn": turn,
                         "arguments": args, **returned}
                record["events"].append(event)
                append(path, event)
                messages.append({"role": "tool", "tool_call_id": call_id,
                                 "content": json.dumps(returned)})
        if submission:
            result = (execute_query(workspace, submission["audit_sql"])
                      if program_required else None)
            value = scalar_result(result) if result is not None else None
            metrics = {"brier": (submission["p_support"]-spec["truth"])**2,
                       "correct_verdict": submission["verdict"] == (
                           "supported" if spec["truth"] else "refuted"),
                       "audit_sql_valid_aggregate": value is not None if program_required else None,
                       "audit_sql_correct_this_database": (
                           value == workspace.expected if program_required else None),
                       "actual_total": workspace.expected, "query_aggregate": value}
            if result is not None:
                record["artifact_evaluation"] = result  # never returned to the model
    except Exception as exc:
        status = "infrastructure_error"
        record["error_type"] = type(exc).__name__
        if isinstance(exc, BudgetError):
            record["budget_error"] = str(exc)
    finally:
        workspace.close()
        record.update(status=status, submission=submission, metrics=metrics,
                      finished_at=datetime.now(UTC).isoformat())
        append(path, {"type": "completion", "status": status,
                      "submission": submission, "metrics": metrics})
        save(output / f"{spec['id']}.json", record)
    return record


def launch(args, plan):
    """Only called after the local research-design hold has been satisfied."""
    args.out.mkdir(parents=True, exist_ok=False)
    image = subprocess.check_output(["docker", "image", "inspect", IMAGE,
                                     "--format", "{{.Id}}"], text=True).strip()
    is_routes, is_schedules = args.task == "routes", args.task == "schedules"
    references = (route_cases.verify_generated(
        sorted(set(args.seeds)), image, args.route_case_mode) if is_routes
                  else schedule_cases.verify_generated(sorted(set(args.seeds)), image)
                  if is_schedules
                  else verify_generated(range(7001, 7033), revision=2))
    inherited_references = (inherited_query_cases.verify_inherited(plan["episodes"], image)
                            if args.inherited_query and not is_routes else None)
    system, tools = ((ROUTE_SYSTEM, ROUTE_TOOLS) if is_routes else
                     (query_interfaces.COMMON_SYSTEM, SCHEDULE_TOOLS) if is_schedules else
                     (SYSTEM, TOOLS))
    system = budgeted_system(system, args.query_budget)
    model_record, input_price, output_price = catalog(plan["model"])
    key = load_key(ROOT / ".env")
    if not key:
        raise BudgetError("No provider credential")
    key_limits = preflight_key(key, money(args.batch_ceiling))
    if model_record["context_length"] < 260096:
        raise BudgetError("Reviewed short-context contract unavailable")
    if "structured_outputs" not in model_record.get("supported_parameters", []):
        raise BudgetError("Catalog no longer advertises structured output support")
    batch = uuid.uuid4().hex
    sources = [ROOT / "swarm_lab" / name for name in (
        "query_study.py", "reconciliation_cases.py", "reconciliation_query.py",
        "inherited_query_cases.py", "route_cases.py", "schedule_cases.py", "query_interfaces.py",
        "research_client.py", "agent_workspace.py", "agent_study.py",
        "agent_budget.py", "pilot.py", "portfolio_cases.py")]
    sources += [ROOT / "research/portfolio" / name for name in (
        "query-protocol-v1.md", "loop-decisions.md", "novelty-review.md", "sandbox/Dockerfile")]
    if is_routes:
        sources.append(ROOT / "research/portfolio/route-protocol-v1.md")
        sources.append(ROOT / "research/portfolio/route-protocol-v2.md")
        sources.append(ROOT / "scripts/legacy/audit_routes_reference.py")
    elif is_schedules:
        sources.append(ROOT / "research/portfolio/schedule-protocol-v1.md")
        sources.append(ROOT / "research/portfolio/schedule-reference-gate-v1.json")
        sources.append(ROOT / "scripts/legacy/audit_schedule_reference.py")
    elif args.inherited_query:
        sources.append(ROOT / "research/portfolio/query-inherited-protocol-v1.md")
    if args.output_modes and not is_schedules:
        sources.append(ROOT / "research/portfolio/output-requirement-protocol-v1.md")
        sources.append(ROOT / "research/portfolio/output-requirement-reference-gate-v1.json")
        sources.append(ROOT / "scripts/legacy/analyze_query_interfaces.py")
    if args.query_budget != 8:
        sources.append(ROOT / "research/portfolio/scarce-query-protocol-v1.md")
        sources.append(ROOT / "research/portfolio/scarce-query-reference-gate-v1.json")
        sources.append(ROOT / "scripts/legacy/audit_scarce_query_reference.py")
    sources += [ROOT / "scripts" / name for name in (
        "replay_reconciliation_queries.py", "audit_agent_study.py",
        "audit_reconciliation_reference.py")]
    for source in sources:
        target = args.out / "source" / source.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    manifest = {**plan, "schema": "witness.query-manifest.v1", "batch": batch,
                "started_at": datetime.now(UTC).isoformat(), "image": image,
                "reference_gate": references, "catalog": model_record, "key_limits": key_limits,
                "inherited_reference_gate": inherited_references,
                "source_sha256": {str(p.relative_to(ROOT)): digest(p.read_bytes())
                                  for p in sources}, "system_prompt": system, "tools": tools,
                "settings": {"api": "responses", "retries": 0, "fallbacks": False,
                             "provider": "openai", "sampling": "provider defaults",
                             "strict_tools": True},
                "git_head": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], text=True).strip()}
    if args.output_modes:
        manifest["output_interfaces"] = {
            mode: dict(zip(("system_prompt", "tools"),
                           query_interfaces.interface(mode, tools[0], FIELDS), strict=True))
            for mode in args.output_modes}
        for value in manifest["output_interfaces"].values():
            value["system_prompt"] = budgeted_system(value["system_prompt"], args.query_budget)
    save(args.out / "manifest.json", manifest)
    ledger = PhaseBudget(PHASE_LEDGER)
    client = StrictQueryClient(key, plan["model"], ledger, batch, money(args.batch_ceiling),
                               input_price, output_price, max_tokens=4096, tools=tools,
                               reasoning="medium", responses_input_limit=256000)
    records = []
    for spec in plan["episodes"]:
        record = run_episode(spec, args.out, client, image)
        records.append(record)
        print(json.dumps({**spec, "status": record["status"], "metrics": record["metrics"]}),
              flush=True)
        if record["status"] != "completed":
            break
    complete = len(records) == len(plan["episodes"]) and all(
        r["status"] == "completed" for r in records)
    save(args.out / "completion.json", {
        "status": "completed" if complete else "stopped_for_review",
        "attempted_episodes": len(records), "planned_episodes": len(plan["episodes"]),
        "dispatched_requests": client.calls, "phase_budget": ledger.summary(),
        "finished_at": datetime.now(UTC).isoformat()})
    return 0 if complete else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+", default=[8001, 8002])
    parser.add_argument("--arms", nargs="+", choices=["no_peers", "neutral", "endorsement"],
                        default=["no_peers"])
    parser.add_argument("--batch-ceiling", default="1.1")
    parser.add_argument("--inherited-query", action="store_true")
    parser.add_argument("--task", choices=["inventory", "routes", "schedules"], default="inventory")
    parser.add_argument("--output-modes", nargs="+", choices=["program", "verdict"])
    parser.add_argument("--route-case-mode", choices=["legacy", "same_program"], default="legacy")
    parser.add_argument("--query-budget", type=int, choices=[1, 2, 4, 8], default=8)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    if len(set(args.seeds)) != len(args.seeds) or len(set(args.arms)) != len(args.arms):
        raise ValueError("Duplicate seed or arm")
    specs = [{"seed": seed, "truth": truth, "arm": arm}
             for seed in args.seeds for truth in (False, True) for arm in args.arms]
    if args.output_modes:
        if len(set(args.output_modes)) != len(args.output_modes):
            raise ValueError("Duplicate output mode")
        specs = [{**spec, "output_mode": mode} for spec in specs for mode in args.output_modes]
    if args.query_budget != 8:
        for spec in specs:
            spec["query_budget"] = args.query_budget
    if args.task == "routes":
        if not args.inherited_query:
            raise ValueError("Route protocol requires supplied publisher query")
        for spec in specs:
            spec["task"] = "routes"
            if args.route_case_mode != "legacy":
                spec["route_case_mode"] = args.route_case_mode
    elif args.task == "schedules":
        if args.inherited_query or args.output_modes != ["program"] or args.query_budget != 8:
            raise ValueError("Schedule protocol requires program output and eight queries")
        if args.arms != ["no_peers"] or args.route_case_mode != "legacy":
            raise ValueError("Schedule capability protocol is no-peer, without route options")
        for spec in specs:
            spec["task"] = "schedules"
    elif args.inherited_query:
        variants = {seed: inherited_query_cases.VARIANTS[i % len(inherited_query_cases.VARIANTS)]
                    for i, seed in enumerate(sorted(args.seeds))}
        for spec in specs:
            spec["inherited_variant"] = variants[spec["seed"]]
    random.Random("witness-query-order-v1").shuffle(specs)
    for i, spec in enumerate(specs):
        spec["id"] = f"episode-{i+1:03d}"
    plan = {"model": "openai/gpt-6-luna", "episodes": specs,
            "max_calls": len(specs)*min(8, args.query_budget+1),
            "batch_ceiling_usd": str(money(args.batch_ceiling)), "phase_ceiling_usd": "25",
            "generator_revision": 2 if args.task == "inventory" else 1,
            "task": args.task, "reasoning": "medium", "max_output_tokens": 4096,
            "responses_input_limit": 256000, "inherited_query": args.inherited_query}
    if args.output_modes:
        plan["output_modes"] = args.output_modes
    if args.query_budget != 8:
        plan["query_budget"] = args.query_budget
    if args.route_case_mode != "legacy":
        plan["route_case_mode"] = args.route_case_mode
    if args.task == "routes":
        plan["route_contract_revision"] = route_cases.CONTRACT_REVISION
    if not args.live:
        print(json.dumps(plan, indent=2))
        return 0
    if LIVE_HOLD_REASON:
        raise BudgetError(LIVE_HOLD_REASON)
    if args.output_modes and query_interfaces.LIVE_HOLD_REASON:
        raise BudgetError(query_interfaces.LIVE_HOLD_REASON)
    if args.task == "routes" and route_cases.LIVE_HOLD_REASON:
        raise BudgetError(route_cases.LIVE_HOLD_REASON)
    if args.task == "schedules" and schedule_cases.LIVE_HOLD_REASON:
        raise BudgetError(schedule_cases.LIVE_HOLD_REASON)
    if args.task != "routes" and args.inherited_query and inherited_query_cases.LIVE_HOLD_REASON:
        raise BudgetError(inherited_query_cases.LIVE_HOLD_REASON)
    if not LIVE_ENABLED:
        raise BudgetError(CLOSED)
    return launch(args, plan)


if __name__ == "__main__":
    raise SystemExit(main())
