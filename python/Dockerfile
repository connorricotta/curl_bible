FROM python:3.9.5

WORKDIR /usr/src/app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt
RUN chmod +x docker-start.sh

CMD ["./docker-start.sh"]