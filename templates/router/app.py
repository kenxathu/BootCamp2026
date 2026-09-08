import os
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

TEAM_ID = os.environ.get("TEAM_ID", "01")
ROUTER_NAME = f"pfSense-Team{int(TEAM_ID):02d}"

HTML_TEMPLATE = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{ROUTER_NAME} | Netgate pfSense Inter-VLAN Router</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }}
        .navbar {{ background: #1e293b; padding: 15px 25px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; border-left: 5px solid #22c55e; }}
        .brand {{ font-size: 20px; font-weight: bold; color: #38bdf8; display: flex; align-items: center; gap: 10px; }}
        .badge {{ background: #15803d; color: white; padding: 4px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 20px; margin-top: 20px; }}
        .card {{ background: #1e293b; border-radius: 8px; padding: 20px; border: 1px solid #334155; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }}
        .card h3 {{ margin-top: 0; color: #38bdf8; border-bottom: 1px solid #334155; padding-bottom: 8px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 13px; }}
        th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #334155; }}
        th {{ color: #94a3b8; }}
        .status-up {{ color: #4ade80; font-weight: bold; }}
        .flag-box {{ background: #450a0a; border: 1px dashed #ef4444; padding: 12px; border-radius: 6px; margin-top: 15px; font-family: monospace; word-break: break-all; }}
    </style>
</head>
<body>
    <div class="navbar">
        <div class="brand">
            <span>🛡️ Netgate pfSense (Community Edition)</span>
            <span class="badge">ONLINE</span>
        </div>
        <div>
            <span>Host: <strong>{ROUTER_NAME}.arena.local</strong></span> | 
            <span>WAN IP: <strong>10.10.1{int(TEAM_ID):02d}.2</strong></span>
        </div>
    </div>

    <div class="grid">
        <div class="card">
            <h3>System Information</h3>
            <table>
                <tr><td>Hostname</td><td><strong>{ROUTER_NAME}</strong></td></tr>
                <tr><td>Role</td><td>Inter-VLAN 802.1Q Router & Firewall</td></tr>
                <tr><td>OS Version</td><td>pfSense 2.7.2-RELEASE (FreeBSD 14-CURRENT)</td></tr>
                <tr><td>Uptime</td><td>Active (Cyber Range Simulation)</td></tr>
                <tr><td>Arena Team</td><td><strong>Team {TEAM_ID}</strong></td></tr>
            </table>
        </div>

        <div class="card">
            <h3>Inter-VLAN Interfaces</h3>
            <table>
                <thead><tr><th>VLAN</th><th>Name</th><th>Subnet / Gateway</th><th>Status</th></tr></thead>
                <tbody>
                    <tr><td>WAN</td><td>Arena Distribution</td><td>10.10.1{int(TEAM_ID):02d}.2/24</td><td class="status-up">UP</td></tr>
                    <tr><td>VLAN 20</td><td>KH (Khách hàng)</td><td>172.16.20.1/24</td><td class="status-up">UP</td></tr>
                    <tr><td>VLAN 201</td><td>SCB_VLAN201 (Edge/Git)</td><td>172.16.201.1/24</td><td class="status-up">UP</td></tr>
                    <tr><td>VLAN 202</td><td>SCB_VLAN202 (CI/CD)</td><td>172.16.202.1/24</td><td class="status-up">UP</td></tr>
                    <tr><td>VLAN 203</td><td>SCB_VLAN203 (Ops/DNS)</td><td>172.16.203.1/24</td><td class="status-up">UP</td></tr>
                    <tr><td>VLAN 204</td><td>AdminPrivate (DHCP)</td><td>172.16.204.1/24</td><td class="status-up">UP</td></tr>
                </tbody>
            </table>
        </div>

        <div class="card">
            <h3>Firewall & Routing Policies</h3>
            <p style="font-size: 13px; color: #cbd5e1;">
                Stateful inspection enabled. Inbound traffic from WAN routed through 10.10.0.0/24 Core.
                DHCP Server active on AdminPrivate (172.16.204.100 - 172.16.204.200).
            </p>
            <div class="flag-box">
                <strong>[APPLIANCE TARGET FLAG]:</strong><br>
                <span>FLAG{{pfSense_Appliance_Team{TEAM_ID}_b9e14a2c}}</span>
            </div>
        </div>
    </div>
</body>
</html>
"""

class PfSenseHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            data = {
                "router": ROUTER_NAME,
                "team_id": TEAM_ID,
                "status": "UP",
                "interfaces": {
                    "wan": f"10.10.1{int(TEAM_ID):02d}.2",
                    "vlan20": "172.16.20.1",
                    "vlan201": "172.16.201.1",
                    "vlan202": "172.16.202.1",
                    "vlan203": "172.16.203.1",
                    "vlan204": "172.16.204.1"
                }
            }
            self.wfile.write(json.dumps(data).encode("utf-8"))
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))

    def log_message(self, format, *args):
        return # Quiet logging

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "80"))
    server = HTTPServer(("0.0.0.0", port), PfSenseHandler)
    print(f"[{ROUTER_NAME}] pfSense Web Interface running on port {port}")
    server.serve_forever()

