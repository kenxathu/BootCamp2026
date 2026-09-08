import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

TEAM_ID = os.environ.get("TEAM_ID", "01")
FLAG = os.environ.get("FLAG_WEB", f"FLAG{{WebAIO_CustomerPortal_Team{TEAM_ID}_1d8a4f9b}}")

HTML_PAGE = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Cổng Giao Dịch Doanh Nghiệp (Web-AIO) - Team {TEAM_ID}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f1f5f9; margin: 0; color: #1e293b; }}
        .header {{ background: #0f766e; color: white; padding: 16px 32px; display: flex; justify-content: space-between; align-items: center; }}
        .container {{ max-width: 1000px; margin: 30px auto; padding: 0 20px; }}
        .card {{ background: white; border-radius: 8px; padding: 24px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; }}
        .grid {{ display: grid; grid-template-columns: 2fr 1fr; gap: 20px; }}
        input, button {{ padding: 10px; border-radius: 6px; border: 1px solid #cbd5e1; }}
        button {{ background: #0f766e; color: white; cursor: pointer; font-weight: bold; border: none; }}
        button:hover {{ background: #115e59; }}
        .flag-box {{ background: #fef2f2; border: 1px solid #f87171; color: #b91c1c; padding: 15px; border-radius: 6px; font-family: monospace; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>🏦 SCB Enterprise Banking Portal [Web-AIO Team {TEAM_ID}]</h2>
        <div>IP: <strong>172.16.20.101</strong> (VLAN 20)</div>
    </div>
    <div class="container">
        <div class="grid">
            <div class="card">
                <h3>Tra cứu thông tin tài khoản doanh nghiệp</h3>
                <p>Nhập mã định danh khách hàng (CIF / Account ID):</p>
                <form action="/search" method="GET">
                    <input type="text" name="cif" placeholder="Nhập CIF: ví dụ CIF9001..." style="width: 70%;" value="">
                    <button type="submit">Truy vấn</button>
                </form>
                <div style="margin-top: 20px;">
                    <h4>Dịch vụ đang trực tuyến:</h4>
                    <ul>
                        <li>Chuyển khoản nội bộ & liên ngân hàng</li>
                        <li>Quản lý nguồn vốn & thanh toán hóa đơn</li>
                        <li>Tích hợp API kết nối cổng thanh toán đối tác</li>
                    </ul>
                </div>
            </div>
            <div class="card">
                <h3>Trạng thái hệ thống</h3>
                <p>Mạng: <strong>VLAN 20 (KH)</strong></p>
                <p>Gateway: <strong>172.16.20.1</strong></p>
                <p>Trạng thái: <strong style="color: #16a34a;">HOẠT ĐỘNG</strong></p>
                <hr>
                <div class="flag-box">
                    <strong>[SERVER TARGET - WEB EXPLOIT FLAG]:</strong><br>
                    <span>{FLAG}</span>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

class WebAIOHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/health" or parsed.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"service": "web-aio", "team": TEAM_ID, "status": "UP"}).encode("utf-8"))
        elif parsed.path == "/search":
            query = urllib.parse.parse_qs(parsed.query)
            cif = query.get("cif", [""])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            result_html = HTML_PAGE + f"<script>alert('Truy vấn CIF: {cif}');</script>"
            self.wfile.write(result_html.encode("utf-8"))
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))

    def log_message(self, format, *args):
        return

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "80"))
    server = HTTPServer(("0.0.0.0", port), WebAIOHandler)
    print(f"[Web-AIO-Team{TEAM_ID}] Running on port {port}")
    server.serve_forever()

