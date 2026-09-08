import os
import sys
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

TEAM_ID = os.environ.get("TEAM_ID", "01")
FLAG = os.environ.get("FLAG_DC", f"FLAG{{DC0153_DomainAdmin_Team{TEAM_ID}_c48f217d}}")
DOMAIN_NAME = f"CORP{int(TEAM_ID):02d}.ARENA.LOCAL"
HOSTNAME = "DC-0153"

AD_WEB_HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Windows Server 2022 - {HOSTNAME} ({DOMAIN_NAME})</title>
    <style>
        body {{ font-family: "Segoe UI", Tahoma, sans-serif; background: #004275; color: #fff; margin: 0; padding: 20px; }}
        .header {{ background: #002b4d; padding: 15px 25px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; }}
        .title {{ font-size: 22px; font-weight: 600; }}
        .content {{ background: #f3f3f3; color: #222; margin-top: 20px; padding: 25px; border-radius: 6px; box-shadow: 0 4px 12px rgba(0,0,0,0.4); }}
        .badge {{ background: #107c41; color: #fff; padding: 4px 8px; border-radius: 3px; font-size: 12px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 14px; }}
        th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
        th {{ background: #e0e0e0; color: #333; }}
        .flag-box {{ background: #ffebee; border-left: 5px solid #d32f2f; padding: 15px; margin-top: 20px; color: #b71c1c; font-family: Consolas, monospace; }}
    </style>
</head>
<body>
    <div class="header">
        <div class="title">🪟 Active Directory Domain Services Web Console</div>
        <div>
            <span class="badge">DC ONLINE</span> &nbsp;
            <span>Host: <strong>{HOSTNAME}.{DOMAIN_NAME}</strong> (172.16.20.104)</span>
        </div>
    </div>
    <div class="content">
        <h2>Domain Controller Status: {DOMAIN_NAME}</h2>
        <p>Operational role: Primary Domain Controller (PDC Emulator, RID Master, Infrastructure Master).</p>
        
        <h3>Active Directory Service Endpoints (Image 1 Compliance):</h3>
        <table>
            <thead><tr><th>Service</th><th>Port</th><th>Protocol</th><th>Status</th></tr></thead>
            <tbody>
                <tr><td>Kerberos KDC</td><td>88</td><td>TCP</td><td><span class="badge">LISTENING</span></td></tr>
                <tr><td>MSRPC Endpoint Mapper</td><td>135</td><td>TCP</td><td><span class="badge">LISTENING</span></td></tr>
                <tr><td>LDAP Directory Service</td><td>389</td><td>TCP</td><td><span class="badge">LISTENING</span></td></tr>
                <tr><td>SMB / CIFS File Sharing</td><td>445</td><td>TCP</td><td><span class="badge">LISTENING</span></td></tr>
                <tr><td>LDAPS (Secure LDAP)</td><td>636</td><td>TCP</td><td><span class="badge">LISTENING</span></td></tr>
                <tr><td>Active Directory Web Console</td><td>8081</td><td>HTTP</td><td><span class="badge">LISTENING</span></td></tr>
                <tr><td>RPC High Dynamic Port A</td><td>50000</td><td>TCP</td><td><span class="badge">LISTENING</span></td></tr>
                <tr><td>RPC High Dynamic Port B</td><td>50050</td><td>TCP</td><td><span class="badge">LISTENING</span></td></tr>
                <tr><td>RPC High Dynamic Port C</td><td>50100</td><td>TCP</td><td><span class="badge">LISTENING</span></td></tr>
            </tbody>
        </table>

        <div class="flag-box">
            <strong>[SERVER TARGET - DOMAIN ADMIN CREDENTIAL LEAK]:</strong><br>
            <span>{FLAG}</span>
        </div>
    </div>
</body>
</html>
"""

class DCWebHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health" or self.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "UP", "host": HOSTNAME, "domain": DOMAIN_NAME}).encode("utf-8"))
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(AD_WEB_HTML.encode("utf-8"))

    def log_message(self, format, *args):
        return

def tcp_listener(port: int, banner: str):
    """Generic TCP responder for Kerberos, LDAP, SMB, RPC ports."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("0.0.0.0", port))
        sock.listen(128)
        print(f"[DC-0153] Listening on port {port} ({banner})")
        while True:
            client, addr = sock.accept()
            try:
                client.settimeout(3.0)
                # Send mock banner/handshake if connected
                if port == 445:
                    client.sendall(b"\x00\x00\x00\x45\xffSMB@\x00\x00\x00\x00Windows Server 2022 DC01\x00")
                elif port in (389, 636):
                    client.sendall(b"LDAPv3 ActiveDirectory DC0153\n")
                elif port == 88:
                    client.sendall(b"KRB5_KDC_DC0153_READY\n")
                elif port in (50000, 50050, 50100):
                    client.sendall(b"MSRPC_EP_OK\n")
                else:
                    client.sendall(b"OK\n")
            except Exception:
                pass
            finally:
                client.close()
    except Exception as e:
        print(f"[DC-0153] Error on port {port}: {e}")

def run_web():
    httpd = HTTPServer(("0.0.0.0", 8081), DCWebHandler)
    print("[DC-0153] Web console listening on port 8081")
    httpd.serve_forever()

if __name__ == "__main__":
    # Monitored ports from Image 1: 88, 135, 389, 445, 636, 8081, 50000, 50050, 50100
    tcp_ports = [
        (88, "Kerberos"),
        (135, "MSRPC"),
        (389, "LDAP"),
        (445, "SMB"),
        (636, "LDAPS"),
        (50000, "RPC High 50000"),
        (50050, "RPC High 50050"),
        (50100, "RPC High 50100")
    ]

    for p, desc in tcp_ports:
        t = threading.Thread(target=tcp_listener, args=(p, desc), daemon=True)
        t.start()

    run_web()

