# Hướng Dẫn Vận Hành & Triển Khai (Deployment Guide)

## 1. Yêu Cầu Hệ Thống (Prerequisites)

* **Hệ điều hành:** Linux (Ubuntu 22.04 LTS khuyến nghị) hoặc Windows Server / Windows 11 với WSL2 / Docker Desktop.
* **Công cụ:**
  * Docker version $\ge$ 24.0.0
  * Docker Compose version $\ge$ 2.20.0
  * Python version $\ge$ 3.10

---

## 2. Các Bước Khởi Chạy Sàn Đấu (Step-by-Step)

### Bước 1: Cài Đặt Thư Viện Phụ Trợ
```bash
cd BootCamp2026
pip install -r requirements.txt
```

### Bước 2: Sinh Cờ (Flags) Bảo Mật Cho 27 Đội
```bash
python arena-ctl.py generate-flags
```
* Kết quả: Tạo file `generated/master_flags.json` chứa 270 flag bí mật được ký số HMAC riêng biệt cho 27 đội x 10 mục tiêu.

### Bước 3: Sinh File Cấu Hình Cho Toàn Bộ 27 Đội
```bash
# Sinh cấu hình cho toàn bộ 27 đội theo đúng sơ đồ mạng
python arena-ctl.py spawn-teams --count 27 --mode exact
```

### Bước 4: Khởi Động Hạ Tầng BTC (10.10.0.0/24)
```bash
python arena-ctl.py up-core
```
* Các dịch vụ BTC sẽ sẵn sàng tại:
  * **CTFd Scoreboard & Nộp Flag:** [http://localhost:8000](http://localhost:8000)
  * **Bảng Giám Sát SLA Thời Gian Thực:** [http://localhost:8081](http://localhost:8081)
  * **Hệ Thống SIEM & Thu Log Syslog:** [http://localhost:5601](http://localhost:5601)

### Bước 5: Khởi Động Môi Trường Của Đội Thi & Cài Đặt Mật Khẩu pfSense
* **Khởi động một đội với mật khẩu tự động:**
  ```bash
  # Tự động sinh mật khẩu bảo mật (ví dụ: pfSense@Team01#3ae5bb76) và hiển thị ra màn hình
  python arena-ctl.py up-team --id 1
  ```
* **Khởi động kèm mật khẩu quản trị pfSense tùy chỉnh:**
  ```bash
  python arena-ctl.py up-team --id 1 --password "MatKhauQuanTri@2026!"
  ```
* **Tra cứu thông tin tài khoản pfSense bất kỳ lúc nào:**
  ```bash
  # Xem toàn bộ danh sách 27 đội
  python arena-ctl.py credentials

  # Hoặc xem riêng một đội cụ thể
  python arena-ctl.py credentials --id 1
  ```
* **Đăng nhập pfSense WebGUI:**
  - Truy cập địa chỉ `http://10.10.1XX.2:80` (hoặc qua Jumpbox VLAN 204).
  - Tên người dùng: `admin`
  - Mật khẩu: Mật khẩu hiển thị khi chạy `up-team` hoặc lưu trong `generated/team_credentials.json`.
  - Hỗ trợ cả đăng nhập giao diện web (Session Cookie) và HTTP Basic Auth.

---

## 3. Kiểm Thử & Giám Sát

### 3.1. Kiểm tra tình trạng SLA trực tiếp qua Terminal:
```bash
python arena-ctl.py sla-status --limit 5
```

### 3.2. Mô phỏng kịch bản tấn công và kiểm tra Stealth Rule:
```bash
# Đội 1 chiếm ESXi của Đội 2 (+1000 điểm)
python arena-ctl.py simulate-attack --attacker 1 --victim 2 --target "Management"
```

### 3.3. Dừng và dọn dẹp hệ thống khi kết thúc giải đấu:
```bash
python arena-ctl.py down-all
```

