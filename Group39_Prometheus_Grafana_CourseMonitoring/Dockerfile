FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000 \
    DATABASE_PATH=/data/registrations.sqlite3 \
    SESSION_TTL_SECONDS=900
WORKDIR /workspace
RUN useradd --uid 10001 --create-home appuser && mkdir -p /data && chown appuser:appuser /data
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
USER appuser
EXPOSE 5000
# Single process: metrics and demo sessions live in that process.
CMD ["waitress-serve", "--host=0.0.0.0", "--port=5000", "--threads=8", "app.main:app"]
