import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

TEAM_ID = os.environ.get("TEAM_ID", "01")

class AppRunnerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({
            "service": "app-runner",
            "team_id": TEAM_ID,
            "vlan": "SCB_VLAN203",
            "status": "HEALTHY",
            "runtime": "Python 3.11 / Microservices Worker"
        }).encode("utf-8"))

    def log_message(self, format, *args):
        return

if __name__ == "__main__":
    httpd = HTTPServer(("0.0.0.0", 5000), AppRunnerHandler)
    print(f"[App-Runner-Team{TEAM_ID}] Running on port 5000")
    httpd.serve_forever()
