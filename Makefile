.PHONY: run-backend run-classification run-forecast stop-classification stop-forecast

run-classification:
	python -m flood_api.services.classification_service.app

run-forecast:
	python -m flood_api.services.forecast_service.app

stop-classification:
	@echo "Stopping classification service on port 5001 (if running)..."
	-lsof -ti tcp:5001 | xargs -r kill

stop-forecast:
	@echo "Stopping forecast service on port 5002 (if running)..."
	-lsof -ti tcp:5002 | xargs -r kill

run-backend:
	@echo "Starting classification and forecast services (Ctrl+C to stop)..."
	@bash -lc 'trap "kill $$pids 2>/dev/null" EXIT INT TERM; \
	  python -m flood_api.services.classification_service.app & \
	  pids="$$!"; \
	  python -m flood_api.services.forecast_service.app & \
	  pids="$$pids $$!"; \
	  wait'
