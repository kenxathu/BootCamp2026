FROM python:3.11-slim

WORKDIR /app

COPY app.py /app/app.py
COPY ../scoring_rules.json /app/scoring_rules.json

EXPOSE 80 443 8000

CMD ["python3", "app.py"]

