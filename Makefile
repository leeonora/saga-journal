.PHONY: run run-backend run-frontend install stop

install:
	@echo "Installing backend dependencies..."
	@cd saga-backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	@cd saga-frontend && npm install

run:
	@echo "Starting backend in the background..."
	@$(MAKE) run-backend &
	@echo "Starting frontend in the foreground..."
	@$(MAKE) run-frontend

run-backend:
	@echo "Starting backend..."
	@cd saga-backend && uvicorn main:app --reload

run-frontend:
	@echo "Starting frontend and opening Firefox..."
	@(sleep 5 && Safari http://localhost:9002/) &
	@cd saga-frontend && npm run dev

stop:
	@echo "Stopping backend..."
	@pkill -f "uvicorn main:app --reload"