import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

TEAM_ID = os.environ.get("TEAM_ID", "01")
FLAG = os.environ.get("FLAG_EDGE", f"FLAG{{EDGE_Proxy_Appliance_Team{TEAM_ID}_3b79a812}}")

PROXY_HTML = f"""<!DOCTYPE html>
<html>
<head><title>EDGE-Proxy - SCB_VLAN201 Team {TEAM_ID}</title></head>
<body style="font-family:sans-serif;background:#0d1117;color:#c9d1d9;padding:25px;">
    <h2>🌐 EDGE Reverse Proxy & Ingress Gateway (Team {TEAM_ID})</h2>
    <p>Location: <strong>SCB_VLAN201 (172.16.201.102)</strong></p>
    <p>Upstream routes:</p>
    <ul>
        <li><code>/git</code> &rarr; Gitea (172.16.201.103:3000)</li>
        <li><code>/ci</code> &rarr; Jenkins (172.16.202.105:8080)</li>
        <li><code>/portal</code> &rarr; Web-AIO (172.16.20.101:80)</li>
    </ul>
    <div style="background:#3b1114;border:1px dashed #f85149;padding:12px;margin-top:20px;color:#ff7b72;">
        [APPLIANCE TARGET - EDGE PROXY SSL LEAK]:<br>
        <code>{FLAG}</code>
    </div>
</body>
</html>"""

class ProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health" or self.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"service": "edge-proxy", "team": TEAM_ID, "status": "UP"}).encode("utf-8"))
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(PROXY_HTML.encode("utf-8"))

    def log_message(self, format, *args):
        return

if __name__ == "__main__":
    httpd = HTTPServer(("0.0.0.0", 80), ProxyHandler)
    print(f"[EDGE-Proxy-Team{TEAM_ID}] Listening on port 80")
    httpd.serve_forever()
