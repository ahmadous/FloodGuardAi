FROM python:3.11-slim

ARG TORCH_INDEX=https://download.pytorch.org/whl/cpu
# Extra index for CPU-only PyTorch wheels and more forgiving pip network settings to avoid timeouts
ENV PIP_EXTRA_INDEX_URL=${TORCH_INDEX} \
    PIP_DEFAULT_TIMEOUT=600 \
    PIP_RETRIES=20

WORKDIR /app

COPY services/classification_service/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --progress-bar off -r /tmp/requirements.txt

COPY . /app/flood_api
ENV PYTHONPATH=/app

EXPOSE 5001

CMD ["python", "-m", "flood_api.services.classification_service.app"]
