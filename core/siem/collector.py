import socket
import threading
import time
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from collections import deque

log_buffer = deque(maxlen=200)

SIEM_HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Wazuh / Arena SIEM Log Collector (10.10.0.8)</title>
    <style>
        body { font-family: monospace; background: #0a0e17; color: #00ff66; margin: 0; padding: 20px; }
        .header { background: #162032; padding: 15px 25px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; color: #38bdf8; }
        .log-box { background: #05080f; border: 1px solid #1e293b; border-radius: 6px; padding: 15px; margin-top: 20px; height: 600px; overflow-y: auto; }
        .log-entry { margin-bottom: 6px; border-bottom: 1px dotted #1f293d; padding-bottom: 4px; font-size: 13px; }
        .ts { color: #94a3b8; }
        .src { color: #fbbf24; font-weight: bold; }
    </style>
    <script>
        setInterval(() => window.location.reload(), 5000);
    </script>
</head>
<body>
    <div class="header">
        <div>
            <h2>🛡️ ARENA SIEM & LOG AGGREGATOR (10.10.0.8)</h2>
            <span>Hạ tầng BTC | Giám sát luồng tấn công & an ninh toàn sàn đấu</span>
        </div>
        <div>
            <span>Syslog UDP/TCP: <strong>514</strong> | Status: <strong>ONLINE</strong></span>
        </div>
    </div>
    <div class="log-box">
        <!-- LOGS -->
    </div>
</body>
</html>
"""

class SIEMWebHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/logs":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(list(log_buffer)).encode("utf-8"))
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            entries = ""
            for entry in reversed(log_buffer):
                entries += f"<div class='log-entry'><span class='ts'>[{entry['time']}]</span> <span class='src'>[{entry['source']}]</span>: {entry['msg']}</div>"
            if not entries:
                entries = "<div class='log-entry' style='color:#64748b;'>Waiting for incoming syslog messages from pfSense and team nodes...</div>"
            page = SIEM_HTML.replace("<!-- LOGS -->", entries)
            self.wfile.write(page.encode("utf-8"))

    def log_message(self, format, *args):
        return

def udp_syslog_listener():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", 514))
    print("[SIEM] Syslog UDP listening on port 514")
    while True:
        try:
            data, addr = sock.recvfrom(2048)
            msg = data.decode("utf-8", errors="replace").strip()
            log_buffer.append({
                "time": time.strftime("%X"),
                "source": f"{addr[0]}:{addr[1]}",
                "msg": msg
            })
        except Exception:
            pass

if __name__ == "__main__":
    t = threading.Thread(target=udp_syslog_listener, daemon=True)
    t.start()

    # Pre-populate sample audit trail
    log_buffer.append({"time": time.strftime("%X"), "source": "10.10.0.1 (Core-L3)", "msg": "Arena Distribution core routing active for subnets 10.10.101.0/24 - 10.10.127.0/24"})
    log_buffer.append({"time": time.strftime("%X"), "source": "10.10.0.10 (CTFd)", "msg": "Competition engine online. Awaiting team connections."})

    httpd = HTTPServer(("0.0.0.0", 5601), SIEMWebHandler)
    print("[SIEM] Web UI listening on port 5601")
    httpd.serve_forever()

