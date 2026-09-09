#!/usr/bin/env python3
"""
Automated in-memory test suite for pfSense WebGUI authentication and session management.
Runs cleanly in sandboxed environments without opening live network sockets.
"""
import os
import sys
import io
import json
import base64
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "templates" / "router"))

# Set test environment variables
os.environ["TEAM_ID"] = "01"
os.environ["PFSENSE_ADMIN_USER"] = "admin"
os.environ["PFSENSE_ADMIN_PASSWORD"] = "ArenaSecret@2026!pf"
os.environ["PORT"] = "80"
os.environ["FLAG"] = "FLAG{pfSense_Appliance_Team01_TESTFLAG123}"

import app

class MockSocket:
    def __init__(self, request_bytes: bytes):
        self.rfile = io.BytesIO(request_bytes)
        self.wfile = io.BytesIO()

    def makefile(self, mode, *args, **kwargs):
        if "r" in mode:
            return self.rfile
        elif "w" in mode:
            return self.wfile
        return self.rfile

    def sendall(self, data):
        self.wfile.write(data)

def simulate_http_request(raw_request: bytes) -> tuple:
    """Simulates an HTTP request through PfSenseHandler and returns (status_code, headers, body)."""
    sock = MockSocket(raw_request)
    client_address = ("127.0.0.1", 54321)
    
    # Instantiate handler with mock socket
    app.PfSenseHandler(sock, client_address, None)
    
    output = sock.wfile.getvalue().decode("utf-8", errors="replace")
    lines = output.split("\r\n")
    status_line = lines[0]
    status_code = int(status_line.split()[1]) if len(status_line.split()) > 1 else 0
    
    headers = {}
    body_idx = 0
    for i, line in enumerate(lines[1:], 1):
        if line == "":
            body_idx = i + 1
            break
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip().lower()] = v.strip()
            
    body = "\r\n".join(lines[body_idx:])
    return status_code, headers, body

def run_tests():
    print("=== STARTING IN-MEMORY PFSENSE AUTHENTICATION TESTS ===")

    # 1. Test session token creation and verification
    print("[1] Testing Session Token cryptographic verification...")
    token = app.create_session_token("admin")
    assert app.verify_session_token(token) is True, "Valid admin token failed verification"
    assert app.verify_session_token("admin.invalidsignature") is False, "Forged token passed verification"
    assert app.verify_session_token("hacker." + token.split(".")[1]) is False, "Wrong user passed verification"
    assert app.verify_session_token("") is False, "Empty token passed verification"
    assert app.verify_session_token("admin") is False, "Malformed token passed verification"
    print("    -> PASS: HMAC session token generation and verification are cryptographically secure!")

    # 2. Test Unauthenticated GET /
    print("\n[2] Testing Unauthenticated GET / ...")
    raw = b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n"
    status, headers, body = simulate_http_request(raw)
    assert status == 200, f"Expected 200, got {status}"
    assert "Sign In to pfSense" in body, "Login page not displayed"
    assert "FLAG{pfSense_Appliance_Team01_TESTFLAG123}" not in body, "SECURITY LEAK: Appliance Flag exposed unauthenticated!"
    print("    -> PASS: Unauthenticated user sees login form; Appliance Flag is hidden.")

    # 3. Test GET /health (unauthenticated liveness probe)
    print("\n[3] Testing GET /health ...")
    raw = b"GET /health HTTP/1.1\r\nHost: localhost\r\n\r\n"
    status, headers, body = simulate_http_request(raw)
    assert status == 200
    data = json.loads(body)
    assert data["status"] == "UP"
    assert data["team"] == 1
    print("    -> PASS: Liveness probe /health returns status UP without requiring auth.")

    # 4. Test GET /api/status unauthenticated
    print("\n[4] Testing GET /api/status (unauthenticated) ...")
    raw = b"GET /api/status HTTP/1.1\r\nHost: localhost\r\n\r\n"
    status, headers, body = simulate_http_request(raw)
    assert status == 200
    data = json.loads(body)
    assert data["authenticated"] is False
    assert data["router"] == "pfSense-Team01"
    print("    -> PASS: /api/status correctly indicates unauthenticated status.")

    # 5. Test POST /login with INVALID credentials
    print("\n[5] Testing POST /login with INVALID credentials ...")
    payload = b"username=admin&password=wrongpassword"
    raw = (
        b"POST /login HTTP/1.1\r\n"
        b"Host: localhost\r\n"
        b"Content-Type: application/x-www-form-urlencoded\r\n"
        b"Content-Length: " + str(len(payload)).encode() + b"\r\n\r\n" +
        payload
    )
    status, headers, body = simulate_http_request(raw)
    assert status == 401, f"Expected 401, got {status}"
    assert "Invalid username or password" in body
    assert "Set-Cookie" not in headers
    print("    -> PASS: Incorrect password rejected with HTTP 401.")

    # 6. Test POST /login with VALID credentials
    print("\n[6] Testing POST /login with VALID credentials ...")
    payload = b"username=admin&password=ArenaSecret%402026%21pf"
    raw = (
        b"POST /login HTTP/1.1\r\n"
        b"Host: localhost\r\n"
        b"Content-Type: application/x-www-form-urlencoded\r\n"
        b"Content-Length: " + str(len(payload)).encode() + b"\r\n\r\n" +
        payload
    )
    status, headers, body = simulate_http_request(raw)
    assert status == 302, f"Expected 302 redirect, got {status}"
    assert headers.get("location") == "/"
    cookie_header = headers.get("set-cookie", "")
    assert "pfsense_session=" in cookie_header, "pfsense_session cookie not set"
    session_token = cookie_header.split("pfsense_session=")[1].split(";")[0]
    print(f"    -> PASS: Login successful! Received valid session cookie: {session_token[:25]}...")

    # 7. Test GET / with session cookie (Authenticated)
    print("\n[7] Testing GET / with session cookie ...")
    raw = (
        b"GET / HTTP/1.1\r\n"
        b"Host: localhost\r\n"
        b"Cookie: pfsense_session=" + session_token.encode() + b"\r\n\r\n"
    )
    status, headers, body = simulate_http_request(raw)
    assert status == 200
    assert "Host: <strong>pfSense-Team01.arena.local</strong>" in body
    assert "User: <strong>👤 admin</strong>" in body
    assert "Inter-VLAN Interfaces" in body
    assert "FLAG{pfSense_Appliance_Team01_TESTFLAG123}" in body, "Target flag missing from authenticated dashboard!"
    print("    -> PASS: Authenticated user views full pfSense Dashboard and Appliance Flag!")

    # 8. Test HTTP Basic Auth
    print("\n[8] Testing HTTP Basic Auth ...")
    auth_str = base64.b64encode(b"admin:ArenaSecret@2026!pf").decode()
    raw = (
        b"GET / HTTP/1.1\r\n"
        b"Host: localhost\r\n"
        b"Authorization: Basic " + auth_str.encode() + b"\r\n\r\n"
    )
    status, headers, body = simulate_http_request(raw)
    assert status == 200
    assert "FLAG{pfSense_Appliance_Team01_TESTFLAG123}" in body
    print("    -> PASS: HTTP Basic Auth grants immediate access to Dashboard and Flag!")

    # 9. Test GET /logout
    print("\n[9] Testing GET /logout ...")
    raw = (
        b"GET /logout HTTP/1.1\r\n"
        b"Host: localhost\r\n"
        b"Cookie: pfsense_session=" + session_token.encode() + b"\r\n\r\n"
    )
    status, headers, body = simulate_http_request(raw)
    assert status == 302
    assert headers.get("location") == "/login"
    assert "expires=thu, 01 jan 1970" in headers.get("set-cookie", "").lower()
    print("    -> PASS: Logout successfully clears session cookie and redirects to /login.")

    print("\n[SUCCESS] ALL PFSENSE IN-MEMORY AUTHENTICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
