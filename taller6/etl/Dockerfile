# Imagen del ETL · contexto de construcción: carpeta taller6/
#   docker build -f etl/Dockerfile -t microrred-etl:1.0.0 .
# Base python:3.12-slim-bookworm: Debian recortado (~45 MB comprimida). Se prefiere a
# alpine porque pandas y psycopg traen ruedas (wheels) precompiladas para glibc; en alpine
# (musl) habría que compilarlas, la imagen crecería y la construcción tardaría minutos.
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app
COPY etl/requirements.txt .
RUN pip install -r requirements.txt

COPY etl/ ./etl/
COPY sql/ ./sql/

# Nunca correr como root dentro del contenedor
RUN useradd --uid 10001 --no-create-home etl
USER 10001

ENTRYPOINT ["python", "-m", "etl.run_etl"]
