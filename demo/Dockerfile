FROM python:3.13-alpine

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ADD . /code
WORKDIR /code/demo
