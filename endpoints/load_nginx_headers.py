import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEADERS_FILE = ROOT / "lab_data" / "headers.conf"

DEFAULT_CONFIG = """# Simulated NGINX headers configuration

add_header X-Frame-Options "SAMEORIGIN";
add_header X-Content-Type-Options "nosniff";
add_header X-Lab-Server "AK-SM-800A";
"""


def initialize_config():
    HEADERS_FILE.parent.mkdir(parents=True, exist_ok=True)

    if not HEADERS_FILE.exists():
        HEADERS_FILE.write_text(
            DEFAULT_CONFIG,
            encoding="utf-8"
        )


def load_nginx_headers():
    initialize_config()

    return HEADERS_FILE.read_text(encoding="utf-8")


def replace_nginx_headers(content):
    if not isinstance(content, str) or not content.strip():
        return {
            "success": False,
            "message": "Empty configuration rejected."
        }

    if len(content) > 65536:
        return {
            "success": False,
            "message": "Configuration exceeds the 64 KB limit."
        }

    initialize_config()

    HEADERS_FILE.write_text(
        content,
        encoding="utf-8"
    )

    routes = extract_simulated_routes(content)

    return {
        "success": True,
        "message": "Configuration successfully replaced.",
        "routes_detected": routes
    }


def extract_simulated_routes(content):
    """
    Recognizes exact-match location declarations.

    These routes are only simulated by the Python lab.
    They are never passed to a real NGINX process.
    """

    pattern = r"location\s*=\s*[\"']?([^\"'\s{]+)"

    return list(dict.fromkeys(
        re.findall(pattern, content)
    ))


def is_simulated_failure_route(path):
    """
    A route is considered a simulated failure route
    when its location block contains the lab marker.

    Marker:
        # LAB_SIMULATE_FAILURE
    """

    content = load_nginx_headers()

    blocks = re.finditer(
        r"location\s*=\s*[\"']?([^\"'\s{]+)[\"']?\s*\{(.*?)\}",
        content,
        re.DOTALL
    )

    for block in blocks:
        route = block.group(1)
        body = block.group(2)

        if (
            route == path
            and "# LAB_SIMULATE_FAILURE" in body
        ):
            return True

    return False