# Makefile for Docker deployment management

.PHONY: help build up down logs clean dev prod simple with-rag with-redis with-db status restart

# Default target
help:
	@echo "Available commands:"
	@echo "  make build     - Build all Docker images"
	@echo "  make up        - Start services (standard deployment)"
	@echo "  make down      - Stop and remove services"
	@echo "  make logs      - View logs from all services"
	@echo "  make clean     - Remove all containers, networks, and volumes"
	@echo "  make dev       - Start development environment"
	@echo "  make prod      - Start production environment"
	@echo "  make simple    - Start with simple agent API"
	@echo "  make with-rag  - Start with RAG pipeline"
	@echo "  make with-redis - Start with Redis caching"
	@echo "  make with-db   - Start with PostgreSQL database"
	@echo "  make status    - Show service status"
	@echo "  make restart   - Restart all services"
	@echo ""
	@echo "Environment setup:"
	@echo "  make env       - Copy .env.example to .env"
	@echo ""
	@echo "Maintenance:"
	@echo "  make backup    - Backup persistent data"
	@echo "  make update    - Pull latest images and restart"

# Environment setup
env:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env file from .env.example"; \
		echo "Please edit .env with your actual values"; \
	else \
		echo ".env file already exists"; \
	fi

# Build all images
build:
	docker-compose build --parallel

# Standard deployment
up: env
	docker-compose up -d

# Stop services
down:
	docker-compose down

# View logs
logs:
	docker-compose logs -f

# Development environment
dev: env
	docker-compose -f docker-compose.dev.yml up -d

# Production environment
prod: env
	docker-compose -f docker-compose.yml up -d

# Simple deployment (without MCP server)
simple: env
	docker-compose --profile simple up -d

# With RAG pipeline
with-rag: env
	docker-compose --profile with-rag up -d

# With Redis caching
with-redis: env
	docker-compose --profile with-redis up -d

# With PostgreSQL database
with-db: env
	docker-compose --profile with-db up -d

# Full stack with all services
full: env
	docker-compose --profile with-rag --profile with-redis --profile with-db up -d

# Service status
status:
	docker-compose ps

# Restart services
restart:
	docker-compose restart

# Clean up everything
clean:
	docker-compose down -v --remove-orphans
	docker system prune -a -f

# Backup persistent data
backup:
	@echo "Creating backup directory..."
	@mkdir -p backups
	@echo "Backing up agent data..."
	@docker run --rm -v deployment-example_agent_data:/data -v $(PWD)/backups:/backup alpine tar czf /backup/agent_data_$(shell date +%Y%m%d_%H%M%S).tar.gz -C /data .
	@if docker volume ls | grep -q postgres_data; then \
		echo "Backing up postgres data..."; \
		docker run --rm -v deployment-example_postgres_data:/data -v $(PWD)/backups:/backup alpine tar czf /backup/postgres_data_$(shell date +%Y%m%d_%H%M%S).tar.gz -C /data .; \
	fi
	@if docker volume ls | grep -q redis_data; then \
		echo "Backing up redis data..."; \
		docker run --rm -v deployment-example_redis_data:/data -v $(PWD)/backups:/backup alpine tar czf /backup/redis_data_$(shell date +%Y%m%d_%H%M%S).tar.gz -C /data .; \
	fi
	@echo "Backup completed in backups/ directory"

# Update and restart
update:
	docker-compose pull
	docker-compose up -d

# Health check
health:
	@echo "Checking service health..."
	@docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
	@echo ""
	@echo "Testing endpoints..."
	@curl -s -o /dev/null -w "Frontend: %{http_code}\n" http://localhost:3000 || echo "Frontend: Not responding"
	@curl -s -o /dev/null -w "Agent API: %{http_code}\n" http://localhost:8001/health || echo "Agent API: Not responding"

# Install dependencies for development
install:
	@echo "Installing frontend dependencies..."
	@cd frontend && npm install
	@echo "Installing agent API dependencies..."
	@cd agent_api && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
	@echo "Installing RAG pipeline dependencies..."
	@cd rag_pipeline && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt

# Run tests
test:
	@echo "Running agent API tests..."
	@cd agent_api && source venv/bin/activate && pytest tests/ -v
	@echo "Running RAG pipeline tests..."
	@cd rag_pipeline && source venv/bin/activate && pytest tests/ -v

# Development helpers
dev-logs:
	docker-compose -f docker-compose.dev.yml logs -f

dev-down:
	docker-compose -f docker-compose.dev.yml down

prod-logs:
	docker-compose -f docker-compose.yml logs -f

prod-down:
	docker-compose -f docker-compose.yml down