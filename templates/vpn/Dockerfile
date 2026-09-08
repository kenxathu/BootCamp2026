FROM python:3.11-slim

WORKDIR /app

COPY server.py /app/server.py

# Monitored VPN Ports: 22, 443
EXPOSE 22 443

CMD ["python3", "server.py"]
