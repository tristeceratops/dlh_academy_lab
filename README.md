# Danfoss Refrigeration Controller Security Lab

A local Python-based educational lab inspired by Claroty Team82's research into vulnerabilities affecting the Danfoss AK-SM 800A refrigeration controller.

The project recreates selected components of the controller's web-management architecture and provides controlled demonstrations of three vulnerabilities:

- CVE-2025-41450 — Authentication bypass.
- CVE-2025-41451 — SMTP configuration command injection.
- CVE-2025-41452 — NGINX configuration injection and denial of service.

**This is an educational simulation, not a reproduction of the original Danfoss firmware.**

---

## 1. Research context

The Danfoss AK-SM 800A is a centralized refrigeration system manager used in environments such as supermarkets, warehouses, and cold-storage facilities.

It provides a web-based management interface through which operators can monitor refrigeration equipment, configure temperature thresholds, manage alarms, configure notifications, and perform maintenance operations.

In their research, Claroty Team82 examined the device's embedded web architecture and identified several security weaknesses.

The research describes three important attack possibilities:

1. A hidden code-of-the-day authentication mechanism that can bypass normal password verification.
2. An SMTP configuration weakness that allows command injection and remote code execution.
3. An authenticated configuration-upload mechanism that allows modification of NGINX directives and can lead to denial of service.

The vulnerabilities affect the AK-SM 8xxA series. Danfoss addressed the reported issues through firmware updates.

**Original research:**

[Claroty Team82 — Freeze the Controller, Defrost the Food](https://claroty.com/team82/research/freeze-the-controller-defrost-the-food-uncovering-vulnerabilities-in-danfoss-refrigeration-controllers)

---

## 2. Lab objectives

This project aims to demonstrate how vulnerabilities in an industrial web-management interface can be chained together.

The lab provides:

- A local HTTP server.
- A simulated authentication mechanism.
- An online refrigeration monitoring dashboard.
- Seven simulated refrigeration controllers.
- Temperature monitoring and defrost functionality.
- An SMTP configuration interface.
- A simulated NGINX configuration-management endpoint.
- Three vulnerability demonstrations.
- Browser-based testing through the web interface and Developer Tools.

The server is designed to run on Windows and Ubuntu.

---

## 3. Architecture

The following diagram represents the main components and their relationships.

```text
                    +----------------+
                    |  Defrost Mode  |
                    +----------------+
                            |
                            |
+------------------+   +----------+   +---------------------------+
| load_nginx_headers|<->|  Server  |<->| Online Fridge Monitor     |
+------------------+   +----------+   | Dashboard                 |
                            |          +---------------------------+
                            |                       |
                            |                       |
                        +--------+        +--------------------------+
                        | xml.cgi|        | SMTP Password Settings   |
                        +--------+        | for Email                |
                         /      \         +--------------------------+
                        /        \
             +----------------+  +---------+
             | read_date_time |  | getauth |
             +----------------+  +---------+
```

### Main components

| Component | Purpose |
|---|---|
| `server/` | Implements the local HTTP server and request handling. |
| `www/` | Contains the browser interface. |
| `endpoints/` | Implements the simulated controller endpoints. |
| `lab_data/` | Stores simulated controller data and NGINX configuration. |
| `logs/` | Stores HTTP request logs. |
| `exploit/` | Contains standalone Python demonstration clients. |

### Web application

The browser interface contains three main areas:

- **Dashboard:** Displays the simulated refrigeration controllers, their temperatures, and their operational status.
- **Defrost mode:** Allows an operator to trigger the simulated defrost process.
- **Settings:** Provides individual configuration forms for SMTP server, port, email address, username, and password.

### Server

The Python HTTP server is the central component.

It handles browser requests, authentication, session management, controller operations, and configuration updates.

It also dispatches requests to the different endpoint modules.

### XML CGI simulation

The `xml.cgi` functionality reproduces selected aspects of the original XML CGI interface.

It includes:

- `getauth`: Handles the synthetic authentication mechanism.
- `read_date_time`: Returns the current date and time.
- `load_nginx_headers`: Reads or replaces the simulated NGINX configuration.

These are Python implementations, not the original Danfoss CGI binaries.

---

## 4. The three vulnerabilities

### CVE-2025-41450 — Authentication bypass

**Category:** CWE-287 — Improper Authentication

The research describes a hidden code-of-the-day authentication mechanism inside the `getauth` request handler.

Instead of validating the administrator's configured password, an alternate authentication path can validate a generated password based on the device's current date and time.

Claroty identified two request attributes that activate this alternate path. Their names were redacted in the published research.

The weakness allows an attacker who reconstructs the algorithm and request conditions to bypass normal password verification.

Successful authentication can provide access to the device's web-management interface.

**Lab implementation**

The lab implements a synthetic version of this mechanism in:

`endpoints/xml_cgi.py`

It includes:

- A generated daily authentication code.
- A normal administrator authentication path.
- An alternate service authentication path.
- A login endpoint that creates a browser session.

The synthetic implementation uses:

- `auth_mode=service`
- `service_access=enabled`

These are lab-specific parameters, not the original Danfoss request attributes.

The daily code is generated using a simplified formula defined in the Python endpoint.

**Demonstration:** Generate the synthetic code and submit the authentication request from the browser.

---

### CVE-2025-41451 — SMTP command injection / Remote Code Execution

**Category:** CWE-77 — Improper Neutralization of Special Elements Used in a Command

Claroty discovered that the SMTP email configuration functionality used a password value when constructing an operating-system shell command.

The research identifies an internal configuration item, `0x1be1`, as the source of the email authentication password.

According to the researchers, the value was not properly sanitized before being formatted into the command.

An attacker able to modify this setting could therefore introduce shell directives and cause additional commands to execute.

This vulnerability is post-authentication: the attacker first needs access to the management interface.

**Lab implementation**

The relevant module is:

`endpoints/smtp_config.py`

The settings page provides separate forms for:

- SMTP server.
- SMTP port.
- Email address.
- Username.
- Password.

For safety and cross-platform compatibility, the current lab does not reproduce unrestricted shell injection.

Instead, entering the exact password value `id` triggers a fixed identity command:

| Operating system | Executed command |
|---|---|
| Linux | `id` |
| Windows | `whoami.exe` |

The command is executed without shell interpretation. Its output is printed in the server terminal and returned in the HTTP response.

This demonstrates the relationship between an SMTP password configuration field and server-side command execution without exposing an unrestricted command-execution interface.

**Demonstration:** Open the settings page and enter `id` in the SMTP password field.

---

### CVE-2025-41452 — NGINX configuration injection / Denial of Service

**Category:** CWE-15 — External Control of System or Configuration Setting

The Danfoss web application exposes functionality for replacing the `headers.conf` configuration file used by the externally exposed NGINX instance.

Claroty found that an authenticated user could upload a modified configuration containing additional NGINX directives.

Because the configuration is reloaded dynamically, injected routing directives can affect how the web server processes requests.

The researchers also identified a malicious route that could trigger an unhandled exception inside the `sm_app` process, resulting in a denial-of-service condition.

**Lab implementation**

The relevant module is:

`endpoints/load_nginx_headers.py`

The lab allows an authenticated user to replace a simulated NGINX configuration file.

The configuration can contain additional routes, including:

- `/lab-configuration-check`
- `/lab-simulated-failure`

The first route demonstrates that the configuration has been modified.

The second returns a simulated HTTP 503 response.

**Important:** The lab does not modify a real NGINX process or crash the Python server. The HTTP 503 response represents the failure condition in a controlled manner.

**Demonstration:** Submit a modified configuration through the browser and request the simulated failure route.

---

## 5. Project structure

```text
dlh_academy_lab/
│
├── www/
│   ├── index.html
│   ├── dashboard.html
│   └── settings.html
│
├── endpoints/
│   ├── load_nginx_headers.py
│   ├── xml_cgi.py
│   ├── device_manager.py
│   └── smtp_config.py
│
├── lab_data/
│   ├── devices.json
│   └── headers.conf
│
├── logs/
│   └── http_requests.jsonl
│
├── server/
│   ├── handler.py
│   ├── request_logger.py
│   └── main.py
│
└── exploit/
    ├── cve1_auth_payload.py
    ├── cve2_nginx_exploit.py
    ├── cve3_smtp_exploit.py
    └── exploit_headers.conf
```

### Important files

| File | Description |
|---|---|
| `server/main.py` | Starts the HTTP server. |
| `server/handler.py` | Handles HTTP requests and routes. |
| `endpoints/xml_cgi.py` | Implements authentication and XML CGI functionality. |
| `endpoints/device_manager.py` | Manages simulated refrigeration controllers. |
| `endpoints/smtp_config.py` | Handles SMTP settings and the fixed identity-command test. |
| `endpoints/load_nginx_headers.py` | Handles simulated NGINX configuration replacement. |
| `lab_data/devices.json` | Stores controller states and temperatures. |
| `lab_data/headers.conf` | Stores the active simulated NGINX configuration. |

---

## 6. Requirements

- Python 3.10 or later recommended.
- Windows or Ubuntu.
- A modern web browser.
- No third-party Python packages are required by the core lab.

Check your Python installation:

**Windows:**

```powershell
python --version
```

**Ubuntu:**

```bash
python3 --version
```

---

## 7. Launching the server

Open a terminal in the project directory.

### Windows — PowerShell

Navigate to the project:

```powershell
cd C:\OSINT-BIA\dlh_academy_lab
```

Start the server:

```powershell
python -m server.main
```

Expected output:

```text
Server running at http://127.0.0.1:8000
```

### Ubuntu

Navigate to the project directory:

```bash
cd ~/dlh_academy_lab
```

Start the server:

```bash
python3 -m server.main
```

Expected output:

```text
Server running at http://127.0.0.1:8000
```

### Access the lab

Open your browser and visit:

[http://127.0.0.1:8000](http://127.0.0.1:8000)

The server listens on `127.0.0.1`, meaning it is accessible from the local machine only by default.

Press `CTRL+C` in the terminal to stop the server.

---

## 8. Resetting the simulated controllers

The project includes a reset script that restores the seven default refrigeration controllers.

From the project root:

**Windows:**

```powershell
python .\reset_devices.py
```

**Ubuntu:**

```bash
python3 reset_devices.py
```

This restores the initial controller data in `lab_data/devices.json`.

---

## 9. Recommended demonstration order

The three vulnerabilities can be studied in the following order:

1. **CVE-2025-41450:** Understand the authentication mechanism and obtain a browser session.
2. **CVE-2025-41451:** Explore the SMTP configuration page and the server-side identity-command test.
3. **CVE-2025-41452:** Replace the simulated NGINX configuration and test the injected routes.

This sequence demonstrates how an authentication weakness can expose privileged configuration functionality, which may then lead to further compromise of a management interface.

---

## 10. Security and remediation

The original research highlights the risks of exposing industrial management interfaces to untrusted networks.

Recommended defensive measures include:

- Upgrade affected Danfoss AK-SM 800A controllers to the appropriate fixed firmware.
- Do not expose management interfaces directly to the Internet.
- Restrict administrative access to trusted management networks.
- Use VPNs and network segmentation for remote administration.
- Validate and sanitize all configuration values.
- Avoid constructing shell commands from user-controlled input.
- Restrict configuration upload functionality to authorized administrators.
- Monitor authentication and configuration changes.

Claroty reports that Danfoss released firmware R4.3.1 addressing the vulnerabilities described in the research.

---

## 11. Disclaimer

This project is intended for educational purposes and authorized local security testing.

It is not the original Danfoss AK-SM 800A firmware and does not reproduce the original vulnerabilities in their entirety.

The authentication parameters, code-generation logic, configuration replacement behavior, and command-execution mechanism are lab-specific implementations.

Do not use the lab against systems for which you do not have explicit authorization.

---

## References

- [Claroty Team82 — Freeze the Controller, Defrost the Food](https://claroty.com/team82/research/freeze-the-controller-defrost-the-food-uncovering-vulnerabilities-in-danfoss-refrigeration-controllers)
- [Danfoss](https://www.danfoss.com/)