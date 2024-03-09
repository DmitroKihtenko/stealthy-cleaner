FROM python:3.11-slim as base-builder
RUN pip install --user pipenv==2023.10.20
WORKDIR /pipenv
ENV PIPENV_VENV_IN_PROJECT=1
COPY Pipfile* ./

FROM base-builder as builder
RUN python -m pipenv sync

FROM base-builder as test-builder
RUN python -m pipenv sync --dev

FROM python:3.11-slim as base_application
ARG USER_ID=1000
ARG GROUP_ID=1000
ENV WORKDIR=/src
ENV PYTHONPATH=${WORKDIR}
WORKDIR ${WORKDIR}
RUN addgroup --gid $GROUP_ID app-user \
    && useradd -u $USER_ID -g $GROUP_ID -m app-user \
    && chown app-user:app-user ${WORKDIR}
USER app-user:app-user
COPY --chown=app-user:app-user src/app/ ./app/
COPY --chown=app-user:app-user src/config.yaml ./
COPY --chown=app-user:app-user src/logging.conf ./

FROM base_application as test_application
COPY --chown=app-user:app-user src/tests ./tests/
COPY --from=test-builder /pipenv/.venv /.venv
CMD ["/.venv/bin/python", "-m", "pytest"]

FROM base_application as application
COPY --from=builder /pipenv/.venv /.venv
CMD ["/.venv/bin/python", "-m", "main"]
