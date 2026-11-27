import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

DEVICES_FILE = ROOT / "lab_data" / "devices.json"
HEADERS_FILE = ROOT / "lab_data" / "headers.conf"

DEFAULT_DEVICES = {
    "controllers": [
        {
            "id": "AK-800-001",
            "name": "Freezer 01",
            "ip": "192.168.1.101",
            "temperature": -18.5,
            "status": "normal",
            "online": True
        },
        {
            "id": "AK-800-002",
            "name": "Freezer 02",
            "ip": "192.168.1.102",
            "temperature": -22.1,
            "status": "normal",
            "online": True
        },
        {
            "id": "AK-800-003",
            "name": "Freezer 03",
            "ip": "192.168.1.103",
            "temperature": -5.2,
            "status": "warning",
            "online": True
        },
        {
            "id": "AK-800-004",
            "name": "Freezer 04",
            "ip": "192.168.1.104",
            "temperature": -16.8,
            "status": "normal",
            "online": True
        },
        {
            "id": "AK-800-005",
            "name": "Freezer 05",
            "ip": "192.168.1.105",
            "temperature": -2.4,
            "status": "critical",
            "online": True
        },
        {
            "id": "AK-800-006",
            "name": "Freezer 06",
            "ip": "192.168.1.106",
            "temperature": -20.3,
            "status": "normal",
            "online": True
        },
        {
            "id": "AK-800-007",
            "name": "Freezer 07",
            "ip": "192.168.1.107",
            "temperature": -8.7,
            "status": "warning",
            "online": True
        }
    ]
}

DEFAULT_HEADERS = """# Simulated NGINX headers configuration

add_header X-Frame-Options "SAMEORIGIN";
add_header X-Content-Type-Options "nosniff";
add_header X-Lab-Server "AK-SM-800A";
"""


def reset_devices():
    DEVICES_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(DEVICES_FILE, "w", encoding="utf-8") as file:
        json.dump(
            DEFAULT_DEVICES,
            file,
            indent=4,
            ensure_ascii=False
        )

    print("[OK] Controllers successfully reset.")
    print(f"[OK] File updated: {DEVICES_FILE}")


def reset_headers():
    HEADERS_FILE.parent.mkdir(parents=True, exist_ok=True)

    HEADERS_FILE.write_text(
        DEFAULT_HEADERS,
        encoding="utf-8"
    )

    print("[OK] NGINX headers configuration successfully reset.")
    print(f"[OK] File updated: {HEADERS_FILE}")


def main():
    reset_devices()
    reset_headers()

    print("\n[OK] Lab reset completed.")


if __name__ == "__main__":
    main()