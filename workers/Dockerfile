FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN useradd --system --create-home app
COPY --chown=app:app main.py /app/main.py

USER app
ENTRYPOINT ["python", "/app/main.py"]
