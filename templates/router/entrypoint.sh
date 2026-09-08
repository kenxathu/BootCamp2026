#!/bin/sh
set -e

echo "[+] Initializing pfSense Inter-VLAN Router..."

# Enable IP forwarding if container has NET_ADMIN capability
if sysctl -w net.ipv4.ip_forward=1 2>/dev/null; then
    echo "[+] IPv4 forwarding enabled"
else
    echo "[-] Note: Running without sysctl NET_ADMIN, software router mode active"
fi

# Try to setup basic NAT / iptables if permitted
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE 2>/dev/null || true

# Start pfSense Dashboard web application
exec python3 /app/app.py

