FROM python:3.11-slim

WORKDIR /app

COPY gateway/requirements.txt /tmp/requirements.txt

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gdal-bin \
        libgdal-dev \
        libspatialindex-dev \
        build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r /tmp/requirements.txt

COPY . /app/flood_api
ENV PYTHONPATH=/app
ENV GDAL_DATA=/usr/share/gdal

EXPOSE 5000

CMD ["python", "-m", "flood_api.gateway.app"]
