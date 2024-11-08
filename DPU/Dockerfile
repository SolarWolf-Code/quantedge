FROM python:3.10.15-slim

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD ps aux | grep python | grep update_prices.py || exit 1

CMD ["python", "update_prices.py"]