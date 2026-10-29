"""Prospective output-requirement intervention; legacy query prompts are preserved."""

from swarm_lab.core.records import tool_schema

LIVE_HOLD_REASON = None  # Frozen 32-episode decision in output-requirement-protocol-v1.md.
COMMON_SYSTEM = """You are an independent auditor of one claim.
The source database is available through the live query tool. Assess whether the
publisher's reported value is correct under the supplied contract. You may inspect
data and run queries before deciding. A passing integrity test establishes database
integrity only. A publisher execution receipt establishes what its program returned.

Submit a verdict and p_support: the probability that the publisher's claim is TRUE,
not confidence in your chosen verdict. Near 0 means probably false, near 1 means
probably true, and 0.5 expresses uncertainty. Your belief is assessed with Brier
loss. Cite evidence IDs you actually received and give a short evidence-based
justification, not private reasoning.

You have at most eight model responses and eight live queries before submission.
Call submit alone.
"""
PROGRAM_PARAGRAPH = """
Also submit audit_sql, your best SELECT query computing the exact integer value
required by the contract. It must return one row and one integer column. Use the
supplied named parameters when appropriate. The unchanged query will be evaluated
on additional databases governed by the same contract. Do not hard-code the
publisher's value. Program quality and your probability assessment are measured
separately.
"""


def interface(mode, query_tool, fields):
    if mode not in ("program", "verdict"):
        raise ValueError("Unknown output-requirement condition")
    system = COMMON_SYSTEM + (PROGRAM_PARAGRAPH if mode == "program" else "")
    selected = {k: v for k, v in fields.items() if k != "audit_sql" or mode == "program"}
    tools = [query_tool, tool_schema(
        "submit", "Submit the final belief" + (
            " and executable verification query." if mode == "program" else "."),
        selected, list(selected))]
    return system, tools


def factual_contract(contract):
    """Remove only the route v1 output instruction, identically in both new modes."""
    marker = " Construct\nyour own final audit_sql"
    return contract.split(marker, 1)[0].rstrip() + "\n" if marker in contract else contract
