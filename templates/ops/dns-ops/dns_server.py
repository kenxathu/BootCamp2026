import os
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

TEAM_ID = os.environ.get("TEAM_ID", "01")

class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({
            "service": "dns-ops",
            "team_id": TEAM_ID,
            "status": "UP",
            "zone": f"team{int(TEAM_ID):02d}.arena.local"
        }).encode("utf-8"))

    def log_message(self, format, *args):
        return

def udp_dns_mock():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", 53))
    print(f"[DNS-OPS-Team{TEAM_ID}] DNS UDP listening on port 53")
    while True:
        try:
            data, addr = sock.recvfrom(512)
            # Send mock DNS response header with NOERROR
            if len(data) >= 12:
                resp = bytearray(data[:12])
                resp[2] = 0x81 # Response, recursion desired
                resp[3] = 0x80 # Recursion available, No error
                sock.sendto(resp + data[12:], addr)
        except Exception:
            pass

def tcp_dns_mock():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", 53))
    sock.listen(16)
    while True:
        c, _ = sock.accept()
        try:
            c.settimeout(2.0)
            data = c.recv(512)
            if len(data) > 0:
                c.sendall(data)
        except Exception:
            pass
        finally:
            c.close()

if __name__ == "__main__":
    t_udp = threading.Thread(target=udp_dns_mock, daemon=True)
    t_udp.start()

    t_tcp = threading.Thread(target=tcp_dns_mock, daemon=True)
    t_tcp.start()

    httpd = HTTPServer(("0.0.0.0", 9153), MetricsHandler)
    print(f"[DNS-OPS-Team{TEAM_ID}] Metrics server listening on port 9153")
    httpd.serve_forever()

