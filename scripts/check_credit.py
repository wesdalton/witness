"""Free credit check before a paid batch: account credit must cover the batch ceiling."""

import json
import sys
from decimal import Decimal
from pathlib import Path
from urllib.request import Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from swarm_lab.core.client import NoRedirect, load_key  # noqa: E402


def main() -> int:
    needed = Decimal(sys.argv[1])
    key = load_key(ROOT / ".env")
    request = Request("https://openrouter.ai/api/v1/credits",
                      headers={"Authorization": f"Bearer {key}"})
    with build_opener(NoRedirect()).open(request, timeout=20) as response:
        data = json.load(response)["data"]
    available = Decimal(str(data["total_credits"])) - Decimal(str(data["total_usage"]))
    print(json.dumps({"available_usd": str(available), "needed_usd": str(needed),
                      "ok": available >= needed}))
    return 0 if available >= needed else 1


if __name__ == "__main__":
    raise SystemExit(main())
