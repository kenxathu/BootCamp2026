import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

TEAM_ID = os.environ.get("TEAM_ID", "01")

class VerdaccioHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health" or self.path == "/-/ping":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode("utf-8"))
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html = f"""<!DOCTYPE html>
<html>
<head><title>Verdaccio Private Registry - Team {TEAM_ID}</title></head>
<body style="font-family:sans-serif;background:#1e1e2f;color:#fff;padding:25px;">
    <h2>📦 Verdaccio Enterprise NPM Registry (Team {TEAM_ID})</h2>
    <p>Location: SCB_VLAN202 (172.16.202.107:4873)</p>
    <ul>
        <li><code>@scb/auth-sdk@1.0.4</code> (Internal authentication module)</li>
        <li><code>@scb/payment-gateway@2.1.0</code> (Core transaction module)</li>
    </ul>
</body>
</html>"""
            self.wfile.write(html.encode("utf-8"))

    def log_message(self, format, *args):
        return

if __name__ == "__main__":
    httpd = HTTPServer(("0.0.0.0", 4873), VerdaccioHandler)
    print(f"[Verdaccio-Team{TEAM_ID}] NPM registry running on port 4873")
    httpd.serve_forever()
