# PDF Viewer Makefile
# Provides common development commands for both backend and frontend

.PHONY: help
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Linting commands
.PHONY: lint
lint: lint-backend lint-frontend ## Run all linters

.PHONY: lint-backend
lint-backend: ## Run backend linters (ruff)
	@echo "Running backend linters..."
	ruff check backend tests

.PHONY: lint-frontend
lint-frontend: ## Run frontend linters (eslint)
	@echo "Running frontend linters..."
	cd frontend && npm run lint

# Formatting commands
.PHONY: format
format: format-backend format-frontend ## Format all code

.PHONY: format-backend
format-backend: ## Format backend code (ruff + black)
	@echo "Formatting backend code..."
	ruff format backend tests
	black backend tests

.PHONY: format-frontend
format-frontend: ## Format frontend code (prettier)
	@echo "Formatting frontend code..."
	cd frontend && npm run format

# Type checking commands
.PHONY: type
type: type-backend type-frontend ## Run all type checkers

.PHONY: type-backend
type-backend: ## Run backend type checker (mypy)
	@echo "Type checking backend..."
	mypy .

.PHONY: type-frontend
type-frontend: ## Run frontend type checker (tsc)
	@echo "Type checking frontend..."
	cd frontend && npx tsc --noEmit

# Check commands (verify without modifying)
.PHONY: check
check: check-format check-lint check-type ## Run all checks without modifying files

.PHONY: check-format
check-format: check-format-backend check-format-frontend ## Check formatting without modifying

.PHONY: check-format-backend
check-format-backend: ## Check backend formatting
	@echo "Checking backend formatting..."
	ruff format --check backend tests
	black --check backend tests

.PHONY: check-format-frontend
check-format-frontend: ## Check frontend formatting
	@echo "Checking frontend formatting..."
	cd frontend && npx prettier --check "src/**/*.{ts,tsx,js,jsx,json,css,md}"

.PHONY: check-lint
check-lint: lint ## Same as lint (no modifications)

.PHONY: check-type
check-type: type ## Same as type (no modifications)

# Test commands
.PHONY: test
test: test-unit test-integration ## Run all tests (unit and integration)

.PHONY: test-all
test-all: test-unit test-integration test-e2e ## Run ALL tests including E2E

.PHONY: test-unit
test-unit: test-unit-backend test-unit-frontend ## Run all unit tests

.PHONY: test-unit-backend
test-unit-backend: ## Run backend unit tests
	@echo "Running backend unit tests..."
	pytest tests/test_*.py -v --tb=short

.PHONY: test-unit-frontend
test-unit-frontend: ## Run frontend unit tests
	@echo "Running frontend unit tests..."
	cd frontend && npm test -- --run

.PHONY: test-integration
test-integration: test-integration-api test-integration-fixtures ## Run all integration tests

.PHONY: test-integration-api
test-integration-api: ## Run API integration tests
	@echo "Running API integration tests..."
	pytest tests/integration/api -v --tb=short

.PHONY: test-integration-fixtures
test-integration-fixtures: ## Verify integration test fixtures
	@echo "Verifying integration test fixtures..."
	@if [ ! -f "tests/integration/fixtures/sample.pdf" ]; then \
		echo "Downloading test fixtures..."; \
		cd tests/integration/fixtures && python download_samples.py; \
	fi

.PHONY: test-e2e
test-e2e: ## Run E2E tests (requires running servers)
	@echo "Running E2E tests..."
	@echo "Make sure servers are running (make dev-backend and make dev-frontend)"
	cd tests/e2e && npm test

.PHONY: test-watch
test-watch: ## Run tests in watch mode
	@echo "Choose watch mode:"
	@echo "  make test-watch-backend   - Watch backend tests"
	@echo "  make test-watch-frontend  - Watch frontend tests"

.PHONY: test-watch-backend
test-watch-backend: ## Run backend tests in watch mode
	@echo "Running backend tests in watch mode..."
	pytest-watch tests/ --runner "pytest -v"

.PHONY: test-watch-frontend
test-watch-frontend: ## Run frontend tests in watch mode
	@echo "Running frontend tests in watch mode..."
	cd frontend && npm test

.PHONY: test-coverage
test-coverage: test-coverage-backend test-coverage-frontend ## Run tests with coverage

.PHONY: test-coverage-backend
test-coverage-backend: ## Run backend tests with coverage
	@echo "Running backend tests with coverage..."
	pytest --cov=backend --cov-report=html --cov-report=term

.PHONY: test-coverage-frontend
test-coverage-frontend: ## Run frontend tests with coverage
	@echo "Running frontend tests with coverage..."
	cd frontend && npm test -- --coverage --run

.PHONY: test-coverage-report
test-coverage-report: ## Open coverage reports
	@echo "Opening coverage reports..."
	@if [ -d "htmlcov" ]; then \
		open htmlcov/index.html || xdg-open htmlcov/index.html || echo "Backend coverage: htmlcov/index.html"; \
	fi
	@if [ -d "frontend/coverage" ]; then \
		open frontend/coverage/index.html || xdg-open frontend/coverage/index.html || echo "Frontend coverage: frontend/coverage/index.html"; \
	fi

.PHONY: test-failed
test-failed: ## Re-run only failed tests
	@echo "Re-running failed backend tests..."
	pytest --lf -v
	@echo "Re-running failed frontend tests..."
	cd frontend && npm test -- --run --reporter=verbose

.PHONY: test-specific
test-specific: ## Run specific test file (use TEST=path/to/test.py or TEST=ComponentName)
	@if [ -z "$(TEST)" ]; then \
		echo "Usage: make test-specific TEST=path/to/test.py"; \
		echo "   or: make test-specific TEST=ComponentName"; \
		exit 1; \
	fi
	@if echo "$(TEST)" | grep -q ".py$$"; then \
		echo "Running Python test: $(TEST)"; \
		pytest "$(TEST)" -v; \
	else \
		echo "Running JavaScript test: $(TEST)"; \
		cd frontend && npm test -- --run --reporter=verbose "$(TEST)"; \
	fi

.PHONY: test-debug
test-debug: ## Run tests with debugging enabled
	@echo "Choose debug mode:"
	@echo "  make test-debug-backend   - Debug backend tests"
	@echo "  make test-debug-frontend  - Debug frontend tests"

.PHONY: test-debug-backend
test-debug-backend: ## Run backend tests with pdb on failure
	@echo "Running backend tests with debugging..."
	pytest --pdb --pdbcls=IPython.terminal.debugger:TerminalPdb -v

.PHONY: test-debug-frontend
test-debug-frontend: ## Run frontend tests with debugging
	@echo "Running frontend tests with debugging..."
	cd frontend && npm test -- --run --reporter=verbose --inspect

.PHONY: test-performance
test-performance: ## Run performance tests
	@echo "Running performance tests..."
	pytest tests/integration/api/test_performance.py -v

.PHONY: test-smoke
test-smoke: ## Run quick smoke tests
	@echo "Running smoke tests..."
	pytest tests/test_health.py -v --no-cov
	cd frontend && npm test -- --run src/components/__tests__/FileUpload.test.tsx

.PHONY: test-nocov
test-nocov: ## Run tests without coverage requirements
	@echo "Running tests without coverage requirements..."
	pytest tests/test_*.py -v --no-cov
	cd frontend && npm test -- --run

# Backward compatibility aliases
.PHONY: test-backend
test-backend: test-unit-backend test-integration-api ## Run all backend tests

.PHONY: test-frontend
test-frontend: test-unit-frontend ## Run all frontend tests

# Development commands
.PHONY: dev
dev: ## Start development servers (requires two terminals)
	@echo "Start backend: make dev-backend"
	@echo "Start frontend: make dev-frontend"

.PHONY: dev-backend
dev-backend: ## Start backend development server
	cd backend && uvicorn app.main:app --reload

.PHONY: dev-frontend
dev-frontend: ## Start frontend development server
	cd frontend && npm run dev

# Installation commands
.PHONY: install
install: install-backend install-frontend ## Install all dependencies

.PHONY: install-backend
install-backend: ## Install backend dependencies
	@echo "Installing backend dependencies..."
	uv pip install -e ".[dev]"

.PHONY: install-frontend
install-frontend: ## Install frontend dependencies
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	cd tests/e2e && npm install

# Clean commands
.PHONY: clean
clean: ## Clean temporary files and caches
	@echo "Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
	rm -rf .mypy_cache
	rm -rf .pytest_cache
	rm -rf frontend/node_modules/.cache
	rm -rf frontend/dist
	rm -rf htmlcov
	rm -rf .ruff_cache

# Docker commands
.PHONY: docker-up
docker-up: ## Start Docker containers
	docker-compose up -d

.PHONY: docker-down
docker-down: ## Stop Docker containers
	docker-compose down

.PHONY: docker-logs
docker-logs: ## View Docker logs
	docker-compose logs -f

# Quality assurance - run before committing
.PHONY: qa
qa: format lint type test ## Run full QA suite (format, lint, type, test)
	@echo "All QA checks passed! ✅"

# Quick check - faster than qa
.PHONY: quick
quick: check-format check-lint ## Run quick checks (format and lint verification)

# Pre-commit hook
.PHONY: pre-commit
pre-commit: check-format check-lint test-smoke ## Run pre-commit checks
	@echo "Pre-commit checks passed! ✅"

# CI/CD pipeline commands
.PHONY: ci
ci: install check-format check-lint type test-coverage ## Run CI pipeline checks

.PHONY: ci-backend
ci-backend: install-backend check-format-backend lint-backend type-backend test-coverage-backend ## Run backend CI checks

.PHONY: ci-frontend
ci-frontend: install-frontend check-format-frontend lint-frontend type-frontend test-coverage-frontend ## Run frontend CI checks

# Test report generation
.PHONY: test-report
test-report: ## Generate test reports in various formats
	@echo "Generating test reports..."
	pytest --html=reports/pytest-report.html --self-contained-html --cov=backend --cov-report=html
	cd frontend && npm test -- --coverage --run --reporter=junit --outputFile=../reports/vitest-report.xml

# Parallel test execution
.PHONY: test-parallel
test-parallel: ## Run tests in parallel for faster execution
	@echo "Running tests in parallel..."
	pytest -n auto tests/
	cd frontend && npm test -- --run