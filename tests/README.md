# PDF Viewer Test Suite

[![Testing](https://img.shields.io/badge/testing-pytest%20%7C%20vitest%20%7C%20playwright-blue.svg)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-80%25%20threshold-green.svg)](tests/)

This directory contains comprehensive tests for the PDF Viewer application following best practices for test organization and execution.

## Table of Contents

- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
  - [Using Make Commands (Recommended)](#using-make-commands-recommended)
  - [Manual Commands](#manual-commands)
- [Test Categories](#test-categories)
- [Best Practices](#best-practices)
- [Coverage Requirements](#coverage-requirements)
- [CI/CD Integration](#cicd-integration)
- [Debugging Tests](#debugging-tests)
- [Performance Testing](#performance-testing)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## Test Structure

```
tests/
├── unit/                        # Unit tests organized by module
│   ├── api/                     # API endpoint unit tests
│   │   ├── test_health.py
│   │   ├── test_upload.py
│   │   ├── test_pdf_endpoints.py
│   │   └── test_pdf_api_comprehensive.py
│   ├── services/                # Service layer unit tests
│   │   ├── test_pdf_service.py
│   │   └── test_pdf_service_comprehensive.py
│   ├── models/                  # Pydantic model unit tests
│   │   └── test_pydantic_models.py
│   ├── utils/                   # Utility function unit tests
│   │   ├── test_validation.py
│   │   ├── test_http_client.py
│   │   └── test_utils_decorators.py
│   └── middleware/              # Middleware unit tests
│       ├── test_logging_middleware.py
│       └── test_api_logging.py
├── integration/                 # Integration tests
│   ├── api/                     # API integration tests
│   │   ├── test_pdf_workflow.py
│   │   ├── test_error_handling.py
│   │   ├── test_performance.py
│   │   └── test_load_url.py
│   ├── test_*_sample.py         # Sample PDF integration tests
│   ├── fixtures/                # Test data and fixtures
│   │   ├── sample.pdf
│   │   └── download_samples.py
│   └── conftest.py             # Integration test configuration
├── e2e/                        # End-to-end tests (Playwright)
│   ├── tests/
│   │   ├── test_pdf_viewer.spec.ts
│   │   └── test_pdf_loader_local.spec.ts
│   └── playwright.config.ts
└── conftest.py                 # Pytest configuration
```

## Running Tests

### Using Make Commands (Recommended)

```bash
# Run all tests (unit + integration)
make test

# Run all tests including E2E
make test-all

# Run specific test suites
make test-unit              # All unit tests
make test-integration       # All integration tests
make test-e2e              # E2E tests (requires running servers)

# Run with coverage
make test-coverage          # Generate coverage reports
make test-coverage-report   # Open coverage reports in browser

# Run specific test categories
make test-unit-backend      # All backend unit tests
make test-unit-api          # API unit tests only
make test-unit-services     # Service unit tests only
make test-unit-models       # Model unit tests only
make test-unit-utils        # Utils unit tests only
make test-unit-middleware   # Middleware unit tests only
make test-unit-frontend     # Frontend unit tests only
make test-integration-api   # API integration tests
make test-integration-samples  # Sample PDF integration tests
make test-performance       # Performance tests only

# Development helpers
make test-watch            # Run tests in watch mode
make test-failed          # Re-run only failed tests
make test-specific TEST=path/to/test.py  # Run specific test file
make test-debug           # Run with debugging enabled
make test-parallel        # Run tests in parallel
```

### Manual Commands

```bash
# Backend tests
pytest tests/                     # Run all backend tests
pytest tests/unit/api            # Run API unit tests
pytest tests/unit/services       # Run service unit tests
pytest tests/integration         # Run integration tests
pytest -k "test_upload"          # Run tests matching pattern
pytest -v --tb=short            # Verbose with short traceback
pytest --pdb                    # Drop into debugger on failure

# Frontend tests
cd frontend && npm test         # Run all frontend tests
cd frontend && npm test -- --run  # Run once (not in watch mode)

# E2E tests
cd tests/e2e && npm test        # Run E2E tests
```

## Test Categories

### 1. Unit Tests (`unit/`)
- Fast, isolated tests for individual components
- Organized by module (api/, services/, models/, utils/, middleware/)
- Mock external dependencies
- Focus on business logic and edge cases
- **Edge case tests**: Files ending in `_edge_cases.py` provide additional coverage
  for boundary conditions and error scenarios

### 2. Integration Tests (`integration/`)
- Test API endpoints with real filesystem/network
- Verify component interactions
- Test error handling and edge cases
- **Sample PDF tests**: `test_sample_pdfs.py` uses parametrization to test
  multiple PDF types (EPA, Weblite, PrinceXML, Anyline, NHTSA) efficiently

### 3. E2E Tests (`e2e/`)
- Full user workflows through the browser
- Test real user interactions
- Verify frontend-backend integration

### 4. Performance Tests
- Response time benchmarks
- Concurrent request handling
- Large file processing
- Memory efficiency

## Best Practices

### Test Organization
- **Module-based structure**: Unit tests are organized by module (api/, services/, models/, utils/, middleware/)
- **One test file per module/component**: e.g., `test_pdf_service.py` for PDFService
- **Edge case separation**: Additional coverage in `*_edge_cases.py` files for boundary conditions
- **Clear test names**: Use descriptive names like `test_should_reject_invalid_pdf_format()`
- **Group related tests in classes**: Use Test classes to group related functionality
- **Use descriptive assertions**: Include helpful assertion messages

### Test Data
- Use fixtures for reusable test data
- Store sample PDFs in `integration/fixtures/`
- Generate test data programmatically when possible
- Clean up test data after tests

### Mocking and Fixtures
```python
# Use pytest fixtures
@pytest.fixture
def sample_pdf():
    return Path("tests/integration/fixtures/sample.pdf")

# Mock external services
@patch('app.services.external_api')
def test_with_mock(mock_api):
    mock_api.return_value = {"status": "ok"}
```

### Async Testing
```python
@pytest.mark.asyncio
async def test_async_endpoint(async_client):
    response = await async_client.get("/api/health")
    assert response.status_code == 200
```

## Coverage Requirements

- Minimum coverage: 80%
- Backend coverage: `pytest --cov=backend`
- Frontend coverage: `npm test -- --coverage`
- View reports: `make test-coverage-report`

## CI/CD Integration

Tests are run automatically on:
- Pull requests (all tests)
- Main branch commits (full test suite)
- Pre-commit hooks (format + lint + smoke tests)

### Pre-commit Setup
```bash
# Install pre-commit hook
make pre-commit

# Run CI checks locally
make ci
```

## Debugging Tests

### Backend Tests
```bash
# Run with pdb debugger
pytest --pdb tests/test_health.py

# Show local variables on failure
pytest -l

# Verbose output
pytest -vv

# Run specific test
pytest tests/test_health.py::test_health_check
```

### Frontend Tests
```bash
# Debug in browser
cd frontend && npm test -- --inspect

# Run specific component test
npm test PDFViewer

# Update snapshots
npm test -- -u
```

### E2E Tests
```bash
# Run with headed browser
cd tests/e2e && npx playwright test --headed

# Debug mode
npx playwright test --debug

# Generate test code
npx playwright codegen http://localhost:5173
```

## Performance Testing

Performance tests verify:
- Upload response time < 500ms average
- Page rendering < 1s average
- Concurrent upload handling
- Memory efficiency

Run performance tests:
```bash
make test-performance
```

## Troubleshooting

### Common Issues

1. **Tests timeout**: Increase timeout in pytest.ini or test file
   ```python
   @pytest.mark.timeout(30)
   def test_slow_operation():
       pass
   ```

2. **Port conflicts**: Ensure dev servers aren't running
   ```bash
   lsof -i :8000  # Check backend port
   lsof -i :5173  # Check frontend port
   ```

3. **Missing fixtures**: Download test PDFs
   ```bash
   cd tests/integration/fixtures
   python download_samples.py
   ```

4. **Coverage failures**: Focus on critical paths
   - API endpoints
   - Business logic
   - Error handling

## Contributing

When adding new tests:
1. Follow existing patterns
2. Add appropriate fixtures
3. Update this README if needed
4. Ensure tests pass locally
5. Check coverage impact