import json

import pytest

from scripts.analyze_query_interfaces import analyze


def make_batch(folder):
    specs = []
    for i, mode in enumerate(("verdict", "program"), 1):
        spec = {"seed": 16001, "truth": False, "arm": "endorsement", "output_mode": mode}
        specs.append(spec)
        record = {
            "spec": spec, "status": "completed", "workspace_sha256": {"database": "same"},
            "initial_view": {"contract": "same", "peer_messages": ["same endorsement"]},
            "system_prompt": mode, "events": [],
            "metrics": {"correct_verdict": mode == "program",
                        "brier": 0.01 if mode == "program" else 0.81},
        }
        (folder / f"episode-{i:03}.json").write_text(json.dumps(record))
    (folder / "manifest.json").write_text(json.dumps({
        "episodes": specs,
        "output_interfaces": {m: {"system_prompt": m} for m in ("verdict", "program")},
    }))


def test_interface_contrast_direction_missingness_and_evidence_invariance(tmp_path):
    make_batch(tmp_path)
    result = analyze(tmp_path)
    comparison = next(c for c in result["output_requirement_contrasts"]
                      if c["peer_arm"] == "endorsement" and c["truth"] is False)
    assert comparison["accuracy_difference"]["difference"] == 1
    assert comparison["mean_brier_difference_program_minus_verdict"] == pytest.approx(-0.8)
    path = tmp_path / "episode-002.json"
    record = json.loads(path.read_text())
    record["status"] = "infrastructure_error"
    path.write_text(json.dumps(record))
    result = analyze(tmp_path)
    comparison = next(c for c in result["output_requirement_contrasts"]
                      if c["peer_arm"] == "endorsement" and c["truth"] is False)
    assert comparison["missing_seeds"] == [16001]
    assert comparison["accuracy_difference"] is None
    record["initial_view"]["contract"] = "changed"
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError, match="evidence"):
        analyze(tmp_path)
