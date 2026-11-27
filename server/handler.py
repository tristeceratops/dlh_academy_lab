import json
import secrets

from http.server import SimpleHTTPRequestHandler
from http.cookies import SimpleCookie
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from endpoints.load_nginx_headers import (
    load_nginx_headers,
    replace_nginx_headers,
    is_simulated_failure_route
)

from endpoints.xml_cgi import (
    read_date_time,
    getauth
)

from endpoints.device_manager import (
    load_devices,
    get_device,
    defrost_device
)

from endpoints.smtp_config import (
    save_smtp_setting,
    get_smtp_config
)

from server.request_logger import log_request


ROOT = Path(__file__).resolve().parent.parent
WWW = ROOT / "www"

sessions = {}


class RequestHandler(SimpleHTTPRequestHandler):

    protected_pages = [
        "/dashboard.html",
        "/settings.html"
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WWW), **kwargs)

    # --------------------------------------------------
    # HTTP logging
    # --------------------------------------------------

    def log_request(self, code="-", size="-"):
        parameter_names = getattr(
            self,
            "_request_parameter_names",
            []
        )

        try:
            log_request(
                self.command,
                self.path,
                code,
                parameter_names
            )
        except OSError as error:
            print(f"HTTP logging error: {error}")

    # --------------------------------------------------
    # Sessions
    # --------------------------------------------------

    def get_session(self):
        cookie = SimpleCookie(
            self.headers.get("Cookie", "")
        )

        session = cookie.get("session_id")

        if session:
            return sessions.get(session.value)

        return None

    def is_authenticated(self):
        return self.get_session() is not None

    def create_session(self, username):
        token = secrets.token_urlsafe(32)
        sessions[token] = username
        return token

    # --------------------------------------------------
    # HTTP responses
    # --------------------------------------------------

    def respond(self, content, status=200):
        body = content.encode("utf-8")

        self.send_response(status)
        self.send_header(
            "Content-Type",
            "text/plain; charset=utf-8"
        )
        self.send_header(
            "Content-Length",
            str(len(body))
        )
        self.end_headers()

        self.wfile.write(body)

    def respond_json(self, content, status=200):
        body = json.dumps(content).encode("utf-8")

        self.send_response(status)
        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )
        self.send_header(
            "Content-Length",
            str(len(body))
        )
        self.end_headers()

        self.wfile.write(body)

    def redirect(self, location):
        self.send_response(303)
        self.send_header("Location", location)
        self.end_headers()

    # --------------------------------------------------
    # GET
    # --------------------------------------------------

    def do_GET(self):
        parsed = urlparse(self.path)

        params = parse_qs(
            parsed.query,
            keep_blank_values=True
        )

        self._request_parameter_names = list(params.keys())

        # Protected pages
        if parsed.path in self.protected_pages:
            if not self.is_authenticated():
                self.redirect("/")
                return

        # Simulated injected route
        if is_simulated_failure_route(parsed.path):
            self.respond(
                "503 Service Unavailable: "
                "Simulated application failure.",
                503
            )
            return
        
        # Simulated configuration-check route
        if parsed.path == "/lab-configuration-check":

            if not self.is_authenticated():
                self.send_error(403)
                return

            self.send_response(200)
            self.send_header(
                "X-Lab-Route",
                "Configuration-Modified"
            )
            self.send_header(
                "Content-Type",
                "text/plain; charset=utf-8"
            )

            body = (
                "NGINX configuration route successfully detected."
            ).encode("utf-8")

            self.send_header(
                "Content-Length",
                str(len(body))
            )
            self.end_headers()
            self.wfile.write(body)
            return

        # NGINX headers endpoint
        if parsed.path == "/load_nginx_headers":
            if not self.is_authenticated():
                self.send_error(403)
                return

            self.respond(load_nginx_headers())
            return

        # XML CGI endpoint
        if parsed.path == "/xml.cgi":

            action = params.get(
                "action",
                [""]
            )[0]

            if action == "read_date_time":
                self.respond(read_date_time())
                return

            if action == "load_nginx_headers":
                if not self.is_authenticated():
                    self.send_error(403)
                    return

                self.respond(load_nginx_headers())
                return

            if action == "getauth" or "getauth" in params:

                username = params.get(
                    "username",
                    [""]
                )[0]

                password = params.get(
                    "password",
                    [""]
                )[0]

                auth_mode = params.get(
                    "auth_mode",
                    [""]
                )[0]

                service_access = params.get(
                    "service_access",
                    [""]
                )[0]

                result = getauth(
                    username,
                    password,
                    auth_mode,
                    service_access
                )

                self.respond(result)
                return

            self.respond("Unknown CGI command", 400)
            return

        # Device collection API
        if parsed.path == "/api/devices":

            if not self.is_authenticated():
                self.send_error(403)
                return

            self.respond_json(load_devices())
            return

        # Individual device API
        if parsed.path.startswith("/api/devices/"):

            if not self.is_authenticated():
                self.send_error(403)
                return

            device_id = parsed.path.split("/")[-1]
            device = get_device(device_id)

            if device:
                self.respond_json(device)
            else:
                self.send_error(404)

            return
        
        
        # Retrieve SMTP configuration
        if parsed.path == "/api/smtp/config":

            if not self.is_authenticated():
                self.respond_json({
                    "success": False,
                    "error": "Authentication required."
                }, 403)
                return

            self.respond_json({
                "success": True,
                "configuration": get_smtp_config()
            })
            return



        # Static files
        super().do_GET()

    # --------------------------------------------------
    # POST
    # --------------------------------------------------

    def do_POST(self):
        parsed = urlparse(self.path)

        length = int(
            self.headers.get("Content-Length", 0)
        )

        raw_data = self.rfile.read(length)

        # NGINX configuration replacement
        if (
            parsed.path == "/xml.cgi"
            and parse_qs(parsed.query).get("action", [""])[0]
            == "load_nginx_headers"
        ):

            self._request_parameter_names = [
                "action",
                "headers.conf"
            ]

            if not self.is_authenticated():
                self.send_error(403)
                return

            try:
                content = raw_data.decode("utf-8")
            except UnicodeDecodeError:
                self.respond_json({
                    "success": False,
                    "message": "Configuration must be UTF-8 text."
                }, 400)
                return

            result = replace_nginx_headers(content)

            if result["success"]:
                self.respond_json(result)
            else:
                self.respond_json(result, 400)

            return
        
        

        
        # SMTP configuration and password lab
        if parsed.path == "/api/smtp/config":

            if not self.is_authenticated():
                self.respond_json({
                    "success": False,
                    "error": "Authentication required."
                }, 403)
                return

            try:
                payload = json.loads(raw_data.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                self.respond_json({
                    "success": False,
                    "error": "Invalid JSON request."
                }, 400)
                return

            if not isinstance(payload, dict):
                self.respond_json({
                    "success": False,
                    "error": "Invalid request format."
                }, 400)
                return

            field = payload.get("field")
            value = payload.get("value")

            self._request_parameter_names = [
                str(field) if field is not None else "unknown"
            ]

            result = save_smtp_setting(field, value)

            status = 200 if result["success"] else 400

            self.respond_json(result, status)
            return

        # Standard form data
        try:
            decoded_data = raw_data.decode("utf-8")
        except UnicodeDecodeError:
            self.send_error(400)
            return

        params = parse_qs(
            decoded_data,
            keep_blank_values=True
        )

        self._request_parameter_names = list(params.keys())

        # Login
        if parsed.path == "/login":

            username = params.get(
                "username",
                [""]
            )[0]

            password = params.get(
                "password",
                [""]
            )[0]

            auth_mode = params.get(
                "auth_mode",
                [""]
            )[0]

            service_access = params.get(
                "service_access",
                [""]
            )[0]

            result = getauth(
                username,
                password,
                auth_mode,
                service_access
            )

            if result == "Connection granted":

                token = self.create_session(username)

                self.send_response(303)
                self.send_header(
                    "Location",
                    "/dashboard.html"
                )
                self.send_header(
                    "Set-Cookie",
                    f"session_id={token}; HttpOnly; SameSite=Strict; Path=/"
                )
                self.end_headers()

            else:
                self.redirect("/?error=1")

            return

        # Logout
        if parsed.path == "/logout":

            cookie = SimpleCookie(
                self.headers.get("Cookie", "")
            )

            session = cookie.get("session_id")

            if session:
                sessions.pop(session.value, None)

            self.send_response(303)
            self.send_header("Location", "/")
            self.send_header(
                "Set-Cookie",
                "session_id=; HttpOnly; Max-Age=0; Path=/"
            )
            self.end_headers()

            return

        # Device defrost
        if (
            parsed.path.startswith("/api/devices/")
            and parsed.path.endswith("/defrost")
        ):

            if not self.is_authenticated():
                self.send_error(403)
                return

            device_id = parsed.path.split("/")[-2]

            result = defrost_device(device_id)

            if result["success"]:
                self.respond_json(result)
            else:
                self.respond_json(result, 400)

            return

        self.send_error(404)