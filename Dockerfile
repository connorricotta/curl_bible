FROM python:3.10

WORKDIR /code

COPY Pipfile Pipfile.lock /code/

RUN pip install pipenv
RUN pipenv install --system --deploy

COPY curl_bible/ ./curl_bible
COPY .env .

# Run as non-root
ARG UID=10000
ARG GID=10000

RUN groupadd -g "${GID}" solomon \
    && useradd --create-home --no-log-init -u "${UID}" -g "${GID}" solomon

RUN chown solomon:solomon /code

USER solomon

CMD ["bash", "curl_bible/docker-start.sh"]

# CMD ["uvicorn", "app.fastapi_bible:app", "--host", "0.0.0.0", "--port", "10000"]