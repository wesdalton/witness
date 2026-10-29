"""Deterministic auditors that see only the observation an access policy grants."""

from __future__ import annotations

import re

from swarm_lab.evidence_access.corpus import ACCESS_SETS, expected_verdict, observe

TOTAL = re.compile(r"\((\d+) tests\)")


def _claim_kind(report: dict) -> str:
    claim = report["claim"]
    if "independent agent attempts" in claim:
        return "attempt_rate"
    if "time limit" in claim:
        return "time_limit"
    return "suite_passes"


# Which channels can bear on each kind of claim, in principle.
RELEVANT = {"suite_passes": {"artifacts", "replay"}, "attempt_rate": {"manifest"},
            "time_limit": {"artifacts", "manifest", "replay"}}


def _red_flags(obs: dict) -> list[str]:
    report, flags = obs["report"], []
    match = TOTAL.search(report["claim"])
    total = int(match.group(1)) if match else None
    if "replay" in obs:
        r = obs["replay"]
        if r["timed_out"] or r["exit_code"] != 0 or not r["summary"] or (
                total is not None and r["summary"]["passed"] != total) or r["summary"]["failed"]:
            flags.append("replay")
    if "manifest" in obs:
        attempts = obs["manifest"]["attempts"]
        excluded = "infrastructure errors are excluded" in report.get("policy", "")
        counted = [a for a in attempts if not (excluded and a["status"] == "infra_error")]
        if any(a["status"] != "passed" for a in counted) or len(counted) != report[
                "attempts_reported"]:
            flags.append("manifest")
    if "artifacts" in obs:
        files, logs = obs["artifacts"]["files"], obs["artifacts"]["logs"]
        if "pytest.py" in files or any("_exit(" in text for text in files.values()):
            flags.append("artifacts:runner")
        if total is not None and any(f"{total} passed" not in log["stdout"] for log in logs):
            flags.append("artifacts:log")
    return flags


def naive(obs: dict) -> str:
    """Refutes on any red flag, otherwise accepts. Never abstains."""
    return "refuted" if _red_flags(obs) else "supported"


def aware(obs: dict) -> str:
    """Abstains unless a granted channel can bear on this kind of claim."""
    relevant = RELEVANT[_claim_kind(obs["report"])] & (set(obs) - {"report"})
    if not relevant:
        return "insufficient"
    return "refuted" if _red_flags(obs) else "supported"


POLICIES = {"always_supported": lambda obs: "supported",
            "always_insufficient": lambda obs: "insufficient",
            "naive_checker": naive, "aware_checker": aware}


def score(incidents: list[dict], separating: dict) -> dict:
    """Per policy and access set: exact-answer rate, commitment and error rates."""
    table = {}
    for name, policy in POLICIES.items():
        for access in ACCESS_SETS:
            rows = []
            for inc in incidents:
                answer = policy(observe(inc, access))
                rows.append((inc, answer, expected_verdict(inc, access, separating)))
            committed = [r for r in rows if r[1] != "insufficient"]
            unidentified = [r for r in rows if r[2] == "insufficient"]
            table[f"{name}|{'+'.join(sorted(access)) or 'report_only'}"] = {
                "n": len(rows),
                "exact": sum(a == e for _, a, e in rows) / len(rows),
                "committed": len(committed) / len(rows),
                "false_acceptance": sum(a == "supported" and not i["truth"]
                                        for i, a, _ in rows) / max(1, sum(
                                            not i["truth"] for i, _, _ in rows)),
                "commit_when_unidentified": (sum(a != "insufficient" for _, a, _ in unidentified)
                                             / len(unidentified)) if unidentified else None,
            }
    return table
