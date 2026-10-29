"""Probe replay measures executed programs separately from source inspection."""

from scripts.replay_portfolio_probes import extract
from swarm_lab.replay_observations import compare_replays


def test_extracts_literal_python_blocks_and_excludes_source_reads():
    command = "sed -n '1,3p' x.py\npython - <<'PY'\nprint('x')\nPY\ncat README.md"
    assert extract(command) == ["print('x')\n"]
    assert extract("cat implementation.py") == []
    assert extract("python - <<'PY'\nprint('incomplete')") == []


def test_preserves_multiple_blocks_without_executing_shell_or_python():
    command = 'python3 - <<"A"\nraise RuntimeError("do not execute on host")\nA\n'
    command += "python - <<B\nprint(2)\nB"
    assert extract(command) == ['raise RuntimeError("do not execute on host")\n', "print(2)\n"]


def execution(stdout, exit_code=0):
    return {"exit_code": exit_code, "stdout": stdout, "stderr": "",
            "timed_out": False, "output_truncated": False}


def test_address_only_difference_is_not_promoted_to_bug_detection():
    control = [execution(f"<NeedData object at 0x{i}>") for i in (111, 222)]
    buggy = [execution(f"<NeedData object at 0x{i}>") for i in (333, 444)]
    result = compare_replays(control, buggy)
    assert result["raw_same_source_change"]
    assert result["address_only_between_variant_difference"]
    assert not result["repeatable_normalized_difference"]
    assert result["semantic_fault_detection"] is None


def test_real_failure_text_survives_repr_noise_and_zero_exit():
    control = [execution("all passed\n")] * 2
    buggy = [execution(f"FAIL b'\\r' <function probe at 0x{i}> b''\n") for i in (111, 222)]
    result = compare_replays(control, buggy)
    assert result["raw_same_source_change"]
    assert not result["address_only_between_variant_difference"]
    assert result["repeatable_normalized_difference"]
    assert result["semantic_review_required"]


def test_source_dump_difference_still_requires_semantic_review():
    result = compare_replays([execution("def f(): return 1")] * 2,
                             [execution("def f(): return 2")] * 2)
    assert result["repeatable_normalized_difference"]
    assert result["semantic_fault_detection"] is None
