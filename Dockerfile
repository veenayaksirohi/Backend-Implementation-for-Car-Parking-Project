FROM python:3.9-slim
WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

# Use Gunicorn with gevent worker for production WSGI serving with access logs to stdout
CMD ["gunicorn", "-w", "4", "-k", "gevent", "-b", "0.0.0.0:5000", "--access-logfile", "-", "run:app"]
