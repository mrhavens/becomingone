FROM python:3.10-slim

WORKDIR /app
COPY pyproject.toml .
RUN pip install pyzmq
COPY becomingone/ becomingone/

ENV PYTHONPATH=/app
