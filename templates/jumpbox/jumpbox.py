import os
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse

TEAM_ID = os.environ.get("TEAM_ID", "01")

HTML = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Team {TEAM_ID} - Red/Blue Console</title>
    <style>
        body {{ font-family: monospace; background: #000; color: #0f0; padding: 20px; }}
        input {{ width: 60%; background: #111; color: #0f0; border: 1px solid #333; padding: 8px; font-family: monospace; }}
        button {{ background: #008800; color: #fff; border: none; padding: 8px 16px; cursor: pointer; font-weight: bold; }}
        pre {{ background: #111; border: 1px solid #222; padding: 15px; color: #0f0; max-height: 400px; overflow-y: auto; }}
    </style>
</head>
<body>
    <h2>💻 Team {TEAM_ID} Terminal Jumpbox (AdminPrivate VLAN 204)</h2>
    <p>Network IP: <strong>172.16.204.100</strong> | Ready for Offensive / Defensive operations.</p>
    <hr>
    <form action="/exec" method="GET">
        <span>$ </span>
        <input type="text" name="cmd" placeholder="e.g. curl http://172.16.20.101/ or nmap -sT 172.16.20.104" autofocus>
        <button type="submit">Run Command</button>
    </form>
    <div style="margin-top:20px;">
        <a href="/target-list" style="color:#0af;">[View Attack Target List for All Teams]</a>
    </div>
</body>
</html>
"""

class JumpboxHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ready", "team": TEAM_ID}).encode("utf-8"))
        elif parsed.path == "/target-list":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            total_teams = int(os.environ.get("TOTAL_TEAMS", "5"))
            for i in range(1, total_teams + 1):
                if f"{i:02d}" != TEAM_ID:
                    targets.append({
                        f"team_{i:02d}": {
                            "pfSense_WAN": f"10.10.1{i:02d}.2",
                            "ESXi_Host": f"10.10.1{i:02d}.3",
                            "VLAN20_KH": f"172.16.20.0/24 (via pfSense)",
                            "VLAN202_SCB": f"172.16.202.0/24"
                        }
                    })
            self.wfile.write(json.dumps(targets, indent=2).encode("utf-8"))
        elif parsed.path == "/exec":
            query = urllib.parse.parse_qs(parsed.query)
            cmd = query.get("cmd", ["echo 'No command'"])[0]
            try:
                out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=10).decode("utf-8", errors="replace")
            except Exception as e:
                out = str(e)
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            resp = HTML + f"<br><h3>Execution Result:</h3><pre>{out}</pre>"
            self.wfile.write(resp.encode("utf-8"))
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(HTML.encode("utf-8"))

    def log_message(self, format, *args):
        return

if __name__ == "__main__":
    httpd = HTTPServer(("0.0.0.0", 8000), JumpboxHandler)
    print(f"[Jumpbox-Team{TEAM_ID}] Terminal ready on port 8000")
    httpd.serve_forever()

