FROM python:3.10.2-slim-bullseye@sha256:bb41290f37c7c96cfddff5bb3f2ad8bddbf499a94cdcc07916c7363e42612fbf as base

RUN groupadd --gid=10001 user \
    && useradd --gid=user --uid=10000 --create-home user
WORKDIR /home/user/app
RUN chown user:user /home/user/app

ENV PATH="/home/user/.local/bin:${PATH}"
ENV PYTHONUNBUFFERED=1


FROM base as build

RUN apt-get update \
    && apt-get install --no-install-recommends --assume-yes \
        curl

USER user

ENV POETRY_VERSION=1.1.13
ENV POETRY_VIRTUALENVS_CREATE=0
ENV POETRY_EXPERIMENTAL_NEW_INSTALLER=0

RUN curl --silent --show-error https://install.python-poetry.org | python -

COPY --chown=user:user poetry.lock .
COPY --chown=user:user pyproject.toml .

RUN poetry install --no-root --no-dev


FROM base as prod

USER user

ENV PYTHONOPTIMIZE=1

COPY --from=build --chown=user:user /home/user/.local /home/user/.local/
COPY --chown=user:user main.py .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]
