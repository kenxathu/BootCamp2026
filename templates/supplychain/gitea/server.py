import os
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

TEAM_ID = os.environ.get("TEAM_ID", "01")

GITEA_HTML = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Gitea: Git with a cup of tea - Team {TEAM_ID}</title>
    <style>
        body {{ font-family: sans-serif; margin: 0; background: #2e3440; color: #eceff4; }}
        .nav {{ background: #242933; padding: 15px 30px; display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #88c0d0; }}
        .content {{ padding: 30px; max-width: 900px; margin: 0 auto; }}
        .repo-card {{ background: #3b4252; padding: 15px; border-radius: 6px; margin-bottom: 12px; }}
        a {{ color: #88c0d0; text-decoration: none; }}
    </style>
</head>
<body>
    <div class="nav">
        <h2>🍵 Gitea - SCB_VLAN201 (Team {TEAM_ID})</h2>
        <span>IP: <strong>172.16.201.103</strong></span>
    </div>
    <div class="content">
        <h3>Repositories:</h3>
        <div class="repo-card">
            <h4>📦 <a href="/repo/scb-core-banking">scb-core-banking</a></h4>
            <p>Production codebase for customer Web-AIO portal.</p>
        </div>
        <div class="repo-card">
            <h4>📦 <a href="/repo/devops-k3s-gitops">devops-k3s-gitops</a></h4>
            <p>ArgoCD sync manifests and deployment scripts.</p>
        </div>
    </div>
</body>
</html>
"""

class GiteaHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health" or self.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"service": "gitea", "status": "UP"}).encode("utf-8"))
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(GITEA_HTML.encode("utf-8"))

    def log_message(self, format, *args):
        return

def ssh_mock(port: int):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", port))
    sock.listen(16)
    while True:
        c, _ = sock.accept()
        try:
            c.sendall(b"SSH-2.0-Gitea-GitSSH\r\n")
        except Exception:
            pass
        finally:
            c.close()

if __name__ == "__main__":
    t = threading.Thread(target=ssh_mock, args=(2222,), daemon=True)
    t.start()

    httpd = HTTPServer(("0.0.0.0", 3000), GiteaHandler)
    print(f"[Gitea-Team{TEAM_ID}] Web interface running on port 3000")
    httpd.serve_forever()

