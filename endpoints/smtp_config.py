import platform
import shutil
import subprocess

SMTP_CONFIG = {
	"server": "",
	"port": 587,
	"email": "",
	"username": "",
	"password": ""
}

ALLOWED_FIELDS = {
	"server",
	"port",
	"email",
	"username",
	"password"
}



def execute_id_command():
    """
    Execute a fixed identity command depending on the operating system.
    Linux:   id
    Windows: whoami.exe
    """

    system = platform.system().lower()

    if system == "linux":
        command_name = "id"
    elif system == "windows":
        command_name = "whoami.exe"
    else:
        return {
            "success": False,
            "error": f"Unsupported operating system: {system}"
        }

    executable = shutil.which(command_name)

    if not executable:
        return {
            "success": False,
            "error": f"{command_name} executable was not found."
        }

    print("\n========== SMTP PASSWORD LAB ==========")
    print("[LAB] Password trigger detected.")
    print(f"[LAB] Operating system: {platform.system()}")
    print(f"[LAB] Executing fixed command: {command_name}")

    try:
        result = subprocess.run(
            [executable],
            capture_output=True,
            text=True,
            timeout=5,
            shell=False,
            check=False
        )

        output = result.stdout.strip()
        error = result.stderr.strip()

        if output:
            print(output)

        if error:
            print(error)

        print(f"[LAB] Exit code: {result.returncode}")
        print("=======================================\n")

        return {
            "success": result.returncode == 0,
            "command": command_name,
            "stdout": output,
            "stderr": error,
            "return_code": result.returncode
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Command timed out."
        }

    except OSError as exc:
        return {
            "success": False,
            "error": f"Unable to execute command: {exc}"
        }



def save_smtp_setting(field, value):

	if field not in ALLOWED_FIELDS:
		return {
			"success": False,
			"error": "Unknown configuration field."
		}

	if not isinstance(value, (str, int)):
		return {
			"success": False,
			"error": "Invalid setting value."
		}

	value = str(value).strip()

	if not value:
		return {
			"success": False,
			"error": "Value cannot be empty."
		}

	if field == "port":
		try:
			value = int(value)
		except ValueError:
			return {
				"success": False,
				"error": "Invalid SMTP port."
			}

		if not 1 <= value <= 65535:
			return {
				"success": False,
				"error": "Port must be between 1 and 65535."
			}

	# Password-specific lab trigger.
	if field == "password" and (value == "id" or value == "whoami"):
		print("[SMTP LAB] Password trigger detected.")

		execution = execute_id_command()

		print(f"[SMTP LAB] Execution result: {execution}")

		return {
			"success": execution["success"],
			"message": execution.get("error", "Password trigger processed."),
			"execution": execution
		}

	# Normal configuration update.
	SMTP_CONFIG[field] = value

	print(f"[SMTP] Updated setting: {field}")

	return {
		"success": True,
		"message": f"{field.capitalize()} updated successfully."
	}


def get_smtp_config():
	return {
		key: (
			"configured" if key == "password" and value
			else value
		)
		for key, value in SMTP_CONFIG.items()
	}