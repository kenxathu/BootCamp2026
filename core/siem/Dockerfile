FROM python:3.11-slim

WORKDIR /app

COPY collector.py /app/collector.py

EXPOSE 514/udp 514/tcp 5601 80

CMD ["python3", "collector.py"]

