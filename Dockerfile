FROM python:3.11-slim as builder
RUN pip install --user pipenv==2023.10.20
WORKDIR /pipenv
ENV PIPENV_VENV_IN_PROJECT=1
COPY Pipfile* ./
RUN python -m pipenv sync

FROM python:3.11-slim as application
ARG USER_ID=1000
ARG GROUP_ID=1000
ENV WORKDIR=/src
ENV PYTHONPATH=${WORKDIR}
WORKDIR ${WORKDIR}
RUN addgroup --gid $GROUP_ID app-user \
    && useradd -u $USER_ID -g $GROUP_ID -m app-user \
    && chown app-user:app-user ${WORKDIR}
USER app-user:app-user
COPY --chown=app-user:app-user src/ ./
COPY --from=builder /pipenv/.venv /.venv
CMD ["/.venv/bin/python", "app/main.py"]
