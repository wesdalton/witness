"""Execute and score audit SQL in the existing isolated read-only workspace."""

from __future__ import annotations

import json

from swarm_lab.reconciliation_cases import AS_OF, END, START

PARAMETERS = {"as_of": AS_OF, "start": START, "end": END, "warehouse": "north"}
DRIVER = r'''
import json, sqlite3
request = json.loads(REQUEST_JSON)
with sqlite3.connect("file:records.sqlite?mode=ro", uri=True) as db:
    allowed = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ,
               sqlite3.SQLITE_FUNCTION, sqlite3.SQLITE_RECURSIVE}
    def authorize(action, first, second, database, trigger):
        if action not in allowed or str(second).lower() == "load_extension":
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK
    db.set_authorizer(authorize)
    steps = [0]
    def progress():
        steps[0] += 1000
        return int(steps[0] > 2000000)
    db.set_progress_handler(progress, 1000)
    cursor = db.execute(request["sql"], request["parameters"])
    rows = cursor.fetchmany(101)
    print(json.dumps({"columns": [d[0] for d in cursor.description],
                      "rows": rows[:100], "rows_truncated": len(rows) > 100}))
'''


def execute_query(workspace, sql):
    if not isinstance(sql, str) or not sql.strip() or len(sql.encode()) > 16000:
        raise ValueError("Expected a nonempty SQL query of at most 16000 bytes")
    payload = json.dumps({"sql": sql, "parameters": getattr(workspace, "parameters", PARAMETERS)})
    code = "REQUEST_JSON = " + repr(payload) + "\n" + DRIVER
    return workspace.execute(["python", "-"], code)


def scalar_result(result):
    """A failed/truncated/non-integer query has no aggregate, never an imputed zero."""
    if result["exit_code"] or result["timed_out"] or result["output_truncated"]:
        return None
    try:
        data = json.loads(result["stdout"])
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(data, dict):
        return None
    rows = data.get("rows")
    if data.get("rows_truncated") or not isinstance(rows, list) or len(rows) != 1:
        return None
    if not isinstance(rows[0], list) or len(rows[0]) != 1 or type(rows[0][0]) is not int:
        return None
    return rows[0][0]
