# Imagen del simulador de streaming · contexto: carpeta taller6/
#   docker build -f simulador/Dockerfile -t microrred-simulador:1.0.0 .
# Misma base slim que el ETL (capas compartidas en la caché del nodo), pero sin pandas:
# solo psycopg. Resultado ≈ 150 MB frente a ≈ 400 MB del ETL.
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app
COPY simulador/requirements.txt .
RUN pip install -r requirements.txt
COPY simulador/simulador.py .

RUN useradd --uid 10001 --no-create-home sim
USER 10001
ENTRYPOINT ["python", "simulador.py"]
