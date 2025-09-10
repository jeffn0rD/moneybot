.PHONY: dev up down test train backtest

# Default development setup with Redis
dev: up

# Start orchestrator and Redis together
up:
	@echo "Starting Redis and orchestrator..."
	@tmux new-session -d -s moneybot "redis-server"
	@tmux new-window -t moneybot -n orchestrator "cd /workspace/moneybot && uvicorn apps.orchestrator.main:app --reload"
	@echo "Services started in tmux session 'moneybot'"
	@echo "Redis running on default port 6379"
	@echo "Orchestrator running on port 8000"
	@echo "Use 'make down' to stop services"

# Stop all services
down:
	@echo "Stopping services..."
	@tmux kill-session -t moneybot || true
	@echo "Services stopped"

# Run tests
test:
	@echo "Running tests..."
	@cd /workspace/moneybot && python -m pytest tests/ -v

# Train meta-learner
train:
	@echo "Training meta-learner..."
	@cd /workspace/moneybot && python libs/models/train_meta.py --symbol AAPL --start 2022-01-01 --end 2024-12-31 --horizon 5 --outfile models/meta_lgbm.pkl

# Run backtest
backtest:
	@echo "Running backtest..."
	@cd /workspace/moneybot && python backtester/engine.py --symbol AAPL --start 2022-01-01 --end 2024-12-31 --horizon 5

# Start external price model server
price-model:
	@echo "Starting external price model server..."
	@cd /workspace/moneybot && uvicorn apps.price_model_server.main:app --port 9000