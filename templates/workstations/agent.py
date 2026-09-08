import os
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

WS_NAME = os.environ.get("WS_NAME", "WS-01")
TEAM_ID = os.environ.get("TEAM_ID", "01")
WS_AGENT_PORT = int(os.environ.get("WS_AGENT_PORT", "4481"))
WINRM_PORT = int(os.environ.get("WINRM_PORT", "5985"))
RDP_PORT = int(os.environ.get("RDP_PORT", "3389"))

FLAG = os.environ.get("FLAG_WS", f"FLAG{{{WS_NAME.replace('-', '')}_LocalAdmin_Team{TEAM_ID}_7a1f0c}}")

class AgentWebHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/status" or self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            data = {
                "workstation": WS_NAME,
                "team_id": TEAM_ID,
                "status": "ONLINE",
                "os": "Windows 11 Enterprise",
                "user": f"CORP{TEAM_ID}\\User_{WS_NAME.lower()}"
            }
            self.wfile.write(json.dumps(data).encode("utf-8"))
        elif self.path == "/flag" or self.path == "/c$/Users/Administrator/flag.txt":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(FLAG.encode("utf-8"))
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            html = f"""<html><body style="font-family:sans-serif;background:#222;color:#eee;padding:20px;">
            <h2>🖥️ {WS_NAME} - Enterprise Workstation Agent</h2>
            <p>Status: <span style="color:#4ade80;">Active</span> | Team: <strong>Team {TEAM_ID}</strong></p>
            <p>Agent Port: {WS_AGENT_PORT} | WinRM Port: {WINRM_PORT} | RDP Port: {RDP_PORT}</p>
            <div style="background:#400;border:1px dashed #f55;padding:10px;margin-top:15px;color:#faa;">
                [WORKSTATION FLAG]: {FLAG}
            </div>
            </body></html>"""
            self.wfile.write(html.encode("utf-8"))

    def log_message(self, format, *args):
        return

def tcp_responder(port: int, banner: str):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("0.0.0.0", port))
        sock.listen(64)
        print(f"[{WS_NAME}] Listening on port {port} ({banner})")
        while True:
            client, addr = sock.accept()
            try:
                client.settimeout(2.0)
                if "RDP" in banner:
                    # Standard RDP Connection Confirm handshake response (TPKT + X.224)
                    client.sendall(b"\x03\x00\x00\x13\x0e\xd0\x00\x00\x12\x34\x00\x02\x00\x08\x00\x00\x00\x00\x00")
                elif "WinRM" in banner:
                    client.sendall(b"HTTP/1.1 401 Unauthorized\r\nServer: Microsoft-HTTPAPI/2.0\r\nWWW-Authenticate: Negotiate\r\nContent-Length: 0\r\n\r\n")
                else:
                    client.sendall(b"OK\n")
            except Exception:
                pass
            finally:
                client.close()
    except Exception as e:
        print(f"[{WS_NAME}] Port {port} error: {e}")

if __name__ == "__main__":
    # Start WinRM and RDP TCP listeners
    t1 = threading.Thread(target=tcp_responder, args=(WINRM_PORT, "WinRM"), daemon=True)
    t1.start()

    t2 = threading.Thread(target=tcp_responder, args=(RDP_PORT, "RDP"), daemon=True)
    t2.start()

    # Start Agent Web server
    httpd = HTTPServer(("0.0.0.0", WS_AGENT_PORT), AgentWebHandler)
    print(f"[{WS_NAME}] Workstation Agent running on port {WS_AGENT_PORT}")
    httpd.serve_forever()

