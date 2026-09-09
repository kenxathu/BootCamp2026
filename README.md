# Arena Cyber Range 2026 - Đấu Trường An Toàn Thông Tin

Hệ thống sàn đấu an toàn thông tin chuyên nghiệp (Cyber Range / Attack-Defense / King of the Hill) được thiết kế và lập trình hoàn chỉnh dựa trên 3 sơ đồ kỹ thuật và quy chế chấm điểm thực tế.

---

## 🌟 Tính Năng Nổi Bật

1. **Chuẩn Hóa Mạng 27 Đội Thi (`Team01` – `Team27`)**:
   - Vùng WAN `10.10.101.0/24` đến `10.10.127.0/24`.
   - Mỗi đội sở hữu **5 VLAN** kết nối qua pfSense 802.1Q router:
     - **VLAN 20 (KH)**: `Web-AIO` (.101), `VPN` (.102), `DC01` (.104), `WS01` (.105), `WS02` (.106).
     - **VLAN 201 (SCB_VLAN201)**: `EDGE-Proxy` (.102), `Gitea` (.103), `CI-Runner` (.104).
     - **VLAN 202 (SCB_VLAN202)**: `Jenkins` (.105), `K3s-ArgoCD` (.106), `npm-registry` (.107).
     - **VLAN 203 (SCB_VLAN203)**: `DNS-OPS` (.109), `App-Runner` (.110).
     - **VLAN 204 (AdminPrivate)**: Dải DHCP `.100 - .200` cho laptop thành viên đội.
   - Nút quản trị máy chủ ảo hóa **ESXi Host** (`10.10.1XX.3`, cổng 2301, 2302, 2303, 2322).

2. **Hạ Tầng BTC Hoàn Chỉnh (`10.10.0.0/24`)**:
   - **CTFd (10.10.0.10:8000)**: Nộp flag, tính điểm tấn công và khôi phục dịch vụ, bảng xếp hạng thời gian thực.
   - **SLA Checker Engine (10.10.0.15:8080)**: Kiểm tra ngẫu nhiên chu kỳ **1–10 phút** các cổng dịch vụ trọng yếu.
   - **SIEM (10.10.0.8:5601)**: Thu thập toàn bộ Syslog (cổng 514 UDP) từ sàn đấu.

3. **Thực Thi Quy Chế & Luật Tàng Hình (Stealth Rule)**:
   - **Điểm khôi phục:** Server K8s: 1000 | Server: 500 | Máy trạm: 100.
   - **Điểm chiếm mục tiêu:** ESXi/vCenter: 1000 | Server: 500 | Thiết bị: 300 | Máy trạm: 100.
   - **Luật bảo toàn dịch vụ:** *\"Khi chiếm được server/máy trạm của đối phương mà không vô hiệu hoá dịch vụ thì đội quản trị server không bị trừ điểm.\"*

---

## 🚀 Khởi Động Nhanh (Quick Start)

```bash
# 1. Sinh cờ bí mật cho 27 đội
python arena-ctl.py generate-flags

# 2. Sinh cấu hình Docker Compose cho 27 đội
python arena-ctl.py spawn-teams --count 27

# 3. Khởi chạy hạ tầng BTC (CTFd, SIEM, SLA Engine)
python arena-ctl.py up-core

# 4. Khởi chạy đội thi (ví dụ Đội 01 với mật khẩu quản trị pfSense)
python arena-ctl.py up-team --id 1
# Hoặc truyền mật khẩu tùy chọn:
# python arena-ctl.py up-team --id 1 --password "SecretPass123!"

# 5. Tra cứu danh sách mật khẩu quản trị pfSense các đội:
python arena-ctl.py credentials --id 1
```

* **pfSense WebGUI:** `http://10.10.1XX.2:80` (User: `admin`, Password tự sinh hoặc cấu hình)
* **CTFd Scoreboard:** [http://localhost:8000](http://localhost:8000)
* **SLA Live Dashboard:** [http://localhost:8081](http://localhost:8081)
* **SIEM Syslog Console:** [http://localhost:5601](http://localhost:5601)

---

## 📁 Cấu Trúc Thư Mục

```text
BootCamp2026/
├── arena-ctl.py               # Trình điều khiển Arena CLI
├── docker-compose.core.yml    # Hạ tầng BTC: CTFd, SIEM, SLA Checker
├── core/
│   ├── ctfd/                  # CTFd web & scoring engine
│   ├── sla-checker/           # SLA Checker daemon (ngẫu nhiên 1-10 phút)
│   ├── siem/                  # Syslog collector (514 UDP) & Dashboard (5601)
│   └── scoring_rules.json     # Đặc tả điểm số & danh sách cổng giám sát
├── templates/                 # Mẫu đóng gói container cho các đội thi
│   ├── router/                # pfSense Inter-VLAN router (10.10.1XX.2)
│   ├── esxi-mgmt/             # ESXi management node (10.10.1XX.3: 2301..2322)
│   ├── dc-0153/               # Domain Controller DC01 (cổng 88,135,389,445,636,8081,50000...)
│   ├── workstations/          # WS01 & WS02 (cổng 4481/4482, 5985/5986, 3389/3390)
│   ├── supplychain/           # Jenkins (8000/8080), Gitea, npm-registry
│   ├── k8s-argocd/            # K3s (6443) & ArgoCD (8080)
│   ├── web-aio/               # Customer Web Portal (80/443)
│   ├── vpn/                   # VPN Gateway (22/443)
│   ├── edge-proxy/            # EDGE-Proxy (80/443/8443)
│   ├── ops/                   # DNS-OPS (53/9153) & App-Runner (5000)
│   ├── jumpbox/               # Laptop thí sinh (AdminPrivate VLAN 204)
│   └── team-compose.template.yml # Jinja2 template sinh 13 container x 5 VLAN
├── generated/                 # Thư mục chứa cấu hình sinh ra cho 27 đội
├── scripts/
│   ├── verify-arena.py        # Kiểm thử toàn diện cấu hình & cổng mạng
│   └── test-scoring-simulation.py # Kiểm thử luật tính điểm & stealth rule
└── docs/
    ├── ARCHITECTURE.md        # Tài liệu kiến trúc mạng chi tiết
    ├── RULESET.md             # Quy chế giải đấu & điểm số
    └── DEPLOYMENT_GUIDE.md    # Hướng dẫn vận hành chi tiết
```

