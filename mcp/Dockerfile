FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir "mcp[cli]>=1.0.0" "httpx>=0.27.0"

COPY server.py server_types.py ./
COPY sources/ ./sources/

ENV PORT=8000
EXPOSE 8000

CMD ["python", "server.py", "sse"]
