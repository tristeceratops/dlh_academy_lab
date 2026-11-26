
from http.server import HTTPServer, SimpleHTTPRequestHandler


class RequestHandler(SimpleHTTPRequestHandler):

    def do_GET(self):
        if self.path == "/load_nginx_headers":
            self.load_nginx_headers()
        elif self.path == "/xml.cgi":
            self.xml_cgi()
        else:
            super().do_GET()

    def load_nginx_headers(self):
        pass

    def xml_cgi(self):
        pass


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8000), RequestHandler)
    print("Server running at http://localhost:8000")
    server.serve_forever()

