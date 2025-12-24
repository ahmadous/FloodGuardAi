FROM python:3.11-slim

ENV PIP_DEFAULT_TIMEOUT=600 \
    PIP_RETRIES=20

WORKDIR /app

COPY services/forecast_service/requirements.txt /tmp/requirements.txt

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gdal-bin \
        libgdal-dev \
        libspatialindex-dev \
        build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --progress-bar off -r /tmp/requirements.txt

COPY . /app/flood_api
ENV PYTHONPATH=/app
ENV GDAL_DATA=/usr/share/gdal

EXPOSE 5002

CMD ["python", "-m", "flood_api.services.forecast_service.app"]
