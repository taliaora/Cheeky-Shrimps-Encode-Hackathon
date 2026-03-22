FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY shrimps/ ./shrimps/
COPY pyproject.toml .

# Non-root user for security
RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 8050

CMD gunicorn shrimps.app:server --bind 0.0.0.0:${PORT:-8050} --workers 2 --timeout 120
