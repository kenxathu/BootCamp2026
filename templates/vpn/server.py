import os
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

TEAM_ID = os.environ.get("TEAM_ID", "01")
FLAG = os.environ.get("FLAG_VPN", f"FLAG{{VPN_Appliance_Team{TEAM_ID}_6e32d5f1}}")

VPN_PORTAL_HTML = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>SSL VPN Access Portal - Team {TEAM_ID}</title>
    <style>
        body {{ font-family: sans-serif; background: #1e293b; color: #fff; margin: 0; padding: 40px; display: flex; justify-content: center; }}
        .card {{ background: #334155; padding: 30px; border-radius: 10px; width: 450px; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }}
        input {{ width: 100%; padding: 10px; margin: 10px 0; border-radius: 4px; border: 1px solid #64748b; box-sizing: border-box; }}
        button {{ width: 100%; padding: 10px; background: #0284c7; color: white; border: none; border-radius: 4px; font-weight: bold; cursor: pointer; }}
        .flag-box {{ background: #450a0a; border-left: 4px solid #ef4444; padding: 10px; margin-top: 15px; color: #fca5a5; font-family: monospace; }}
    </style>
</head>
<body>
    <div class="card">
        <h2>🔒 SCB Internal SSL VPN Gateway</h2>
        <p>Target: <strong>KH VLAN 20 (172.16.20.102)</strong></p>
        <p>Monitored Ports: <strong>22</strong> (SSH) | <strong>443</strong> (SSL VPN)</p>
        <form action="/login" method="POST">
            <label>Username</label>
            <input type="text" placeholder="corp\\username">
            <label>Password / OTP</label>
            <input type="password" placeholder="••••••••">
            <button type="submit">Connect to Corporate Network</button>
        </form>
        <div class="flag-box">
            <strong>[APPLIANCE TARGET - VPN PRIVATE KEY]:</strong><br>
            <span>{FLAG}</span>
        </div>
    </div>
</body>
</html>
"""

class VPNWebHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health" or self.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"service": "vpn", "status": "UP", "team": TEAM_ID}).encode("utf-8"))
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(VPN_PORTAL_HTML.encode("utf-8"))

    def log_message(self, format, *args):
        return

def ssh_responder(port: int):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", port))
    sock.listen(32)
    print(f"[VPN-Team{TEAM_ID}] SSH listener active on port {port}")
    while True:
        c, _ = sock.accept()
        try:
            c.sendall(b"SSH-2.0-OpenSSH_9.2p1 SCB-VPN-Gateway\r\n")
        except Exception:
            pass
        finally:
            c.close()

if __name__ == "__main__":
    t = threading.Thread(target=ssh_responder, args=(22,), daemon=True)
    t.start()

    httpd = HTTPServer(("0.0.0.0", 443), VPNWebHandler)
    print(f"[VPN-Team{TEAM_ID}] Web VPN Portal active on port 443")
    httpd.serve_forever()

