"""Closed study runners refuse paid dispatch before touching keys or output paths."""

import pytest

from swarm_lab.core.budget import BudgetError
from swarm_lab.legacy import CLOSED, agent_study, portfolio, query_study


@pytest.mark.parametrize("module, argv", [
    (agent_study, ["agent_study", "--live"]),
    (portfolio, ["portfolio", "--live", "--revision", "v2"]),
    (query_study, ["query_study", "--live"]),
])
def test_closed_runner_refuses_live_dispatch(tmp_path, monkeypatch, module, argv):
    output = tmp_path / "never-created"
    monkeypatch.setattr("sys.argv", [*argv, "--out", str(output)])
    monkeypatch.setattr(module, "load_key", lambda *a, **k: pytest.fail("key loaded"))
    with pytest.raises(BudgetError) as raised:
        module.main()
    assert str(raised.value) == CLOSED
    assert not output.exists()
