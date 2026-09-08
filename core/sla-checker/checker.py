import asyncio
import socket
import time
import random
import os
import json
from typing import Dict, List, Any
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

app = FastAPI(title="Cyber Range Arena SLA Checker & Scoring Engine")

TOTAL_TEAMS = int(os.environ.get("TOTAL_TEAMS", "27"))
MIN_INTERVAL = int(os.environ.get("SLA_MIN_INTERVAL", "5")) # default fast for test, 60 in prod
MAX_INTERVAL = int(os.environ.get("SLA_MAX_INTERVAL", "20")) # default fast for test, 600 in prod
FAST_MODE = os.environ.get("FAST_MODE", "true").lower() == "true"

# Scoring Rules from Image 1
SCORING_RULES = {
    "service_recovery_points": {
        "server_k8s": 1000,
        "server": 500,
        "workstation": 100
    },
    "compromise_points": {
        "esxi_vcenter": 1000,
        "server": 500,
        "appliance": 300,
        "workstation": 100
    }
}

# SLA Target Definition from Image 1
SLA_TARGET_SPECS = [
    {
        "category": "Supply Chain",
        "alias": "jenkins",
        "ports": [8000, 8080],
        "type": "server",
        "penalty": 500
    },
    {
        "category": "DC-0153",
        "alias": "dc01",
        "ports": [88, 135, 389, 445, 636, 8081, 50000, 50050, 50100],
        "type": "server",
        "penalty": 500
    },
    {
        "category": "WS-01",
        "alias": "ws01",
        "ports": [4481, 5985, 3389],
        "type": "workstation",
        "penalty": 100
    },
    {
        "category": "WS-02",
        "alias": "ws02",
        "ports": [4482, 5986, 3390],
        "type": "workstation",
        "penalty": 100
    },
    {
        "category": "VPN",
        "alias": "vpn",
        "ports": [22, 443],
        "type": "appliance",
        "penalty": 300
    },
    {
        "category": "Management",
        "alias": "esxi",
        "ports": [2301, 2302, 2303, 2322],
        "type": "esxi_vcenter",
        "penalty": 1000
    }
]

# In-memory arena state
arena_state: Dict[str, Any] = {
    "round": 0,
    "last_check_timestamp": 0,
    "next_check_in_seconds": 0,
    "teams": {}
}

# Initialize team states
for tid in range(1, TOTAL_TEAMS + 1):
    tkey = f"team{tid:02d}"
    arena_state["teams"][tkey] = {
        "id": tid,
        "name": f"Team {tid:02d}",
        "score_total": 5000, # Initial starting defense budget
        "score_pwn": 0,
        "score_sla": 5000,
        "services": {},
        "pwned_targets": set(),
        "sla_penalties": []
    }
    for spec in SLA_TARGET_SPECS:
        arena_state["teams"][tkey]["services"][spec["category"]] = {
            "status": "UP",
            "uptime_ratio": 1.0,
            "failed_ports": [],
            "last_checked": 0
        }

async def check_port(host: str, port: int, timeout: float = 1.5) -> bool:
    """Non-blocking TCP socket connect check."""
    try:
        conn = asyncio.open_connection(host, port)
        reader, writer = await asyncio.wait_for(conn, timeout=timeout)
        writer.close()
        await writer.wait_closed()
        return True
    except Exception:
        return False

async def probe_team_service(team_id: int, spec: dict) -> dict:
    """Probes all required ports of a given service for a team."""
    alias = spec["alias"]
    ports = spec["ports"]
    tkey = f"team{team_id:02d}"
    
    # Try resolving hostname inside docker network or fallback to localhost mapping
    host_candidates = [
        f"{tkey}-{alias}",
        f"{alias}.team{team_id:02d}.arena.local",
        "127.0.0.1"
    ]
    
    target_host = host_candidates[0]
    
    failed_ports = []
    for port in ports:
        alive = await check_port(target_host, port)
        if not alive:
            # Check secondary fallback
            alive = await check_port("127.0.0.1", port)
        if not alive:
            failed_ports.append(port)

    # In mock simulation if no container is up yet, keep healthy unless forced down
    is_up = len(failed_ports) == 0
    return {
        "category": spec["category"],
        "is_up": is_up,
        "failed_ports": failed_ports,
        "penalty": spec["penalty"] if not is_up else 0
    }

async def run_sla_probe_round():
    """Executes a randomized SLA probe round across all teams."""
    arena_state["round"] += 1
    round_id = arena_state["round"]
    timestamp = time.time()
    arena_state["last_check_timestamp"] = timestamp

    print(f"\n[SLA CHECKER] >>> Starting Random SLA Check Round #{round_id} at {time.strftime('%X')}")

    for tid in range(1, TOTAL_TEAMS + 1):
        tkey = f"team{tid:02d}"
        t_data = arena_state["teams"][tkey]

        for spec in SLA_TARGET_SPECS:
            cat = spec["category"]
            res = await probe_team_service(tid, spec)
            
            svc_data = t_data["services"][cat]
            svc_data["last_checked"] = timestamp

            if not res["is_up"]:
                svc_data["status"] = "DOWN"
                svc_data["failed_ports"] = res["failed_ports"]
                
                # Deduct penalty
                penalty = spec["penalty"]
                t_data["score_sla"] = max(0, t_data["score_sla"] - penalty)
                t_data["score_total"] = t_data["score_sla"] + t_data["score_pwn"]
                t_data["sla_penalties"].append({
                    "round": round_id,
                    "service": cat,
                    "penalty": penalty,
                    "failed_ports": res["failed_ports"],
                    "timestamp": timestamp
                })
                print(f"[-] [{tkey}] Service {cat} DOWN! Ports {res['failed_ports']} unreachable. -{penalty} pts.")
            else:
                svc_data["status"] = "UP"
                svc_data["failed_ports"] = []
                # Check stealth rule:
                # "Khi chiếm được server/máy trạm của đối phương mà không vô hiệu hoá dịch vụ thì đội quản trị server không bị trừ điểm"
                if cat in t_data["pwned_targets"]:
                    # Target was compromised, but service is UP -> No penalty!
                    pass

    # Schedule next random interval (1 to 10 minutes, or 5-20s in fast mode)
    next_interval = random.randint(MIN_INTERVAL, MAX_INTERVAL)
    arena_state["next_check_in_seconds"] = next_interval
    print(f"[SLA CHECKER] <<< Round #{round_id} complete. Next check in {next_interval} seconds.\n")

async def sla_loop():
    """Background loop with random interval 1-10 minutes."""
    while True:
        await run_sla_probe_round()
        wait_seconds = arena_state.get("next_check_in_seconds", 30)
        await asyncio.sleep(wait_seconds)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(sla_loop())

@app.get("/api/state")
async def get_state():
    # Convert sets to lists for JSON serialization
    serialized = json.loads(json.dumps(arena_state, default=lambda o: list(o) if isinstance(o, set) else str(o)))
    return JSONResponse(content=serialized)

@app.post("/api/pwn")
async def register_pwn(attacker_id: int, victim_id: int, target_category: str):
    """Registers a successful compromise of a target category."""
    attacker_key = f"team{attacker_id:02d}"
    victim_key = f"team{victim_id:02d}"

    if attacker_key not in arena_state["teams"] or victim_key not in arena_state["teams"]:
        return JSONResponse(status_code=400, content={"error": "Invalid team ID"})

    # Determine points from specification
    pts_map = {
        "Management": 1000, # ESXi/vCenter
        "Supply Chain": 500, # Server
        "DC-0153": 500,      # Server
        "VPN": 300,          # Appliance / Thiết bị
        "WS-01": 100,        # Workstation
        "WS-02": 100         # Workstation
    }
    pts = pts_map.get(target_category, 100)

    # Award points to attacker
    attacker = arena_state["teams"][attacker_key]
    attacker["score_pwn"] += pts
    attacker["score_total"] = attacker["score_sla"] + attacker["score_pwn"]

    # Mark victim target as pwned
    victim = arena_state["teams"][victim_key]
    victim["pwned_targets"].add(target_category)

    # Check stealth rule condition:
    # "Khi chiếm được server/máy trạm của đối phương mà không vô hiệu hoá dịch vụ thì đội quản trị server không bị trừ điểm."
    is_svc_up = victim["services"].get(target_category, {}).get("status", "UP") == "UP"

    msg = f"Team {attacker_id} PWNED {target_category} of Team {victim_id}! (+{pts} pts)."
    if is_svc_up:
        msg += " (Stealth Rule Active: Service is still UP, Team " + str(victim_id) + " is NOT penalized on SLA!)"

    return {
        "status": "success",
        "points_awarded": pts,
        "stealth_rule_applied": is_svc_up,
        "message": msg
    }

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    state_json = json.dumps(arena_state, default=lambda o: list(o) if isinstance(o, set) else str(o))
    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Cyber Range Arena - SLA Checker & Live Scoreboard</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0b0f19; color: #e2e8f0; margin: 0; padding: 20px; }}
        .topbar {{ background: #1a2234; padding: 18px 24px; border-radius: 10px; display: flex; justify-content: space-between; align-items: center; border-left: 6px solid #38bdf8; }}
        .title {{ font-size: 22px; font-weight: bold; color: #38bdf8; }}
        .meta {{ font-size: 14px; color: #94a3b8; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr)); gap: 20px; margin-top: 24px; }}
        .card {{ background: #161e2e; border: 1px solid #27354f; border-radius: 10px; padding: 18px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }}
        .card-header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #27354f; padding-bottom: 10px; margin-bottom: 12px; }}
        .score {{ font-size: 18px; font-weight: bold; color: #f59e0b; }}
        .badge-up {{ background: #065f46; color: #34d399; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }}
        .badge-down {{ background: #7f1d1d; color: #f87171; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
        th, td {{ padding: 6px 8px; text-align: left; border-bottom: 1px solid #1e293b; }}
        th {{ color: #64748b; }}
        .rules-card {{ background: #1e1b4b; border: 1px solid #4338ca; border-radius: 10px; padding: 16px; margin-top: 20px; }}
    </style>
    <script>
        setInterval(() => window.location.reload(), 8000);
    </script>
</head>
<body>
    <div class="topbar">
        <div>
            <div class="title">🏆 ARENA CYBER RANGE - SLA & SCORING ENGINE</div>
            <div class="meta">Hạ tầng BTC (10.10.0.0/24) | SLA Random Interval: 1-10 phút | Trạng thái: <strong>ACTIVE</strong></div>
        </div>
        <div>
            <span style="background:#0369a1;padding:8px 14px;border-radius:6px;font-weight:bold;">Round: {arena_state['round']}</span>
        </div>
    </div>

    <div class="rules-card">
        <h4 style="margin:0 0 8px 0;color:#a5b4fc;">📜 QUY CHẾ ĐẤU TRƯỜNG:</h4>
        <span style="color:#cbd5e1;font-size:13px;">
            • <strong>Điểm chiếm đối phương:</strong> ESXi/vCenter: 1000 | Server: 500 | Thiết bị: 300 | Máy trạm: 100<br>
            • <strong>Điểm khôi phục:</strong> Server K8s: 1000 | Server: 500 | Máy trạm: 100<br>
            • <strong>Quy tắc tàng hình (Stealth Rule):</strong> Khi chiếm được server/máy trạm của đối phương mà <strong>không vô hiệu hoá dịch vụ</strong> thì đội quản trị server không bị trừ điểm.
        </span>
    </div>

    <h2 style="margin-top:24px;color:#f8fafc;">Bảng Giám Sát Dịch Vụ 27 Đội (Team01 - Team27)</h2>
    <div class="grid" id="teams-grid">
        <!-- Render teams -->
    </div>

    <script>
        const state = {state_json};
        const container = document.getElementById("teams-grid");
        Object.keys(state.teams).forEach(tkey => {{
            const t = state.teams[tkey];
            let rows = "";
            Object.keys(t.services).forEach(sname => {{
                const s = t.services[sname];
                const badge = s.status === "UP" ? '<span class="badge-up">UP</span>' : '<span class="badge-down">DOWN</span>';
                rows += `<tr><td><strong>${{sname}}</strong></td><td>${{badge}}</td><td>${{s.failed_ports.length > 0 ? s.failed_ports.join(', ') : 'None'}}</td></tr>`;
            }});

            const card = document.createElement("div");
            card.className = "card";
            card.innerHTML = `
                <div class="card-header">
                    <span style="font-size:16px;font-weight:bold;">${{t.name}}</span>
                    <span class="score">${{t.score_total}} pts</span>
                </div>
                <div style="font-size:12px;color:#94a3b8;margin-bottom:8px;">
                    SLA Defense: ${{t.score_sla}} | Pwn Attack: ${{t.score_pwn}}
                </div>
                <table>
                    <thead><tr><th>Dịch vụ</th><th>Trạng thái</th><th>Cổng lỗi</th></tr></thead>
                    <tbody>${{rows}}</tbody>
                </table>
            `;
            container.appendChild(card);
        }});
    </script>
</body>
</html>"""

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)

