FROM python:3.10

WORKDIR /code

COPY Pipfile Pipfile.lock container-start.sh /code/

RUN pip install pipenv
RUN pipenv install --system --deploy

COPY curl_bible/ .

# Run as non-root
ARG UID=10000
ARG GID=10000

RUN groupadd -g "${GID}" solomon \
    && useradd --create-home --no-log-init -u "${UID}" -g "${GID}" solomon

RUN chown -R solomon:solomon /code

USER solomon

CMD ["bash", "container-start.sh"]