import os
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

TEAM_ID = os.environ.get("TEAM_ID", "01")
FLAG = os.environ.get("FLAG_ESXI", f"FLAG{{ESXi_vCenter_Root_Team{TEAM_ID}_e82a391c}}")

ESXI_HTML = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>VMware ESXi Host Client - Team {TEAM_ID}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #23282d; color: #fff; margin: 0; padding: 20px; }}
        .header {{ background: #000; padding: 15px 25px; border-bottom: 2px solid #007cbb; display: flex; justify-content: space-between; align-items: center; }}
        .logo {{ font-size: 18px; font-weight: bold; color: #007cbb; }}
        .card {{ background: #2d3238; border-radius: 6px; padding: 20px; margin-top: 20px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 13px; }}
        th, td {{ padding: 8px; border-bottom: 1px solid #3d444d; text-align: left; }}
        .badge {{ background: #007cbb; color: white; padding: 3px 6px; border-radius: 3px; font-size: 11px; }}
        .flag-box {{ background: #3b1114; border-left: 4px solid #ff4d4f; padding: 12px; margin-top: 20px; font-family: monospace; color: #ff7875; }}
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">VMware ESXi 8.0.2 [Host Client] - Team {TEAM_ID}</div>
        <div><span>Host IP: <strong>10.10.1{int(TEAM_ID):02d}.3</strong></span></div>
    </div>
    <div class="card">
        <h3>Host System Overview</h3>
        <table>
            <tr><td>Model</td><td>VMware Virtual Platform</td></tr>
            <tr><td>Hypervisor</td><td>VMware ESXi, 8.0.2, Build 22380479</td></tr>
            <tr><td>Management Ports</td><td><strong>2301, 2302, 2303, 2322</strong> (Active / SLA Monitored)</td></tr>
            <tr><td>Target Weight</td><td><strong>1000 Points</strong> (ESXi / vCenter Compromise)</td></tr>
        </table>

        <h3>Virtual Machines on Host:</h3>
        <table>
            <thead><tr><th>VM Name</th><th>VLAN</th><th>State</th><th>CPUs / RAM</th></tr></thead>
            <tbody>
                <tr><td>Web-AIO</td><td>VLAN 20</td><td><span class="badge">Running</span></td><td>2 vCPU / 4 GB</td></tr>
                <tr><td>DC01-WindowsServer</td><td>VLAN 20</td><td><span class="badge">Running</span></td><td>4 vCPU / 8 GB</td></tr>
                <tr><td>Jenkins-SupplyChain</td><td>VLAN 202</td><td><span class="badge">Running</span></td><td>4 vCPU / 8 GB</td></tr>
                <tr><td>K3s-ArgoCD-Master</td><td>VLAN 202</td><td><span class="badge">Running</span></td><td>4 vCPU / 8 GB</td></tr>
            </tbody>
        </table>

        <div class="flag-box">
            <strong>[ESXi / VCENTER TARGET - HYPERVISOR ROOT FLAG]:</strong><br>
            <span>{FLAG}</span>
        </div>
    </div>
</body>
</html>
"""

class ESXiWebHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health" or self.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"service": "esxi", "status": "UP", "team": TEAM_ID}).encode("utf-8"))
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(ESXI_HTML.encode("utf-8"))

    def log_message(self, format, *args):
        return

def mgmt_responder(port: int):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", port))
    sock.listen(16)
    print(f"[ESXi-Team{TEAM_ID}] Management port {port} listening")
    while True:
        c, _ = sock.accept()
        try:
            c.sendall(f"ESXi-MGMT-PORT-{port}-READY\r\n".encode("utf-8"))
        except Exception:
            pass
        finally:
            c.close()

if __name__ == "__main__":
    # Monitored Management Ports: 2301, 2302, 2303, 2322
    for p in (2301, 2302, 2303, 2322):
        t = threading.Thread(target=mgmt_responder, args=(p,), daemon=True)
        t.start()

    httpd = HTTPServer(("0.0.0.0", 80), ESXiWebHandler)
    print(f"[ESXi-Team{TEAM_ID}] ESXi Web host client running on port 80")
    httpd.serve_forever()

