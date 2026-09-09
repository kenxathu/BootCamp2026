#!/usr/bin/env python3
"""
ARENA-CTL: Master Orchestrator for Information Security Cyber Range Arena 2026
Controls BTC Core (10.10.0.0/24), Distribution Routing, and 27 Team Environments.
"""

import os
import sys
import json
import random
import hmac
import hashlib
import subprocess
import argparse
from pathlib import Path

# Fix Windows console encoding for Unicode/Vietnamese text
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent
GENERATED_DIR = BASE_DIR / "generated"
TEMPLATES_DIR = BASE_DIR / "templates"
CORE_DIR = BASE_DIR / "core"
CREDENTIALS_FILE = GENERATED_DIR / "team_credentials.json"

SECRET_KEY = os.environ.get("ARENA_SECRET_KEY", "CyberRange2026_SecretKey_TopSecret")

def ensure_dirs():
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

def generate_flag(team_id: int, target: str) -> str:
    """Generates a cryptographically signed flag for a specific team and target."""
    raw = f"team:{team_id}:{target}:{SECRET_KEY}".encode("utf-8")
    sig = hashlib.sha256(raw).hexdigest()[:12]
    return f"FLAG{{{target}_Team{team_id:02d}_{sig}}}"

def generate_pfsense_password(team_id: int) -> str:
    """Generates a cryptographically derived admin password for pfSense for a team."""
    raw = f"pfsense:admin:team:{team_id}:{SECRET_KEY}".encode("utf-8")
    sig = hashlib.sha256(raw).hexdigest()[:8]
    return f"pfSense@Team{team_id:02d}#{sig}"

def load_all_credentials() -> dict:
    ensure_dirs()
    if CREDENTIALS_FILE.exists():
        try:
            with open(CREDENTIALS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_all_credentials(creds: dict):
    ensure_dirs()
    with open(CREDENTIALS_FILE, "w", encoding="utf-8") as f:
        json.dump(creds, f, indent=2)

def get_or_set_team_pfsense_password(team_id: int, custom_password: str = None) -> str:
    creds = load_all_credentials()
    tkey = f"team{team_id:02d}"
    if tkey not in creds:
        creds[tkey] = {
            "team_id": team_id,
            "wan_ip": f"10.10.1{team_id:02d}.2",
            "pfsense": {}
        }
    
    if custom_password:
        pwd = custom_password
    elif "pfsense" in creds[tkey] and "password" in creds[tkey]["pfsense"] and creds[tkey]["pfsense"]["password"]:
        pwd = creds[tkey]["pfsense"]["password"]
    else:
        pwd = generate_pfsense_password(team_id)

    creds[tkey]["pfsense"] = {
        "url": f"http://10.10.1{team_id:02d}.2:80",
        "username": "admin",
        "password": pwd
    }
    save_all_credentials(creds)
    return pwd

def render_team_compose(team_id: int, mode: str = "multi", pfsense_password: str = None) -> Path:
    """Renders the docker-compose file for a given team."""
    ensure_dirs()
    template_file = TEMPLATES_DIR / "team-compose.template.yml"
    with open(template_file, "r", encoding="utf-8") as f:
        content = f.read()

    tid_str = f"{team_id:02d}"
    
    # In exact mode, single team isolated lab
    if mode == "exact":
        vlan20 = "172.16.20"
        vlan201 = "172.16.201"
        vlan202 = "172.16.202"
        vlan203 = "172.16.203"
        vlan204 = "172.16.204"
    else:
        # Multi-team co-hosting on single bridge engine without namespaces
        # Uses 172.(20+team_id).X to avoid docker0 (172.17.0.0/16) and prevent collisions across teams
        vlan_base = 20 + team_id
        vlan20 = f"172.{vlan_base}.20"
        vlan201 = f"172.{vlan_base}.201"
        vlan202 = f"172.{vlan_base}.202"
        vlan203 = f"172.{vlan_base}.203"
        vlan204 = f"172.{vlan_base}.204"

    # Get pfSense password
    pwd = get_or_set_team_pfsense_password(team_id, custom_password=pfsense_password)

    rendered = content.replace("{{ team_id }}", tid_str)
    rendered = rendered.replace("{{ vlan20_prefix }}", vlan20)
    rendered = rendered.replace("{{ vlan201_prefix }}", vlan201)
    rendered = rendered.replace("{{ vlan202_prefix }}", vlan202)
    rendered = rendered.replace("{{ vlan203_prefix }}", vlan203)
    rendered = rendered.replace("{{ vlan204_prefix }}", vlan204)
    rendered = rendered.replace("{{ pfsense_admin_password }}", pwd)

    out_file = GENERATED_DIR / f"docker-compose.team{tid_str}.yml"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(rendered)

    print(f"[+] Generated team {tid_str} compose: {out_file.name}")
    return out_file

def cmd_generate_flags(args):
    """Generates all challenge flags for all 27 teams."""
    ensure_dirs()
    targets = [
        ("esxi", "ESXi_vCenter_Root", 1000, "ESXi/vCenter Management"),
        ("k8s", "K3s_ArgoCD_ClusterAdmin", 500, "Server K8s"),
        ("jenkins", "Jenkins_SupplyChain", 500, "Server - Supply Chain"),
        ("dc01", "DC0153_DomainAdmin", 500, "Server - Active Directory"),
        ("web_aio", "WebAIO_CustomerPortal", 500, "Server - Web Customer"),
        ("vpn", "VPN_Appliance", 300, "Appliance - VPN"),
        ("pfsense", "pfSense_Appliance", 300, "Appliance - Router"),
        ("edge_proxy", "EDGE_Proxy_Appliance", 300, "Appliance - Reverse Proxy"),
        ("ws01", "WS01_LocalAdmin", 100, "Workstation - WS01"),
        ("ws02", "WS02_FinanceUser", 100, "Workstation - WS02")
    ]

    TOTAL_TEAMS = int(os.environ.get("TOTAL_TEAMS", "5"))
    master_flags = {}
    for tid in range(1, TOTAL_TEAMS + 1):
        tkey = f"team{tid:02d}"
        master_flags[tkey] = {
            "team_id": tid,
            "wan_ip": f"10.10.1{tid:02d}.2",
            "flags": {}
        }
        for code, label, pts, desc in targets:
            flag = generate_flag(tid, label)
            master_flags[tkey]["flags"][code] = {
                "flag": flag,
                "points": pts,
                "description": desc
            }

    flags_file = GENERATED_DIR / "master_flags.json"
    with open(flags_file, "w", encoding="utf-8") as f:
        json.dump(master_flags, f, indent=2)

    print(f"[+] Generated flags for {TOTAL_TEAMS} teams ({TOTAL_TEAMS * len(targets)} total flags) -> {flags_file.name}")

def cmd_spawn_teams(args):
    """Spawns configuration files and pfSense credentials for N teams."""
    count = args.count
    mode = args.mode
    print(f"[*] Generating environments and pfSense admin credentials for {count} teams in '{mode}' mode...")
    for tid in range(1, count + 1):
        render_team_compose(tid, mode=mode)
    print(f"[+] Successfully generated configs for {count} teams in ./generated/")
    print(f"[+] Team credentials saved to {CREDENTIALS_FILE.name}")

def check_docker_daemon() -> bool:
    """Checks if docker engine is running and accessible."""
    try:
        res = subprocess.run(["docker", "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return res.returncode == 0
    except (FileNotFoundError, Exception):
        return False

def get_compose_cmd():
    """Detects whether to use 'docker compose' or 'docker-compose'."""
    try:
        res = subprocess.run(["docker", "compose", "version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0:
            return ["docker", "compose"]
    except Exception:
        pass
    try:
        res = subprocess.run(["docker-compose", "version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0:
            return ["docker-compose"]
    except Exception:
        pass
    return ["docker", "compose"]

def start_native_core():
    """Runs CTFd, SIEM, and SLA Checker as background Python processes."""
    ctfd_script = CORE_DIR / "ctfd" / "app.py"
    siem_script = CORE_DIR / "siem" / "collector.py"
    sla_script = CORE_DIR / "sla-checker" / "checker.py"

    env_ctfd = os.environ.copy()
    env_ctfd["PORT"] = "8000"
    env_ctfd["TOTAL_TEAMS"] = "5"
    env_ctfd["SLA_CHECKER_URL"] = "http://127.0.0.1:8081"

    env_sla = os.environ.copy()
    env_sla["PORT"] = "8081"
    env_sla["TOTAL_TEAMS"] = "5"

    env_siem = os.environ.copy()

    p_ctfd = subprocess.Popen([sys.executable, str(ctfd_script)], env=env_ctfd)
    p_siem = subprocess.Popen([sys.executable, str(siem_script)], env=env_siem)
    p_sla = subprocess.Popen([sys.executable, str(sla_script)], env=env_sla)

    pids_file = BASE_DIR / ".native_core.pids"
    with open(pids_file, "w") as f:
        json.dump({"ctfd": p_ctfd.pid, "siem": p_siem.pid, "sla": p_sla.pid}, f)

    print("\n[+] BTC Core online (Native Mode)!")
    print("    - CTFd Scoreboard:    http://localhost:8000")
    print("    - SIEM Dashboard:     http://localhost:5601")
    print("    - SLA Live Matrix:    http://localhost:8081")
    print("\n    Chạy 'python arena-ctl.py down-all' để dừng toàn bộ dịch vụ.")

def cmd_up_core(args):
    """Starts the BTC Core infrastructure (CTFd, SIEM, SLA Checker)."""
    if getattr(args, "native", False):
        print("[*] Starting BTC Core natively in background processes (Dev/Test mode)...")
        start_native_core()
        return

    if not check_docker_daemon():
        print("[-] Lỗi: Docker Daemon chưa chạy (Docker Engine is not running)!")
        print("    👉 Trên Windows: Vui lòng mở ứng dụng 'Docker Desktop' và chờ biểu tượng cá voi chuyển sang màu xanh.")
        print("    👉 Trên Linux: Chạy lệnh 'sudo systemctl start docker' hoặc 'sudo service docker start'.")
        print("\n    💡 Mẹo: Bạn có thể khởi chạy ngay BTC Core không cần Docker daemon (Local Native Mode) bằng lệnh:")
        print("       python arena-ctl.py up-core --native")
        sys.exit(1)

    core_compose = BASE_DIR / "docker-compose.core.yml"
    print("[*] Starting BTC Core Infrastructure (10.10.0.0/24)...")
    compose_cmd = get_compose_cmd() + ["-f", str(core_compose), "up", "-d", "--build"]
    try:
        subprocess.run(compose_cmd, check=True)
        print("\n[+] BTC Core online!")
        print("    - CTFd Scoreboard:    http://localhost:8000")
        print("    - SIEM Dashboard:     http://localhost:5601")
        print("    - SLA Live Matrix:    http://localhost:8081")
    except subprocess.CalledProcessError as e:
        print(f"[-] Docker compose execution failed with exit code {e.returncode}.")
        sys.exit(1)

def cmd_up_team(args):
    """Starts a specific team environment and displays credentials."""
    tid = args.id
    tid_str = f"{tid:02d}"
    custom_pwd = getattr(args, "password", None)
    
    compose_path = GENERATED_DIR / f"docker-compose.team{tid_str}.yml"
    if custom_pwd or not compose_path.exists():
        compose_path = render_team_compose(tid, pfsense_password=custom_pwd)
    
    pwd = get_or_set_team_pfsense_password(tid, custom_password=custom_pwd)

    print(f"\n{'='*65}")
    print(f"[*] KHỞI CHẠY ĐỘI THI: TEAM {tid_str}")
    print(f"{'='*65}")
    print(f"🛡️  THÔNG TIN QUẢN TRỊ PFSENSE ROUTER (TEAM {tid_str}):")
    print(f"    - WebGUI Dashboard : http://10.10.1{tid_str}.2:80")
    print(f"    - Tên đăng nhập    : admin")
    print(f"    - Mật khẩu quản trị: {pwd}")
    print(f"    - Cờ Appliance     : {generate_flag(tid, 'pfSense_Appliance')}")
    print(f"{'='*65}\n")

    if not check_docker_daemon():
        print("[-] Lỗi: Docker Daemon chưa chạy! Vui lòng khởi động Docker trước khi start đội thi.")
        sys.exit(1)

    compose_cmd = get_compose_cmd() + ["-f", str(compose_path), "up", "-d", "--build"]
    try:
        subprocess.run(compose_cmd, check=True)
        print(f"[+] Team {tid_str} is UP!")
        print(f"[+] pfSense Dashboard online tại http://10.10.1{tid_str}.2 (User: admin / Pass: {pwd})")
    except subprocess.CalledProcessError as e:
        print(f"[-] Starting Team {tid_str} failed with exit code {e.returncode}.")
        sys.exit(1)

def cmd_show_credentials(args):
    """Displays stored credentials for teams."""
    creds = load_all_credentials()
    if not creds:
        print("[-] Chưa có thông tin credentials. Chạy 'spawn-teams' hoặc 'up-team' trước.")
        return

    tid = getattr(args, "id", None)
    print("\n" + "="*68)
    print(" 🛡️  ARENA CYBER RANGE - DANH SÁCH TÀI KHOẢN QUẢN TRỊ ĐỘI THI")
    print("="*68)

    keys = [f"team{tid:02d}"] if tid else sorted(creds.keys())
    for tkey in keys:
        if tkey not in creds:
            print(f"[-] Không tìm thấy thông tin cho {tkey}.")
            continue
        c = creds[tkey]
        pfs = c.get("pfsense", {})
        print(f"\n[TEAM {c.get('team_id', 0):02d}] - IP WAN: {c.get('wan_ip')}")
        print(f"  • pfSense WebGUI : {pfs.get('url', 'N/A')}")
        print(f"  • Tài khoản      : {pfs.get('username', 'admin')}")
        print(f"  • Mật khẩu       : {pfs.get('password', 'N/A')}")
    print("\n" + "="*68)

def cmd_down_all(args):
    """Stops all running containers and cleans up."""
    print("[*] Stopping all Cyber Range components...")
    
    # Stop native core processes if running
    pids_file = BASE_DIR / ".native_core.pids"
    if pids_file.exists():
        try:
            with open(pids_file, "r") as f:
                pids = json.load(f)
            import signal
            for name, pid in pids.items():
                try:
                    if sys.platform == "win32":
                        subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    else:
                        os.kill(pid, signal.SIGTERM)
                    print(f"[+] Stopped native {name} (PID: {pid})")
                except Exception:
                    pass
            pids_file.unlink(missing_ok=True)
        except Exception:
            pass

    if check_docker_daemon():
        compose_bin = get_compose_cmd()
        # Stop all generated team composes
        for compose_file in GENERATED_DIR.glob("docker-compose.team*.yml"):
            print(f"[*] Stopping {compose_file.name}...")
            subprocess.run(compose_bin + ["-f", str(compose_file), "down"], check=False)

        # Stop core
        core_compose = BASE_DIR / "docker-compose.core.yml"
        if core_compose.exists():
            print("[*] Stopping BTC Core...")
            subprocess.run(compose_bin + ["-f", str(core_compose), "down"], check=False)
    print("[+] Arena environment stopped.")

def cmd_sla_status(args):
    """Queries and prints the SLA checker status."""
    import urllib.request
    try:
        url = "http://localhost:8081/api/state"
        req = urllib.request.urlopen(url, timeout=3)
        data = json.loads(req.read().decode("utf-8"))
        print(f"\n=== CYBER RANGE SLA ENGINE (Round #{data['round']}) ===")
        print(f"Teams monitored: {len(data['teams'])}")
        for tkey, t in list(data["teams"].items())[:args.limit]:
            print(f"\n[{t['name']}] Total: {t['score_total']} pts | SLA: {t['score_sla']} | Pwn: {t['score_pwn']}")
            for sname, s in t["services"].items():
                st = "UP" if s["status"] == "UP" else f"DOWN (ports: {s['failed_ports']})"
                print(f"   - {sname:<14}: {st}")
    except Exception as e:
        print(f"[-] Could not query SLA engine at http://localhost:8081: {e}")
        print("    Make sure BTC Core is running (`python arena-ctl.py up-core`).")

def cmd_simulate_attack(args):
    """Simulates an attack, flag submission, and tests stealth rule."""
    import urllib.request
    import urllib.parse
    att = args.attacker
    vic = args.victim
    tgt = args.target

    print(f"[*] Simulating Attack: Team {att:02d} pwning {tgt} on Team {vic:02d}...")
    try:
        url = f"http://localhost:8081/api/pwn?attacker_id={att}&victim_id={vic}&target_category={urllib.parse.quote(tgt)}"
        req = urllib.request.Request(url, method="POST")
        resp = urllib.request.urlopen(req, timeout=3)
        res_data = json.loads(resp.read().decode("utf-8"))
        print("[+] Result from Scoring Engine:")
        print(f"    - Points awarded: +{res_data.get('points_awarded')} pts")
        print(f"    - Stealth rule applied: {res_data.get('stealth_rule_applied')}")
        print(f"    - Message: {res_data.get('message')}")
    except Exception as e:
        print(f"[-] Error contacting scoring engine: {e}")

def main():
    parser = argparse.ArgumentParser(description="Arena Cyber Range CLI Master Controller")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # spawn-teams
    p_spawn = subparsers.add_parser("spawn-teams", help="Generate Docker Compose files for teams")
    p_spawn.add_argument("--count", type=int, default=5, help="Number of teams (default 5)")
    p_spawn.add_argument("--mode", choices=["exact", "multi"], default="multi", help="IP allocation mode (default: multi)")
    p_spawn.set_defaults(func=cmd_spawn_teams)

    # generate-flags
    p_flags = subparsers.add_parser("generate-flags", help="Generate signed flags for all teams")
    p_flags.set_defaults(func=cmd_generate_flags)

    # up-core
    p_up_core = subparsers.add_parser("up-core", help="Start BTC Core (CTFd, SIEM, SLA Checker)")
    p_up_core.add_argument("--native", action="store_true", help="Run BTC Core as native Python services without Docker")
    p_up_core.set_defaults(func=cmd_up_core)

    # up-team
    p_up_team = subparsers.add_parser("up-team", help="Start a specific team stack")
    p_up_team.add_argument("--id", type=int, required=True, help="Team ID (e.g. 1-5)")
    p_up_team.add_argument("--password", "--pfsense-password", dest="password", default=None, help="Custom pfSense admin password for this team")
    p_up_team.set_defaults(func=cmd_up_team)

    # credentials
    p_creds = subparsers.add_parser("credentials", help="View admin credentials for teams")
    p_creds.add_argument("--id", type=int, default=None, help="Team ID (optional, defaults to all teams)")
    p_creds.set_defaults(func=cmd_show_credentials)

    # down-all
    p_down = subparsers.add_parser("down-all", help="Stop all arena containers")
    p_down.set_defaults(func=cmd_down_all)

    # sla-status
    p_sla = subparsers.add_parser("sla-status", help="Print live SLA status table")
    p_sla.add_argument("--limit", type=int, default=5, help="Number of teams to show in terminal")
    p_sla.set_defaults(func=cmd_sla_status)

    # simulate-attack
    p_atk = subparsers.add_parser("simulate-attack", help="Simulate an attack and test stealth rule")
    p_atk.add_argument("--attacker", type=int, default=1, help="Attacker team ID")
    p_atk.add_argument("--victim", type=int, default=2, help="Victim team ID")
    p_atk.add_argument("--target", default="Management", help="Target category (Management, Supply Chain, DC-0153, etc.)")
    p_atk.set_defaults(func=cmd_simulate_attack)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()

