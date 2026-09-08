FROM python:3.11-slim

WORKDIR /app

COPY dns_server.py /app/dns_server.py

EXPOSE 53/tcp 53/udp 9153

CMD ["python3", "dns_server.py"]
