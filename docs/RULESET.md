# Quy Chế Tính Điểm & Luật Đấu Trường An Toàn Thông Tin

## 1. Bảng Điểm Khôi Phục Dịch Vụ (Service Recovery Points)

| Hạng mục mục tiêu | Điểm cộng khôi phục | Ghi chú kỹ thuật |
| :--- | :--- | :--- |
| **Server K8s** | **+1000 điểm** | Cụm K3s + ArgoCD (`172.16.202.106`) |
| **Server** | **+500 điểm** | Web-AIO, DC-0153, Jenkins CI/CD |
| **Máy trạm** | **+100 điểm** | WS-01 (`.105`), WS-02 (`.106`) |

---

## 2. Bảng Điểm Chiếm Của Đối Phương (Compromise / Pwn Points)

| Hạng mục mục tiêu | Điểm cộng tấn công | Ghi chú kỹ thuật |
| :--- | :--- | :--- |
| **ESXi / vCenter** | **+1000 điểm** | Hypervisor host (`10.10.1XX.3`, cổng 2301..2322) |
| **Server** | **+500 điểm** | Web-AIO, DC-0153, Jenkins, K8s master |
| **Thiết bị (Appliance)** | **+300 điểm** | pfSense FW, VPN gateway, EDGE-Proxy |
| **Máy trạm (Workstation)**| **+100 điểm** | WS-01, WS-02 |

---

## 3. Quy Tắc Tàng Hình (Stealth Rule)

> [!IMPORTANT]
> **Quy định bảo toàn SLA:** Khi chiếm được server/máy trạm của đối phương mà **không vô hiệu hoá dịch vụ** thì đội quản trị server không bị trừ điểm.

* **Trường hợp 1 (Tấn công chuẩn xác / Tàng hình):**
  * Đội A khai thác lỗ hổng và lấy được flag trên `DC-0153` của Đội B.
  * Dịch vụ Active Directory (cổng 88, 135, 389, 445, 636, 8081...) vẫn hoạt động bình thường khi BTC kiểm tra ngẫu nhiên.
  * **Kết quả:** Đội A nhận `+500 điểm` tấn công. Đội B **không bị trừ điểm SLA**.
* **Trường hợp 2 (Phá hoại / Gián đoạn dịch vụ):**
  * Đội A chiếm máy chủ và tắt dịch vụ hoặc xóa cấu hình làm rơi cổng.
  * BTC kiểm tra ngẫu nhiên phát hiện dịch vụ bị gián đoạn.
  * **Kết quả:** Đội A nhận `+500 điểm` tấn công. Đội B **bị trừ 500 điểm SLA**.

---

## 4. Dịch Vụ Giám Sát SLA (SLA Monitored Services)

BTC kiểm tra tự động và **ngẫu nhiên trong khoảng thời gian từ 1 đến 10 phút**. Dịch vụ không phản hồi đúng cổng khi kiểm tra sẽ bị trừ điểm tương ứng.

| Dịch vụ giám sát | Cổng kiểm tra (Ports) | Nút thực thi | Vùng mạng |
| :--- | :--- | :--- | :--- |
| **Supply Chain** | `8000, 8080` | Jenkins | SCB_VLAN202 (`172.16.202.105`) |
| **DC-0153** | `88, 135, 389, 445, 636, 8081, 50000/50050/50100` | DC01 (AD) | KH VLAN 20 (`172.16.20.104`) |
| **WS-01** | `4481, 5985, 3389` | WS-01 | KH VLAN 20 (`172.16.20.105`) |
| **WS-02** | `4482, 5986, 3390` | WS-02 | KH VLAN 20 (`172.16.20.106`) |
| **VPN** | `22, 443` | VPN Gateway | KH VLAN 20 (`172.16.20.102`) |
| **Management** | `2301, 2302, 2303, 2322` | ESXi Host | WAN (`10.10.1XX.3`) |
