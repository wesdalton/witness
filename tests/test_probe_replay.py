"""Probe replay measures executed programs separately from source inspection."""

from scripts.replay_portfolio_probes import extract


def test_extracts_literal_python_blocks_and_excludes_source_reads():
    command = "sed -n '1,3p' x.py\npython - <<'PY'\nprint('x')\nPY\ncat README.md"
    assert extract(command) == ["print('x')\n"]
    assert extract("cat implementation.py") == []
    assert extract("python - <<'PY'\nprint('incomplete')") == []


def test_preserves_multiple_blocks_without_executing_shell_or_python():
    command = 'python3 - <<"A"\nraise RuntimeError("do not execute on host")\nA\n'
    command += "python - <<B\nprint(2)\nB"
    assert extract(command) == ['raise RuntimeError("do not execute on host")\n', "print(2)\n"]
