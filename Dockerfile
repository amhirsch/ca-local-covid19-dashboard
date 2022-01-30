FROM python:3.10

WORKDIR /usr/src/app

RUN pip install pipenv
COPY Pipfile Pipfile.lock ./
RUN pipenv install --system --deploy

COPY app.py footnotes.md ./
COPY data/*.pickle data/

RUN useradd -m myuser
USER myuser

CMD gunicorn --bind 0.0.0.0:$PORT app:server
