# Integration Tests

This directory contains integration tests for the PDF Viewer application, testing the complete system including frontend, backend, and their interactions.

## Directory Structure

```
integration/
├── api/                 # API integration tests
│   ├── test_pdf_workflow.py     # Complete PDF processing workflows
│   ├── test_error_handling.py   # Error scenarios and edge cases
│   └── test_performance.py      # Performance and load tests
├── frontend/           # Frontend integration tests (Playwright E2E)
├── fixtures/           # Test data files
├── config/            # Test configuration
│   └── test_settings.py        # Test environment settings
└── conftest.py        # Shared fixtures
```

## Running Integration Tests

### API Integration Tests

```bash
# Run all integration tests
pytest tests/integration/

# Run specific test categories
pytest tests/integration/api/test_pdf_workflow.py
pytest tests/integration/api/test_error_handling.py
pytest tests/integration/api/test_performance.py

# Run with coverage
pytest tests/integration/ --cov=backend.app --cov-report=html
```

### E2E Tests (Playwright)

```bash
# Run all E2E tests
npm run test:e2e

# Run in UI mode
npm run test:e2e:ui

# Run specific test file
npx playwright test tests/e2e/tests/test_upload_flow.spec.ts
```

## Test Categories

### 1. Workflow Tests (`test_pdf_workflow.py`)
- Complete PDF processing lifecycle
- Concurrent operations
- Retry logic
- Correlation ID propagation

### 2. Error Handling Tests (`test_error_handling.py`)
- Invalid file uploads
- Malformed requests
- Resource not found scenarios
- Concurrent deletion handling
- Special character handling

### 3. Performance Tests (`test_performance.py`)
- Response time measurements
- Concurrent load testing
- Page rendering performance
- Memory efficiency
- Large file handling

## Environment Variables

Configure tests using these environment variables:

```bash
# Test environment
TEST_ENV=local|staging|production
TEST_BASE_URL=http://localhost:8000
TEST_FRONTEND_URL=http://localhost:5173

# Performance settings
ENABLE_PERFORMANCE_TESTS=true
ENABLE_STRESS_TESTS=false

# E2E settings
E2E_HEADLESS=true
E2E_SLOW_MO=0
E2E_TIMEOUT=30000

# Logging
TEST_LOG_LEVEL=INFO
CAPTURE_LOGS=false
```

## Performance Benchmarks

Expected performance targets:

- **Upload Response**: < 500ms average
- **Page Rendering**: < 1000ms average
- **PDF Analysis**: < 5000ms for standard documents
- **Concurrent Uploads**: > 10 uploads/second throughput

## Writing New Integration Tests

1. **Use async/await**: All API tests should be async
2. **Clean up resources**: Always delete uploaded files after tests
3. **Use fixtures**: Leverage conftest.py fixtures for common setup
4. **Test realistic scenarios**: Focus on user workflows
5. **Include timing**: Measure and assert on performance

Example test structure:

```python
@pytest.mark.asyncio
async def test_complete_workflow(async_client, sample_pdf_path):
    # Arrange
    # ... setup test data
    
    # Act
    # ... perform operations
    
    # Assert
    # ... verify results
    
    # Cleanup
    # ... delete test resources
```

## CI/CD Integration

The integration tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions configuration
- name: Run Integration Tests
  run: |
    docker-compose up -d
    npm run test:integration
    docker-compose down
```

## Troubleshooting

### Common Issues

1. **Port conflicts**: Ensure ports 8000 and 5173 are available
2. **File permissions**: Check write permissions for upload directory
3. **Memory issues**: Increase Docker memory for large file tests
4. **Timeout errors**: Adjust E2E_TIMEOUT for slower environments

### Debug Mode

Run tests with detailed logging:

```bash
# API tests with debug logs
pytest tests/integration/ -v -s --log-cli-level=DEBUG

# E2E tests with headed browser
E2E_HEADLESS=false npm run test:e2e
```