import os
import time
import json
import urllib.parse
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler

SLA_CHECKER_URL = os.environ.get("SLA_CHECKER_URL", "http://sla-checker:8080")

TOTAL_TEAMS = int(os.environ.get("TOTAL_TEAMS", "5"))

# Scoreboard memory store
teams_scores = {}
submissions = []

for tid in range(1, TOTAL_TEAMS + 1):
    tkey = f"team{tid:02d}"
    teams_scores[tkey] = {
        "id": tid,
        "name": f"Team {tid:02d}",
        "score_total": 5000,
        "score_pwn": 0,
        "score_recovery": 0,
        "captures": 0
    }

CTFD_HTML = """<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>CTFd - Đấu Trường An Toàn Thông Tin 2026</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 25px; }
        .nav { background: #1e293b; padding: 16px 28px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; border-left: 5px solid #e11d48; }
        .brand { font-size: 20px; font-weight: bold; color: #fb7185; }
        .grid { display: grid; grid-template-columns: 1fr 2fr; gap: 24px; margin-top: 24px; }
        .card { background: #1e293b; padding: 20px; border-radius: 8px; border: 1px solid #334155; }
        input, select, button { width: 100%; padding: 10px; margin-top: 6px; margin-bottom: 14px; border-radius: 6px; border: 1px solid #475569; background: #0f172a; color: #fff; box-sizing: border-box; }
        button { background: #e11d48; color: white; font-weight: bold; border: none; cursor: pointer; }
        button:hover { background: #be123c; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 13px; }
        th, td { padding: 8px 10px; text-align: left; border-bottom: 1px solid #334155; }
        th { color: #94a3b8; }
        .pts-gold { color: #facc15; font-weight: bold; }
        .alert { padding: 12px; border-radius: 6px; margin-bottom: 15px; }
        .alert-success { background: #064e3b; border: 1px solid #059669; color: #6ee7b7; }
        .alert-info { background: #1e1b4b; border: 1px solid #4338ca; color: #c7d2fe; }
    </style>
    <script>
        setInterval(() => window.location.reload(), 10000);
    </script>
</head>
<body>
    <div class="nav">
        <div class="brand">🚩 CTFd SCOREBOARD & FLAG SUBMISSION (10.10.0.10)</div>
        <div><span>Hạ tầng BTC | Sàn đấu 27 Đội</span></div>
    </div>

    <div class="grid">
        <div class="card">
            <h3>Nộp Flag Tấn Công (Offensive Pwn)</h3>
            <!-- ALERT -->
            <form action="/submit-flag" method="POST">
                <label>Đội của bạn (Attacker):</label>
                <select name="attacker_id">
                    <!-- ATTACKER_OPTIONS -->
                </select>

                <label>Mục tiêu chiếm được (Hạng mục điểm):</label>
                <select name="target_category">
                    <option value="Management">ESXi / vCenter (+1000 điểm)</option>
                    <option value="K8s">Server K8s (+1000 điểm khôi phục / +500 chiếm)</option>
                    <option value="Supply Chain">Server - Supply Chain / Jenkins (+500 điểm)</option>
                    <option value="DC-0153">Server - Active Directory DC-0153 (+500 điểm)</option>
                    <option value="Web-AIO">Server - Customer Web-AIO (+500 điểm)</option>
                    <option value="VPN">Thiết bị - VPN (+300 điểm)</option>
                    <option value="pfSense">Thiết bị - pfSense Router (+300 điểm)</option>
                    <option value="EDGE-Proxy">Thiết bị - EDGE-Proxy (+300 điểm)</option>
                    <option value="WS-01">Máy trạm - WS-01 (+100 điểm)</option>
                    <option value="WS-02">Máy trạm - WS-02 (+100 điểm)</option>
                </select>

                <label>Đội đối phương bị chiếm (Victim):</label>
                <select name="victim_id">
                    <!-- VICTIM_OPTIONS -->
                </select>

                <label>Chuỗi Flag:</label>
                <input type="text" name="flag" placeholder="FLAG{...}" required>

                <button type="submit">Xác Nhận Nộp Flag</button>
            </form>
        </div>

        <div class="card">
            <h3>Bảng Xếp Hạng Trực Tiếp (Live Leaderboard)</h3>
            <table>
                <thead>
                    <tr><th>Hạng</th><th>Đội</th><th>Điểm Tấn Công</th><th>Khôi Phục Dịch Vụ</th><th>Tổng Điểm</th></tr>
                </thead>
                <tbody>
                    <!-- SCORE_ROWS -->
                </tbody>
            </table>

            <h4 style="margin-top:25px;border-top:1px solid #334155;padding-top:15px;">Lịch Sử Nộp Flag Gần Nhất:</h4>
            <table>
                <thead><tr><th>Thời gian</th><th>Đội Tấn Công</th><th>Mục tiêu</th><th>Nạn nhân</th><th>Điểm</th></tr></thead>
                <tbody>
                    <!-- SUBMISSION_ROWS -->
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""

class CTFdHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/scoreboard":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(teams_scores).encode("utf-8"))
        else:
            self.render_page("")

    def do_POST(self):
        if self.path == "/submit-flag":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length).decode("utf-8")
            params = urllib.parse.parse_qs(post_data)
            
            attacker_id = int(params.get("attacker_id", [1])[0])
            victim_id = int(params.get("victim_id", [2])[0])
            target_cat = params.get("target_category", ["Server"])[0]
            flag_val = params.get("flag", [""])[0].strip()

            # Scoring spec
            points = 100
            if "ESXi" in target_cat or target_cat == "Management":
                points = 1000
            elif "K8s" in target_cat:
                points = 1000 if "khôi phục" in target_cat.lower() else 500
            elif "Server" in target_cat or target_cat in ("Supply Chain", "DC-0153", "Web-AIO"):
                points = 500
            elif "Thiết bị" in target_cat or target_cat in ("VPN", "pfSense", "EDGE-Proxy"):
                points = 300
            elif "WS" in target_cat:
                points = 100

            att_key = f"team{attacker_id:02d}"
            teams_scores[att_key]["score_pwn"] += points
            teams_scores[att_key]["score_total"] += points
            teams_scores[att_key]["captures"] += 1

            sub_entry = {
                "time": time.strftime("%X"),
                "attacker": f"Team {attacker_id:02d}",
                "victim": f"Team {victim_id:02d}",
                "target": target_cat,
                "points": points,
                "flag": flag_val
            }
            submissions.insert(0, sub_entry)

            # Inform SLA Checker API
            try:
                req_url = f"{SLA_CHECKER_URL}/api/pwn?attacker_id={attacker_id}&victim_id={victim_id}&target_category={urllib.parse.quote(target_cat)}"
                req = urllib.request.Request(req_url, method="POST")
                urllib.request.urlopen(req, timeout=2.0)
            except Exception:
                pass

            msg = f"<div class='alert alert-success'>✅ Flag chính xác! Team {attacker_id:02d} chiếm thành công {target_cat} của Team {victim_id:02d} (+{points} điểm). [Stealth rule áp dụng: Đội bị chiếm không bị trừ điểm SLA nếu dịch vụ vẫn hoạt động]</div>"
            self.render_page(msg)

    def render_page(self, alert_html=""):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()

        # Build options
        att_opts = ""
        vic_opts = ""
        for i in range(1, TOTAL_TEAMS + 1):
            att_opts += f"<option value='{i}'>Team {i:02d}</option>"
            vic_opts += f"<option value='{i}' {'selected' if i == 2 else ''}>Team {i:02d}</option>"

        # Sort scoreboard
        sorted_teams = sorted(teams_scores.values(), key=lambda t: t["score_total"], reverse=True)
        score_rows = ""
        for rank, t in enumerate(sorted_teams, start=1):
            score_rows += f"<tr><td>{rank}</td><td><strong>{t['name']}</strong></td><td>+{t['score_pwn']} pts</td><td>{t['score_recovery']} pts</td><td class='pts-gold'>{t['score_total']} pts</td></tr>"

        sub_rows = ""
        for s in submissions[:8]:
            sub_rows += f"<tr><td>{s['time']}</td><td><span style='color:#38bdf8;'>{s['attacker']}</span></td><td>{s['target']}</td><td><span style='color:#f87171;'>{s['victim']}</span></td><td>+{s['points']}</td></tr>"
        if not sub_rows:
            sub_rows = "<tr><td colspan='5' style='color:#64748b;'>Chưa có flag nào được nộp.</td></tr>"

        html = CTFD_HTML.replace("<!-- ALERT -->", alert_html)
        html = html.replace("<!-- ATTACKER_OPTIONS -->", att_opts)
        html = html.replace("<!-- VICTIM_OPTIONS -->", vic_opts)
        html = html.replace("<!-- SCORE_ROWS -->", score_rows)
        html = html.replace("<!-- SUBMISSION_ROWS -->", sub_rows)

        self.wfile.write(html.encode("utf-8"))

    def log_message(self, format, *args):
        return

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    server = HTTPServer(("0.0.0.0", port), CTFdHandler)
    print(f"[CTFd] Running on port {port}")
    server.serve_forever()

