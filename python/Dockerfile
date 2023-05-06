FROM python:3.10

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./ /code/app

# Run as non-root
ARG UID=10000
ARG GID=10000

RUN groupadd -g "${GID}" solomon \
    && useradd --create-home --no-log-init -u "${UID}" -g "${GID}" solomon

RUN chown solomon:solomon /code

USER solomon

CMD ["uvicorn", "app.fastapi_bible:app", "--host", "0.0.0.0", "--port", "10000"]