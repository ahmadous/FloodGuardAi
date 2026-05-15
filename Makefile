.PHONY: run-backend run-classification stop-classification

run-classification:
	python -m flood_api.services.classification_service.app

stop-classification:
	@echo "Stopping classification service on port 5001 (if running)..."
	-lsof -ti tcp:5001 | xargs -r kill

run-backend:
	@echo "Starting classification service (Ctrl+C to stop)..."
	python -m flood_api.services.classification_service.app
