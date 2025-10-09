# A imagem 'slim' é maior, mas já inclui as ferramentas de build necessárias
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

RUN pip install uv

COPY pyproject.toml uv.lock ./
RUN uv pip sync pyproject.toml --no-cache --system

COPY alembic.ini ./
COPY migrations/ ./migrations/
COPY src/ ./src/
COPY entrypoint.sh ./

RUN chmod +x entrypoint.sh

CMD ["./entrypoint.sh"]