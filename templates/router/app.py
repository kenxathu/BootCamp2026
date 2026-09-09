import os
import sys
import json
import base64
import hmac
import hashlib
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

TEAM_ID = os.environ.get("TEAM_ID", "01")
tid_int = int(TEAM_ID)
ROUTER_NAME = f"pfSense-Team{tid_int:02d}"
ADMIN_USER = os.environ.get("PFSENSE_ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("PFSENSE_ADMIN_PASSWORD", "pfsense")
SECRET_KEY = os.environ.get("ARENA_SECRET_KEY", "CyberRange2026_SecretKey_TopSecret")
FLAG = os.environ.get("FLAG", f"FLAG{{pfSense_Appliance_Team{tid_int:02d}_b9e14a2c}}")

def create_session_token(username: str) -> str:
    sig = hmac.new(SECRET_KEY.encode("utf-8"), f"pfsense:{username}:{ADMIN_PASSWORD}".encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{username}.{sig}"

def verify_session_token(token: str) -> bool:
    if not token or "." not in token:
        return False
    parts = token.split(".", 1)
    if len(parts) != 2:
        return False
    user, sig = parts
    if user != ADMIN_USER:
        return False
    expected = hmac.new(SECRET_KEY.encode("utf-8"), f"pfsense:{user}:{ADMIN_PASSWORD}".encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(sig, expected)

def render_login_html(error_msg: str = "") -> str:
    error_box = ""
    if error_msg:
        error_box = f"""
        <div class="error-banner">
            ⚠️ <strong>Login Failed:</strong> {error_msg}
        </div>
        """
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>pfSense - Login | {ROUTER_NAME}</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #0b1120;
            color: #f8fafc;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }}
        .login-card {{
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 10px;
            width: 100%;
            max-width: 420px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            overflow: hidden;
        }}
        .header {{
            background: #0f172a;
            padding: 24px 28px;
            border-bottom: 2px solid #0284c7;
            text-align: center;
        }}
        .header .logo {{
            font-size: 26px;
            font-weight: 800;
            color: #38bdf8;
            letter-spacing: 0.5px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }}
        .header .subtitle {{
            font-size: 13px;
            color: #94a3b8;
            margin-top: 6px;
        }}
        .body {{
            padding: 28px;
        }}
        .error-banner {{
            background: #450a0a;
            border: 1px solid #ef4444;
            color: #fca5a5;
            padding: 12px 14px;
            border-radius: 6px;
            font-size: 13px;
            margin-bottom: 20px;
        }}
        .form-group {{
            margin-bottom: 18px;
        }}
        label {{
            display: block;
            font-size: 13px;
            font-weight: 600;
            color: #cbd5e1;
            margin-bottom: 6px;
        }}
        input[type="text"], input[type="password"] {{
            width: 100%;
            padding: 10px 14px;
            background: #0f172a;
            border: 1px solid #475569;
            border-radius: 6px;
            color: #f8fafc;
            font-size: 14px;
            outline: none;
            transition: border-color 0.2s;
        }}
        input[type="text"]:focus, input[type="password"]:focus {{
            border-color: #38bdf8;
            box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2);
        }}
        .btn-submit {{
            width: 100%;
            background: #0284c7;
            color: #ffffff;
            border: none;
            padding: 12px;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 700;
            cursor: pointer;
            transition: background 0.2s;
            margin-top: 8px;
        }}
        .btn-submit:hover {{
            background: #0369a1;
        }}
        .footer {{
            background: #0f172a;
            padding: 14px 20px;
            border-top: 1px solid #334155;
            font-size: 12px;
            color: #64748b;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="login-card">
        <div class="header">
            <div class="logo">
                <span>🛡️</span> pfSense<span style="color:#f8fafc;">®</span>
            </div>
            <div class="subtitle">Community Edition • Inter-VLAN Gateway</div>
        </div>
        <div class="body">
            {error_box}
            <form action="/login" method="POST">
                <div class="form-group">
                    <label for="username">Username</label>
                    <input type="text" id="username" name="username" placeholder="admin" autofocus required>
                </div>
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" placeholder="••••••••" required>
                </div>
                <button type="submit" class="btn-submit">Sign In to pfSense</button>
            </form>
        </div>
        <div class="footer">
            <span>Node: <strong>{ROUTER_NAME}.arena.local</strong></span><br>
            <span>WAN IP: <strong>10.10.1{tid_int:02d}.2</strong> | Team {tid_int:02d}</span>
        </div>
    </div>
</body>
</html>
"""

def render_dashboard_html() -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{ROUTER_NAME} | Netgate pfSense Inter-VLAN Router</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }}
        .navbar {{ background: #1e293b; padding: 15px 25px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; border-left: 5px solid #22c55e; }}
        .brand {{ font-size: 20px; font-weight: bold; color: #38bdf8; display: flex; align-items: center; gap: 10px; }}
        .badge {{ background: #15803d; color: white; padding: 4px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; }}
        .user-info {{ display: flex; align-items: center; gap: 15px; font-size: 14px; }}
        .btn-logout {{ background: #dc2626; color: white; text-decoration: none; padding: 6px 12px; border-radius: 4px; font-size: 12px; font-weight: bold; transition: background 0.2s; }}
        .btn-logout:hover {{ background: #b91c1c; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 20px; margin-top: 20px; }}
        .card {{ background: #1e293b; border-radius: 8px; padding: 20px; border: 1px solid #334155; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }}
        .card h3 {{ margin-top: 0; color: #38bdf8; border-bottom: 1px solid #334155; padding-bottom: 8px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 13px; }}
        th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #334155; }}
        th {{ color: #94a3b8; }}
        .status-up {{ color: #4ade80; font-weight: bold; }}
        .flag-box {{ background: #450a0a; border: 1px dashed #ef4444; padding: 12px; border-radius: 6px; margin-top: 15px; font-family: monospace; word-break: break-all; }}
    </style>
</head>
<body>
    <div class="navbar">
        <div class="brand">
            <span>🛡️ Netgate pfSense (Community Edition)</span>
            <span class="badge">ONLINE</span>
        </div>
        <div class="user-info">
            <span>Host: <strong>{ROUTER_NAME}.arena.local</strong></span> | 
            <span>WAN IP: <strong>10.10.1{tid_int:02d}.2</strong></span> |
            <span>User: <strong>👤 {ADMIN_USER}</strong></span>
            <a href="/logout" class="btn-logout">Sign Out</a>
        </div>
    </div>

    <div class="grid">
        <div class="card">
            <h3>System Information</h3>
            <table>
                <tr><td>Hostname</td><td><strong>{ROUTER_NAME}</strong></td></tr>
                <tr><td>Role</td><td>Inter-VLAN 802.1Q Router & Firewall</td></tr>
                <tr><td>OS Version</td><td>pfSense 2.7.2-RELEASE (FreeBSD 14-CURRENT)</td></tr>
                <tr><td>Uptime</td><td>Active (Cyber Range Simulation)</td></tr>
                <tr><td>Arena Team</td><td><strong>Team {tid_int:02d}</strong></td></tr>
                <tr><td>Admin Account</td><td><code>{ADMIN_USER}</code></td></tr>
            </table>
        </div>

        <div class="card">
            <h3>Inter-VLAN Interfaces</h3>
            <table>
                <thead><tr><th>VLAN</th><th>Name</th><th>Subnet / Gateway</th><th>Status</th></tr></thead>
                <tbody>
                    <tr><td>WAN</td><td>Arena Distribution</td><td>10.10.1{tid_int:02d}.2/24</td><td class="status-up">UP</td></tr>
                    <tr><td>VLAN 20</td><td>KH (Khách hàng)</td><td>172.16.20.1/24</td><td class="status-up">UP</td></tr>
                    <tr><td>VLAN 201</td><td>SCB_VLAN201 (Edge/Git)</td><td>172.16.201.1/24</td><td class="status-up">UP</td></tr>
                    <tr><td>VLAN 202</td><td>SCB_VLAN202 (CI/CD)</td><td>172.16.202.1/24</td><td class="status-up">UP</td></tr>
                    <tr><td>VLAN 203</td><td>SCB_VLAN203 (Ops/DNS)</td><td>172.16.203.1/24</td><td class="status-up">UP</td></tr>
                    <tr><td>VLAN 204</td><td>AdminPrivate (DHCP)</td><td>172.16.204.1/24</td><td class="status-up">UP</td></tr>
                </tbody>
            </table>
        </div>

        <div class="card">
            <h3>Firewall & Routing Policies</h3>
            <p style="font-size: 13px; color: #cbd5e1;">
                Stateful inspection enabled. Inbound traffic from WAN routed through 10.10.0.0/24 Core.
                DHCP Server active on AdminPrivate (172.16.204.100 - 172.16.204.200).
            </p>
            <div class="flag-box">
                <strong>[APPLIANCE TARGET FLAG]:</strong><br>
                <span>{FLAG}</span>
            </div>
        </div>
    </div>
</body>
</html>
"""

class PfSenseHandler(BaseHTTPRequestHandler):
    def is_authenticated(self) -> bool:
        # Check HTTP Basic Auth header
        auth_header = self.headers.get("Authorization")
        if auth_header and auth_header.startswith("Basic "):
            try:
                b64_val = auth_header[6:].strip()
                decoded = base64.b64decode(b64_val).decode("utf-8", errors="replace")
                if ":" in decoded:
                    user, pwd = decoded.split(":", 1)
                    if user == ADMIN_USER and pwd == ADMIN_PASSWORD:
                        return True
            except Exception:
                pass

        # Check session cookie
        cookie_header = self.headers.get("Cookie", "")
        for item in cookie_header.split(";"):
            item = item.strip()
            if item.startswith("pfsense_session="):
                token = item.split("=", 1)[1]
                if verify_session_token(token):
                    return True

        return False

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # Unauthenticated health check endpoint
        if path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "UP", "team": tid_int}).encode("utf-8"))
            return

        # Status API endpoint
        if path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            is_auth = self.is_authenticated()
            data = {
                "router": ROUTER_NAME,
                "team_id": tid_int,
                "status": "UP",
                "authenticated": is_auth,
                "interfaces": {
                    "wan": f"10.10.1{tid_int:02d}.2",
                    "vlan20": "172.16.20.1",
                    "vlan201": "172.16.201.1",
                    "vlan202": "172.16.202.1",
                    "vlan203": "172.16.203.1",
                    "vlan204": "172.16.204.1"
                }
            }
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return

        # Logout endpoint
        if path == "/logout":
            self.send_response(302)
            self.send_header("Location", "/login")
            self.send_header("Set-Cookie", "pfsense_session=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT; HttpOnly")
            self.end_headers()
            return

        # Login page endpoint
        if path == "/login":
            if self.is_authenticated():
                self.send_response(302)
                self.send_header("Location", "/")
                self.end_headers()
                return
            html = render_login_html()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
            return

        # Main root or other pages: require authentication
        if self.is_authenticated():
            html = render_dashboard_html()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
        else:
            # Render login page
            html = render_login_html()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/login":
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len).decode("utf-8", errors="replace")
            params = urllib.parse.parse_qs(post_body)
            username = params.get("username", [""])[0]
            password = params.get("password", [""])[0]

            if username == ADMIN_USER and password == ADMIN_PASSWORD:
                token = create_session_token(username)
                self.send_response(302)
                self.send_header("Location", "/")
                self.send_header("Set-Cookie", f"pfsense_session={token}; Path=/; HttpOnly")
                self.end_headers()
            else:
                html = render_login_html(error_msg="Invalid username or password.")
                self.send_response(401)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(html.encode("utf-8"))
            return

        # Default fallback
        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        return # Quiet logging

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "80"))
    server = HTTPServer(("0.0.0.0", port), PfSenseHandler)
    print(f"[{ROUTER_NAME}] pfSense Web Interface running on port {port}")
    print(f"[{ROUTER_NAME}] Admin User: {ADMIN_USER} | Password: {'*' * len(ADMIN_PASSWORD)}")
    server.serve_forever()

