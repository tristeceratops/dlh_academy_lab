import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, parse_qs


ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = ROOT / "logs"
LOG_FILE = LOG_DIR / "http_requests.jsonl"


def log_request(method, request_path, status, parameter_names=None):
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    parsed = urlsplit(request_path)

    query_parameters = parse_qs(
        parsed.query,
        keep_blank_values=True
    )

    names = set(query_parameters.keys())

    if parameter_names:
        names.update(parameter_names)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "method": method,
        "path": parsed.path,
        "parameter_names": sorted(names),
        "status": status
    }

    with LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(entry) + "\n")