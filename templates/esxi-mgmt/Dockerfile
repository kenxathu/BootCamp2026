FROM python:3.11-slim

WORKDIR /app

COPY server.py /app/server.py

# Monitored Management Ports: 2301, 2302, 2303, 2322 + Web UI 80/443
EXPOSE 2301 2302 2303 2322 80 443

CMD ["python3", "server.py"]

