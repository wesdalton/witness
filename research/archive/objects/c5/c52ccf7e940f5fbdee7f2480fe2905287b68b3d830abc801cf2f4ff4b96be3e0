"""Conservative replay evidence flags; these never certify semantic fault detection."""

import re


def signature(result):
    return result["exit_code"], result["stdout"], result["stderr"]


def normalized_signature(result):
    def clean(text):
        return re.sub(r"(<[^<>\n]*\b(?:object|function)\b[^<>\n]* at )0x[0-9a-fA-F]+(>)",
                      r"\1<address>\2", text)
    return result["exit_code"], clean(result["stdout"]), clean(result["stderr"])


def compare_replays(reference, variant):
    """Require repeated observations; preserve behavior changes alongside repr noise."""
    if len(reference) < 2 or len(variant) < 2:
        raise ValueError("Two fresh same-source executions required for each variant")
    comparable = not any(r["timed_out"] or r["output_truncated"] for r in reference + variant)
    raw_same_source_change = any(len({signature(r) for r in rs}) > 1
                                 for rs in (reference, variant))
    stable_normalized = all(len({normalized_signature(r) for r in rs}) == 1
                            for rs in (reference, variant))
    raw_difference = signature(reference[0]) != signature(variant[0])
    normalized_difference = normalized_signature(reference[0]) != normalized_signature(variant[0])
    return {
        "comparable": comparable,
        "raw_between_variant_difference": comparable and raw_difference,
        "raw_same_source_change": comparable and raw_same_source_change,
        "address_only_between_variant_difference": comparable and raw_difference
        and not normalized_difference,
        "repeatable_normalized_difference": comparable and stable_normalized
        and normalized_difference,
        "semantic_fault_detection": None,
        "semantic_review_required": True,
    }
