FROM python:3.14-slim
RUN apt-get update && apt-get install -y --no-install-recommends git build-essential libssl-dev libffi-dev curl && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY leadgen/ ./
RUN pip install -q -U pip setuptools wheel && pip install -q -r requirements.txt && pip install -q flask
COPY docker/mcp_api.py /app/mcp_api.py
CMD ["python","mcp_api.py"]
