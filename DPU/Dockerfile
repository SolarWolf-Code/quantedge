FROM python:3.10.15-slim

# Install postgresql-client package
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD pg_isready -U ${DB_USER} -d ${DB_NAME} -h ${DB_HOST} -p ${DB_PORT} || exit 1

CMD ["python", "update_prices.py"]