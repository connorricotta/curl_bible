FROM python:3.9.5

WORKDIR /usr/src/app

COPY requirements.txt ./
COPY .env ./
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# CMD ["gunicorn", "--bind", "0.0.0.0:10000", "wsgi:app"]
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "wsgi:app", "--log-level", "warning", "--error-logfile", "error.log" "--capture-output", "--log-config", "logging.conf"]