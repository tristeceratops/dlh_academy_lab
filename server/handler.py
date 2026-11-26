from http.server import SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from endpoints.load_nginx_headers import load_nginx_headers
from endpoints.xml_cgi import read_date_time

ROOT = Path(__file__).resolve().parent.parent
WWW = ROOT / "www"


class RequestHandler(SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WWW), **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/load_nginx_headers":
            self.respond(load_nginx_headers())

        elif parsed.path == "/xml.cgi":
            params = parse_qs(parsed.query)

            if "read_date_time" in params or parsed.query == "read_date_time":
                self.respond(read_date_time())
            else:
                self.respond("Unknown CGI command")

        else:
            super().do_GET()

    def respond(self, content):
        body = content.encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

