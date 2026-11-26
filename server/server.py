
from http.server import HTTPServer
from server.handler import RequestHandler

HOST = "127.0.0.1"
PORT = 8000

def main():
    server = HTTPServer((HOST, PORT), RequestHandler)
    print(f"Server running at http://{HOST}:{PORT}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

