FROM python:3.11-slim

WORKDIR /app

COPY server.py /app/server.py

# DC-0153 Ports specified in Image 1:
# 88 (Kerberos), 135 (RPC), 389 (LDAP), 445 (SMB), 636 (LDAPS), 8081 (Admin Web), 50000, 50050, 50100
EXPOSE 88 135 389 445 636 8081 50000 50050 50100

CMD ["python3", "server.py"]
