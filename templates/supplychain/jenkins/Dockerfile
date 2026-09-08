FROM python:3.11-slim

WORKDIR /app

COPY server.py /app/server.py

# Monitored Supply Chain Ports: 8000, 8080
EXPOSE 8000 8080

CMD ["python3", "server.py"]

