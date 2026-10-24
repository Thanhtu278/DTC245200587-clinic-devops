FROM python:3.12-slim

WORKDIR /app

RUN groupadd -g 10002 sinkgroup && \
    useradd -u 10002 -g sinkgroup -m appuser && \
    mkdir -p /var/log && \
    touch /var/log/alerts.log && \
    chown -R appuser:sinkgroup /var/log/alerts.log /app

COPY app.py .

USER appuser

EXPOSE 5001

CMD ["python", "-u", "app.py"]
