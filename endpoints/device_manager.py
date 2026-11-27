import json
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DEVICES_FILE = ROOT / "lab_data" / "devices.json"

DEFROST_TARGET = 50.0
DEFROST_RATE = 0.5  # Degrees Celsius per second


def save_devices(devices):
    with open(DEVICES_FILE, "w", encoding="utf-8") as file:
        json.dump(
            {"controllers": devices},
            file,
            indent=4
        )


def update_defrost_progress(devices):
    current_time = time.time()
    changed = False

    for device in devices:
        if device.get("status") != "defrosting":
            continue

        started_at = device.get("defrost_started_at")
        start_temperature = device.get("defrost_start_temperature")

        if started_at is None or start_temperature is None:
            continue

        elapsed = max(0, current_time - started_at)

        new_temperature = min(
            DEFROST_TARGET,
            start_temperature + elapsed * DEFROST_RATE
        )

        new_temperature = round(new_temperature, 1)

        if device.get("temperature") != new_temperature:
            device["temperature"] = new_temperature
            changed = True

        if new_temperature >= DEFROST_TARGET:
            device["status"] = "defrost_complete"
            device.pop("defrost_started_at", None)
            device.pop("defrost_start_temperature", None)
            changed = True

    if changed:
        save_devices(devices)

    return devices


def load_devices():
    with open(DEVICES_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    devices = data.get("controllers", [])

    return update_defrost_progress(devices)


def get_device(device_id):
    devices = load_devices()

    for device in devices:
        if device["id"] == device_id:
            return device

    return None


def update_temperature(device_id, temperature):
    devices = load_devices()

    for device in devices:
        if device["id"] == device_id:
            if device.get("status") == "defrosting":
                return False

            device["temperature"] = temperature

            if temperature > -5:
                device["status"] = "critical"
            elif temperature > -15:
                device["status"] = "warning"
            else:
                device["status"] = "normal"

            save_devices(devices)
            return True

    return False


def defrost_device(device_id):
    devices = load_devices()

    for device in devices:
        if device["id"] != device_id:
            continue

        if not device.get("online", False):
            return {
                "success": False,
                "message": "Controller is offline."
            }

        if device.get("status") == "defrosting":
            return {
                "success": False,
                "message": "Defrost is already running."
            }

        device["defrost_start_temperature"] = device["temperature"]
        device["defrost_started_at"] = time.time()
        device["status"] = "defrosting"

        save_devices(devices)

        return {
            "success": True,
            "message": f"Defrost started on {device_id}."
        }

    return {
        "success": False,
        "message": "Controller not found."
    }

