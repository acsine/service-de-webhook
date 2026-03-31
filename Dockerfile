# Use the official Python base image
FROM python:3.12-slim AS builder

ENV PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PYTHONDONTWRITEBYTECODE=1 \
  # pip:
  PIP_NO_CACHE_DIR=1 \
  PIP_DISABLE_PIP_VERSION_CHECK=1 \
  PIP_DEFAULT_TIMEOUT=100 \
  PIP_ROOT_USER_ACTION=ignore \
  # tini:
  TINI_VERSION=v0.19.0 \
  # poetry:
  POETRY_VERSION=1.8.2 \
  POETRY_NO_INTERACTION=1 \
  POETRY_VIRTUALENVS_CREATE=false \
  POETRY_CACHE_DIR='/var/cache/pypoetry' \
  POETRY_HOME='/usr/local'

SHELL ["/bin/bash", "-eo", "pipefail", "-c"]

RUN apt-get update && apt-get upgrade -y \
  && apt-get install --no-install-recommends -y \
    bash \
    brotli \
    build-essential \
    curl \
    gettext \
    git \
    libpq-dev \
    wait-for-it \
  && dpkgArch="$(dpkg --print-architecture | awk -F- '{ print $NF }')" \
  && curl -o /usr/local/bin/tini -sSLO "https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini-${dpkgArch}" \
  && chmod +x /usr/local/bin/tini && tini --version \
  # Installing `poetry` package manager:
  # https://github.com/python-poetry/poetry
  && curl -sSL 'https://install.python-poetry.org' | python - \
  && poetry --version \
  # Cleaning cache:
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

COPY ./poetry.lock ./pyproject.toml /app/

RUN --mount=type=cache,target="$POETRY_CACHE_DIR" \
  poetry version \
  && poetry lock --no-update \
  && poetry run pip install -U pip \
  && poetry install --no-interaction --no-ansi

COPY . .


# FROM python:3.10-slim AS runner


# Copy the application code to the working directory

# WORKDIR /app

RUN poetry env info

# COPY --from=builder /app /app
# Expose the port on which the application will run
EXPOSE 8000

# Run the FastAPI application using uvicorn server
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
ENTRYPOINT [ "/app/entrypoint.sh" ]