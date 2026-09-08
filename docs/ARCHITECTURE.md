# Kiến Trúc Đấu Trường An Toàn Thông Tin (Arena Cyber Range 2026)

## 1. Tổng Quan Kiến Trúc Mạng (Network Topology)

Sàn đấu an toàn thông tin được thiết kế theo mô hình phân tầng mô phỏng hệ thống ngân hàng / doanh nghiệp đa chi nhánh:

```text
                               +--------------------------------------------+
                               |         HẠ TẦNG BTC (10.10.0.0/24)         |
                               |  Core GW: 10.10.0.1 | DNS: 10.10.0.2       |
                               |  SIEM: 10.10.0.8    | CTFd: 10.10.0.10     |
                               |  SLA Engine: 10.10.0.15                    |
                               +--------------------------------------------+
                                                     |
                                                     v
                               +--------------------------------------------+
                               |             ARENA DISTRIBUTION             |
                               |   Routing: 10.10.101.0/24 - 10.10.127.0/24 |
                               +--------------------------------------------+
                                        /            |             \
                     +-----------------+      +-------------+      +-----------------+
                     | Team 01 Zone    |      | Team 02 ... |      | Team 27 Zone    |
                     | 10.10.101.0/24  |      |             |      | 10.10.127.0/24  |
                     +-----------------+      +-------------+      +-----------------+
```

---

## 2. Phân Bổ Địa Chỉ IP & Phân Vùng Mạng Chi Tiết

### 2.1. Vùng Hạ Tầng BTC (`10.10.0.0/24`)
* **ARENA CORE L3 Router**: `10.10.0.1`
* **ARENA CORE DNS**: `10.10.0.2`
* **SIEM Log Aggregator**: `10.10.0.8` (Cổng 514 Syslog UDP, Cổng 5601 Web UI)
* **CTFd Scoreboard & Flag Portal**: `10.10.0.10` (Cổng 8000 Web UI)
* **SLA Service Checker Engine**: `10.10.0.15` (Cổng 8080 API & Dashboard)

### 2.2. Vùng WAN & Quản Trị Của Từng Đội (`10.10.1XX.0/24` với XX = 01 .. 27)
* **WAN Gateway**: `10.10.1XX.1`
* **pfSense Inter-VLAN Router**: `10.10.1XX.2` (Trunk 802.1Q xuống các VLAN nội bộ)
* **ESXi Host / vCenter**: `10.10.1XX.3` (Các cổng quản trị: 2301, 2302, 2303, 2322)

---

## 3. Kiến Trúc Mạng Nội Bộ Sau pfSense (Mẫu Chung 27 Đội)

Mỗi đội sở hữu 5 VLAN độc lập được định tuyến liên VLAN qua pfSense:

```mermaid
graph TD
    PFSENSE["pfSense Router (10.10.1XX.2)"]
    
    subgraph VLAN20 ["VLAN 20: KH (Khách Hàng - 172.16.20.1/24)"]
        WEB_AIO["Web-AIO (172.16.20.101)"]
        VPN["VPN Gateway (172.16.20.102)"]
        DC01["DC-0153 (172.16.20.104)"]
        WS01["WS-01 (172.16.20.105)"]
        WS02["WS-02 (172.16.20.106)"]
    end

    subgraph VLAN201 ["VLAN 201: SCB_VLAN201 (Biên & Source Control - 172.16.201.1/24)"]
        EDGE["EDGE-Proxy (172.16.201.102)"]
        GITEA["Gitea (172.16.201.103)"]
        CIRUN["CI-Runner (172.16.201.104)"]
    end

    subgraph VLAN202 ["VLAN 202: SCB_VLAN202 (Chuỗi CI/CD & K8s - 172.16.202.1/24)"]
        JENKINS["Jenkins (172.16.202.105)"]
        K3S["K3s-ArgoCD (172.16.202.106)"]
        NPM["npm-registry (172.16.202.107)"]
    end

    subgraph VLAN203 ["VLAN 203: SCB_VLAN203 (Vận Hành & DNS - 172.16.203.1/24)"]
        DNS_OPS["DNS-OPS (172.16.203.109)"]
        APPRUN["App-Runner (172.16.203.110)"]
    end

    subgraph VLAN204 ["VLAN 204: AdminPrivate (Laptop Đội - 172.16.204.1/24)"]
        JUMPBOX["Laptop Đội / DHCP Pool (172.16.204.100 - .200)"]
    end

    PFSENSE --> VLAN20
    PFSENSE --> VLAN201
    PFSENSE --> VLAN202
    PFSENSE --> VLAN203
    PFSENSE --> VLAN204
```

---

## 4. Luồng Dữ Liệu (Traffic Flows)

1. **Luồng Tấn Công (Attack Flow)**:
   $$\text{Team X (AdminPrivate)} \rightarrow \text{pfSense X (out)} \rightarrow \text{Arena Core 10.10.0.0/24} \rightarrow \text{Distribution} \rightarrow \text{pfSense Y} \rightarrow \text{Dịch vụ trong VLAN đối phương}$$
2. **Luồng Quản Trị & Chấm Điểm (Admin & Scoring Flow)**:
   * Nộp Flag: Thí sinh gửi request về `CTFd 10.10.0.10:8000`.
   * SLA Monitoring: `SLA Engine 10.10.0.15` chủ động bắn các gói kiểm tra TCP/HTTP định kỳ ngẫu nhiên (1–10 phút) vào các cổng dịch vụ của 27 đội.
   * Thu thập Log: Toàn bộ pfSense và node gửi Syslog về `SIEM 10.10.0.8:514`.

