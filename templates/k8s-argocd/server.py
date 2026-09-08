import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

TEAM_ID = os.environ.get("TEAM_ID", "01")
FLAG = os.environ.get("FLAG_K8S", f"FLAG{{K3s_ArgoCD_ClusterAdmin_Team{TEAM_ID}_9b42e7a0}}")

ARGOCD_HTML = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Argo CD - Team {TEAM_ID}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #001529; color: #fff; margin: 0; padding: 25px; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1890ff; padding-bottom: 15px; }}
        .card {{ background: #141f2d; border-radius: 8px; padding: 20px; margin-top: 20px; border: 1px solid #22354d; }}
        .badge {{ background: #52c41a; padding: 3px 8px; border-radius: 4px; font-size: 12px; }}
        .flag-box {{ background: #2a1215; border-left: 4px solid #ff4d4f; padding: 12px; margin-top: 20px; font-family: monospace; color: #ff7875; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        th, td {{ padding: 10px; border-bottom: 1px solid #22354d; text-align: left; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>🐙 ArgoCD GitOps Engine (Team {TEAM_ID})</h2>
        <div><span>Server K8s Target (172.16.202.106)</span></div>
    </div>
    <div class="card">
        <h3>Applications</h3>
        <table>
            <thead><tr><th>App Name</th><th>Project</th><th>Status</th><th>Health</th><th>Repository</th></tr></thead>
            <tbody>
                <tr><td>web-aio-prod</td><td>default</td><td><span class="badge">Synced</span></td><td><span class="badge">Healthy</span></td><td>gitea.arena.local/scb-core</td></tr>
                <tr><td>payment-service</td><td>default</td><td><span class="badge">Synced</span></td><td><span class="badge">Healthy</span></td><td>gitea.arena.local/payment</td></tr>
            </tbody>
        </table>

        <div class="flag-box">
            <strong>[SERVER K8S TARGET - CLUSTER ADMIN TOKEN]:</strong><br>
            <span>{FLAG}</span>
        </div>
    </div>
</body>
</html>
"""

class ArgoCDHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health" or self.path == "/api/version":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"service": "argocd", "status": "UP"}).encode("utf-8"))
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(ARGOCD_HTML.encode("utf-8"))

    def log_message(self, format, *args):
        return

class K8sApiHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({
            "apiVersion": "v1",
            "cluster": f"k3s-team{TEAM_ID}",
            "status": "Ready",
            "k8s_version": "v1.28.2+k3s1"
        }).encode("utf-8"))

    def log_message(self, format, *args):
        return

def run_k8s_api():
    httpd = HTTPServer(("0.0.0.0", 6443), K8sApiHandler)
    print(f"[K3s-Team{TEAM_ID}] K8s API server running on port 6443")
    httpd.serve_forever()

if __name__ == "__main__":
    t = threading.Thread(target=run_k8s_api, daemon=True)
    t.start()

    httpd = HTTPServer(("0.0.0.0", 8080), ArgoCDHandler)
    print(f"[K3s-Team{TEAM_ID}] ArgoCD Web running on port 8080")
    httpd.serve_forever()

