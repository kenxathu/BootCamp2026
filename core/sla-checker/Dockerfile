FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY checker.py .
COPY ../scoring_rules.json ./scoring_rules.json

EXPOSE 8080

CMD ["python3", "checker.py"]

