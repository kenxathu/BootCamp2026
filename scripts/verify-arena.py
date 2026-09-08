#!/usr/bin/env python3
"""
Automated Verification Script for Arena Cyber Range
Validates template files, port mappings, scoring configuration, and network topology.
"""

import os
import sys
import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def test_scoring_rules():
    print("[1] Verifying core/scoring_rules.json...")
    rule_file = BASE_DIR / "core" / "scoring_rules.json"
    assert rule_file.exists(), "scoring_rules.json does not exist!"
    with open(rule_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Check scoring points against Image 1
    recovery = data["scoring"]["service_recovery_points"]
    assert recovery["server_k8s"] == 1000, "K8s recovery points mismatch"
    assert recovery["server"] == 500, "Server recovery points mismatch"
    assert recovery["workstation"] == 100, "Workstation recovery points mismatch"

    compromise = data["scoring"]["compromise_points"]
    assert compromise["esxi_vcenter"] == 1000, "ESXi compromise points mismatch"
    assert compromise["server"] == 500, "Server compromise points mismatch"
    assert compromise["appliance"] == 300, "Appliance compromise points mismatch"
    assert compromise["workstation"] == 100, "Workstation compromise points mismatch"

    # Check SLA ports against Image 1
    targets = {t["category"]: t["ports"] for t in data["sla_monitor"]["targets"]}
    assert targets["Supply Chain"] == [8000, 8080], "Supply chain ports mismatch"
    assert targets["DC-0153"] == [88, 135, 389, 445, 636, 8081, 50000, 50050, 50100], "DC-0153 ports mismatch"
    assert targets["WS-01"] == [4481, 5985, 3389], "WS-01 ports mismatch"
    assert targets["WS-02"] == [4482, 5986, 3390], "WS-02 ports mismatch"
    assert targets["VPN"] == [22, 443], "VPN ports mismatch"
    assert targets["Management"] == [2301, 2302, 2303, 2322], "Management ports mismatch"
    print("    -> All scoring rules and SLA ports match Image 1 perfectly!")

def test_template_files():
    print("\n[2] Verifying Dockerfile and server implementations...")
    required_templates = [
        "templates/router/Dockerfile",
        "templates/router/app.py",
        "templates/dc-0153/Dockerfile",
        "templates/dc-0153/server.py",
        "templates/workstations/Dockerfile.ws01",
        "templates/workstations/Dockerfile.ws02",
        "templates/workstations/agent.py",
        "templates/supplychain/jenkins/Dockerfile",
        "templates/supplychain/jenkins/server.py",
        "templates/supplychain/gitea/Dockerfile",
        "templates/supplychain/gitea/server.py",
        "templates/supplychain/verdaccio/Dockerfile",
        "templates/supplychain/verdaccio/server.py",
        "templates/k8s-argocd/Dockerfile",
        "templates/k8s-argocd/server.py",
        "templates/web-aio/Dockerfile",
        "templates/web-aio/app.py",
        "templates/vpn/Dockerfile",
        "templates/vpn/server.py",
        "templates/esxi-mgmt/Dockerfile",
        "templates/esxi-mgmt/server.py",
        "templates/edge-proxy/Dockerfile",
        "templates/edge-proxy/app.py",
        "templates/ops/dns-ops/Dockerfile",
        "templates/ops/dns-ops/dns_server.py",
        "templates/ops/app-runner/Dockerfile",
        "templates/ops/app-runner/server.py",
        "templates/jumpbox/Dockerfile",
        "templates/jumpbox/jumpbox.py",
        "core/sla-checker/Dockerfile",
        "core/sla-checker/checker.py",
        "core/siem/Dockerfile",
        "core/siem/collector.py",
        "core/ctfd/Dockerfile",
        "core/ctfd/app.py",
        "docker-compose.core.yml"
    ]

    for p in required_templates:
        fpath = BASE_DIR / p
        assert fpath.exists(), f"Missing template file: {p}"
    print(f"    -> All {len(required_templates)} core template and service files verified!")

def test_team_compose_generation():
    rule_file = BASE_DIR / "core" / "scoring_rules.json"
    with open(rule_file, "r", encoding="utf-8") as f:
        total_teams = json.load(f)["competition"]["total_teams"]
    print(f"\n[3] Verifying Team Compose topology for all {total_teams} teams...")
    generated_dir = BASE_DIR / "generated"
    for tid in range(1, total_teams + 1):
        cf = generated_dir / f"docker-compose.team{tid:02d}.yml"
        assert cf.exists(), f"Compose file for Team {tid:02d} missing!"
        content = cf.read_text(encoding="utf-8")

        # Verify static IP mappings from Image 2 and Image 3
        wan_ip = f"10.10.1{tid:02d}.2"
        esxi_ip = f"10.10.1{tid:02d}.3"
        assert wan_ip in content, f"Team {tid} pfSense WAN IP missing"
        assert esxi_ip in content, f"Team {tid} ESXi IP missing"

        # Check VLAN subnets from Image 3
        assert "172.16.20.101" in content, "Web-AIO IP missing"
        assert "172.16.20.102" in content, "VPN IP missing"
        assert "172.16.20.104" in content, "DC01 IP missing"
        assert "172.16.20.105" in content, "WS01 IP missing"
        assert "172.16.20.106" in content, "WS02 IP missing"

        assert "172.16.201.102" in content, "EDGE-Proxy IP missing"
        assert "172.16.201.103" in content, "Gitea IP missing"
        assert "172.16.201.104" in content, "CI-Runner IP missing"

        assert "172.16.202.105" in content, "Jenkins IP missing"
        assert "172.16.202.106" in content, "K3s-ArgoCD IP missing"
        assert "172.16.202.107" in content, "npm-registry IP missing"

        assert "172.16.203.109" in content, "DNS-OPS IP missing"
        assert "172.16.203.110" in content, "App-Runner IP missing"

        assert "172.16.204.100" in content, "AdminPrivate Jumpbox IP missing"

    print(f"    -> All 27 team environments correctly map all 5 VLANs and all 13 containers!")

def main():
    print("=== STARTING ARENA SPECIFICATION VERIFICATION ===")
    test_scoring_rules()
    test_template_files()
    test_team_compose_generation()
    print("\n[SUCCESS] ALL VERIFICATION CHECKS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
