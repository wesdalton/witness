"""Matched-portfolio analysis with conservative exact intervals; no inference."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


def tail(n, x, p, upper):
    values = range(x, n+1) if upper else range(x+1)
    return sum(math.comb(n, k)*p**k*(1-p)**(n-k) for k in values)


def binomial_interval(x, n, alpha=0.05):
    """Clopper-Pearson inversion, with exact boundary formulas."""
    if not 0 <= x <= n or n == 0:
        raise ValueError("Invalid binomial counts")
    lower = 0.0
    if x:
        lo, hi = 0.0, 1.0
        for _ in range(60):
            mid = (lo+hi)/2
            if tail(n, x, mid, True) < alpha/2:
                lo = mid
            else:
                hi = mid
        lower = (lo+hi)/2
    upper = 1.0
    if x < n:
        lo, hi = 0.0, 1.0
        for _ in range(60):
            mid = (lo+hi)/2
            if tail(n, x, mid, False) > alpha/2:
                lo = mid
            else:
                hi = mid
        upper = (lo+hi)/2
    return lower, upper


def paired_binary(differences):
    n = len(differences)
    if not n or any(x not in (-1, 0, 1) for x in differences):
        raise ValueError("Expected paired differences in {-1,0,1}")
    plus, minus = differences.count(1), differences.count(-1)
    pplus = binomial_interval(plus, n, 0.025)
    pminus = binomial_interval(minus, n, 0.025)
    discordant = plus + minus
    pvalue = min(1.0, 2*sum(math.comb(discordant, k)
                            for k in range(min(plus, minus)+1))/2**discordant)
    return {
        "pairs": n, "right_only": plus, "left_only": minus,
        "equal": n-discordant, "difference": (plus-minus)/n,
        "difference_ci95_conservative_exact": [pplus[0]-pminus[1], pplus[1]-pminus[0]],
        "exact_paired_sign_p": pvalue,
        "interval_method": "Bonferroni-combined 97.5% Clopper-Pearson intervals "
                           "for the two discordant-cell probabilities",
    }


def observed_allocation(episode):
    if not episode:
        return None
    opened = {e["claim_id"] for e in episode["events"] if e["type"] == "tool"}
    if episode["portfolio"]["target"] in opened:
        return True
    if episode["status"] == "completed" or len(opened) == episode["spec"]["budget"]:
        return False
    return None


def analyze(folder, left="neutral", right="endorsement", continuation=None):
    manifest = json.loads((folder / "manifest.json").read_text())
    episodes = [json.loads(p.read_text()) for p in sorted(folder.glob("episode-*.json"))]
    continuations = ([continuation] if isinstance(continuation, Path) else continuation) or []
    previous_folder, previous_manifest = folder, manifest
    input_limits = [manifest.get("responses_input_limit", 160000)]
    for continued_folder in continuations:
        extra = json.loads((continued_folder / "manifest.json").read_text())
        parent_hash = hashlib.sha256(
            (previous_folder / "manifest.json").read_bytes()).hexdigest()
        if extra["continuation_manifest_sha256"] != parent_hash:
            raise ValueError("Continuation does not link the preceding manifest")
        original_specs = {s["id"]: s for s in previous_manifest["episodes"]}
        attempted_ids = {e["spec"]["id"] for e in episodes}
        if any(s != original_specs.get(s["id"]) or s["id"] in attempted_ids
               for s in extra["episodes"]):
            raise ValueError("Continuation retries or changes an original spec")
        if any(extra[k] != manifest[k] for k in ("model", "reasoning", "max_output_tokens")):
            raise ValueError("Continuation changes model generation configuration")
        episodes += [json.loads(p.read_text())
                     for p in sorted(continued_folder.glob("episode-*.json"))]
        previous_folder, previous_manifest = continued_folder, extra
        input_limits.append(extra["responses_input_limit"])
    by_key = {(e["spec"]["seed"], e["spec"]["arm"]): e for e in episodes}
    if len(by_key) != len(episodes):
        raise ValueError("Duplicate seed/arm; analyze configurations separately")
    planned = {e["seed"] for e in manifest["episodes"] if e["arm"] in (left, right)}
    pairs, missing, observable = [], [], []
    for seed in sorted(planned):
        a, b = by_key.get((seed, left)), by_key.get((seed, right))
        if a and b and a["portfolio"] != b["portfolio"]:
            raise ValueError("Unmatched portfolio")
        selected_a, selected_b = observed_allocation(a), observed_allocation(b)
        if selected_a is not None and selected_b is not None:
            observable.append(int(selected_b)-int(selected_a))
        if not a or not b or a["status"] != "completed" or b["status"] != "completed":
            missing.append(seed)
            continue
        if a["portfolio"] != b["portfolio"] or a["system_prompt"] != b["system_prompt"]:
            raise ValueError("Unmatched portfolio or system instructions")
        if a["initial_view"]["claims"] != b["initial_view"]["claims"]:
            raise ValueError("Claim evidence differs across arms")
        if a["spec"]["budget"] != b["spec"]["budget"]:
            raise ValueError("Investigation budgets differ across arms")
        target = a["portfolio"]["target"]
        target_case = next(c for c in a["portfolio"]["cases"] if c["id"] == target)
        pairs.append({
            "seed": seed, "target": target, "family": target_case["family"],
            "truth": target_case["truth"], "variant": target_case.get("variant"),
            "left_selected": a["metrics"]["target_investigated"],
            "right_selected": b["metrics"]["target_investigated"],
            "selection_difference": int(b["metrics"]["target_investigated"])
            - int(a["metrics"]["target_investigated"]),
            "brier_difference": b["metrics"]["brier"] - a["metrics"]["brier"],
        })
    result = {"schema": "witness.portfolio-paired.v1", "batch": folder.name,
              "model": manifest["model"], "left": left, "right": right,
              "planned_pairs": len(planned), "attempted_episodes": len(episodes),
              "missing_or_incomplete_pairs": missing, "pairs": pairs,
              "interpretation": "Portfolio seeds vary a small fixed source corpus. "
                                "They are not independent repository samples. "
                                "Pilot/adaptive contrasts remain exploratory."}
    if pairs:
        result["target_selection"] = paired_binary([p["selection_difference"] for p in pairs])
        result["mean_brier_difference"] = sum(p["brier_difference"] for p in pairs)/len(pairs)
        result["right_minus_left"] = True
    if continuations:
        result["continuations"] = [p.name for p in continuations]
        result["input_ceilings_by_batch"] = input_limits
        if observable:
            result["posthoc_observable_allocation_sensitivity"] = {
                **paired_binary(observable),
                "interpretation": "Separate sensitivity analysis added after infrastructure "
                "review. Includes incomplete episodes only when target access already "
                "occurred or all investigation credits were spent. No missing verdict imputed."}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--left", default="neutral")
    parser.add_argument("--right", default="endorsement")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--continuation", type=Path, nargs="+")
    args = parser.parse_args()
    result = analyze(args.folder, args.left, args.right, args.continuation)
    text = json.dumps(result, indent=2) + "\n"
    if args.out:
        with args.out.open("x") as stream:
            stream.write(text)
    print(text)


if __name__ == "__main__":
    main()
