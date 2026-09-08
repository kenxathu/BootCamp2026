#!/usr/bin/env python3
"""
Unit test and simulation for SLA scoring, Pwn scoring, and Stealth rule logic.
"""

import sys
import json
from pathlib import Path

# Load scoring rules
BASE_DIR = Path(__file__).resolve().parent.parent
with open(BASE_DIR / "core" / "scoring_rules.json", "r", encoding="utf-8") as f:
    config = json.load(f)

def run_simulation():
    print("=== SIMULATING ARENA SCORING & STEALTH RULES ===")
    
    # State representation
    teams = {
        1: {"name": "Team 01", "sla_score": 5000, "pwn_score": 0, "recovery_score": 0, "services": {"DC-0153": "UP", "Management": "UP", "Supply Chain": "UP"}},
        2: {"name": "Team 02", "sla_score": 5000, "pwn_score": 0, "recovery_score": 0, "services": {"DC-0153": "UP", "Management": "UP", "Supply Chain": "UP"}}
    }

    # Step 1: Team 01 compromises ESXi/vCenter on Team 02
    print("\n[Step 1] Team 01 captures ESXi/vCenter on Team 02...")
    pwn_pts = config["scoring"]["compromise_points"]["esxi_vcenter"]
    assert pwn_pts == 1000
    teams[1]["pwn_score"] += pwn_pts
    print(f"    -> Team 01 awarded +{pwn_pts} Pwn points (Total Pwn: {teams[1]['pwn_score']})")

    # Step 2: Evaluate Stealth Rule
    # Rule: "Khi chiếm được server/máy trạm của đối phương mà không vô hiệu hoá dịch vụ thì đội quản trị server không bị trừ điểm"
    print("\n[Step 2] Evaluating Stealth Rule on Team 02...")
    esxi_status = teams[2]["services"]["Management"]
    if esxi_status == "UP":
        print("    -> ESXi Management services still ONLINE! Team 02 SLA score is PRESERVED (0 deduction).")
        assert teams[2]["sla_score"] == 5000
    else:
        teams[2]["sla_score"] -= 1000

    # Step 3: Team 02 suffers an outage on DC-0153 during random BTC check
    print("\n[Step 3] Random BTC SLA check (1-10 min) occurs: DC-0153 ports down on Team 02...")
    teams[2]["services"]["DC-0153"] = "DOWN"
    dc_penalty = config["scoring"]["compromise_points"]["server"] # 500
    assert dc_penalty == 500
    teams[2]["sla_score"] -= dc_penalty
    print(f"    -> Team 02 penalized -{dc_penalty} SLA points (New SLA: {teams[2]['sla_score']})")
    assert teams[2]["sla_score"] == 4500

    # Step 4: Team 02 recovers K8s service
    print("\n[Step 4] Team 02 restores Server K8s service...")
    rec_pts = config["scoring"]["service_recovery_points"]["server_k8s"]
    assert rec_pts == 1000
    teams[2]["recovery_score"] += rec_pts
    print(f"    -> Team 02 awarded +{rec_pts} Service Recovery points!")

    # Summary
    print("\n=== FINAL SIMULATION STANDINGS ===")
    for tid, t in teams.items():
        total = t["sla_score"] + t["pwn_score"] + t["recovery_score"]
        print(f"[{t['name']}] Total: {total} | SLA: {t['sla_score']} | Pwn: {t['pwn_score']} | Recovery: {t['recovery_score']}")

    print("\n[SUCCESS] Scoring and Stealth Rule simulation completed successfully!")

if __name__ == "__main__":
    run_simulation()
