FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends git build-essential libssl-dev libffi-dev && rm -rf /var/lib/apt/lists/*
COPY leadgen/ ./leadgen/
COPY server/requirements.txt .
RUN pip install -q -U pip && pip install -q -e leadgen[.] -r requirements.txt
COPY server/ .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
