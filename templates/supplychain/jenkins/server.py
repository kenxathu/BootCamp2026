import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

TEAM_ID = os.environ.get("TEAM_ID", "01")
FLAG = os.environ.get("FLAG_JENKINS", f"FLAG{{Jenkins_SupplyChain_Team{TEAM_ID}_8f39c2d1}}")

JENKINS_HTML = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Dashboard [Jenkins] - Team {TEAM_ID}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; background: #f8fafc; }}
        .header {{ background: #1f2937; color: white; padding: 12px 24px; display: flex; justify-content: space-between; align-items: center; }}
        .logo {{ font-size: 20px; font-weight: bold; color: #f97316; display: flex; align-items: center; gap: 8px; }}
        .content {{ padding: 24px; max-width: 1000px; margin: 0 auto; }}
        .card {{ background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 10px; border-bottom: 1px solid #e2e8f0; text-align: left; }}
        .status-ok {{ color: #16a34a; font-weight: bold; }}
        .flag-box {{ background: #fef2f2; border-left: 4px solid #ef4444; padding: 12px; margin-top: 15px; font-family: monospace; color: #991b1b; }}
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">⚙️ Jenkins CI/CD Enterprise [Team {TEAM_ID}]</div>
        <div><span>Target: <strong>SCB_VLAN202</strong> (172.16.202.105)</span></div>
    </div>
    <div class="content">
        <div class="card">
            <h2>CI/CD Pipelines & Supply Chain Status</h2>
            <p>Monitored Ports: <strong>8000</strong> (API/Webhook) | <strong>8080</strong> (Web Dashboard)</p>
            <table>
                <thead><tr><th>Pipeline Name</th><th>Branch</th><th>Last Build</th><th>Health</th></tr></thead>
                <tbody>
                    <tr><td><strong>prod-web-aio-deploy</strong></td><td>main</td><td>#142 (Success)</td><td class="status-ok">100% Passing</td></tr>
                    <tr><td><strong>npm-internal-publish</strong></td><td>release</td><td>#88 (Success)</td><td class="status-ok">100% Passing</td></tr>
                    <tr><td><strong>k8s-manifest-sync</strong></td><td>develop</td><td>#412 (Success)</td><td class="status-ok">100% Passing</td></tr>
                </tbody>
            </table>

            <div class="flag-box">
                <strong>[SERVER TARGET - JENKINS PIPELINE SECRET LEAK]:</strong><br>
                <span>{FLAG}</span>
            </div>
        </div>
    </div>
</body>
</html>
"""

class JenkinsWebHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health" or self.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"service": "jenkins", "status": "UP", "team_id": TEAM_ID}).encode("utf-8"))
        elif self.path == "/job/credentials/secret":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(FLAG.encode("utf-8"))
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(JENKINS_HTML.encode("utf-8"))

    def log_message(self, format, *args):
        return

class JenkinsWebhookHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({
            "service": "jenkins-webhook-engine",
            "port": 8000,
            "status": "READY",
            "team_id": TEAM_ID
        }).encode("utf-8"))

    def do_POST(self):
        self.send_response(202)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"msg": "Build triggered successfully"}).encode("utf-8"))

    def log_message(self, format, *args):
        return

def run_webhook():
    httpd = HTTPServer(("0.0.0.0", 8000), JenkinsWebhookHandler)
    print(f"[Jenkins-Team{TEAM_ID}] Webhook/API listening on port 8000")
    httpd.serve_forever()

if __name__ == "__main__":
    t = threading.Thread(target=run_webhook, daemon=True)
    t.start()

    httpd = HTTPServer(("0.0.0.0", 8080), JenkinsWebHandler)
    print(f"[Jenkins-Team{TEAM_ID}] Web dashboard listening on port 8080")
    httpd.serve_forever()
