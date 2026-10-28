import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "repeatability", Path(__file__).resolve().parents[1] / "scripts/audit_replay_repeatability.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def test_normalization_removes_repr_addresses_without_erasing_payload_values():
    value = "<function probe at 0x123abc> <thing.NeedData object at 0x456def>"
    assert audit.normalize_repr(value) == (
        "<function probe at <address>> <thing.NeedData object at <address>>")
    payload = "actual=0x123abc expected=0x456def bytes=b'\\x12'"
    assert audit.normalize_repr(payload) == payload
