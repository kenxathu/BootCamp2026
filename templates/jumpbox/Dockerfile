FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    net-tools \
    iputils-ping \
    nmap \
    netcat-traditional \
    dnsutils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY jumpbox.py /app/jumpbox.py

EXPOSE 7681 8000

CMD ["python3", "jumpbox.py"]
