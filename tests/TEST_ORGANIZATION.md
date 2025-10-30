# Test Suite Organization

This document describes the organization of the PDF Viewer test suite, which has been refactored into a module-based structure with separated edge cases.

## Directory Structure

```
tests/
├── unit/                        # Unit tests organized by module
│   ├── api/                     # API endpoint tests
│   ├── services/                # Service layer tests
│   ├── models/                  # Pydantic model tests
│   ├── utils/                   # Utility function tests
│   ├── middleware/              # Middleware tests
│   └── edge_cases/              # Edge case tests
├── samples/                     # Sample PDF integration tests
├── integration/                 # Integration tests
│   ├── api/                     # API integration tests
│   └── config/                  # Configuration tests
└── e2e/                         # End-to-end tests (Playwright)
```

## Module Categories

### Unit Tests (`unit/`)

Unit tests are organized by the module they test. Each subdirectory contains tests for a specific layer of the application:

#### API Tests (`unit/api/`)
Tests for FastAPI endpoint handlers:
- `test_health.py` - Health check endpoint
- `test_upload.py` - File upload endpoint
- `test_pdf_endpoints.py` - PDF retrieval endpoints
- `test_load_url_api_comprehensive.py` - Load PDF from URL endpoint
- `test_pdf_api_comprehensive.py` - Comprehensive API tests

#### Service Tests (`unit/services/`)
Tests for business logic services:
- `test_pdf_service.py` - Core PDF service functionality
- `test_pdf_service_comprehensive.py` - Comprehensive service tests

#### Model Tests (`unit/models/`)
Tests for Pydantic data models:
- `test_pydantic_models.py` - Model validation and computed fields

#### Utility Tests (`unit/utils/`)
Tests for utility functions and helpers:
- `test_validation.py` - Validation utilities
- `test_utils_decorators.py` - Function decorators
- `test_http_client.py` - HTTP client utilities
- `test_content_disposition.py` - Content-Disposition header utilities
- `test_api_logging.py` - API logging utilities
- `test_core_logging.py` - Core logging functionality
- `test_dependencies.py` - Dependency injection
- `test_utils_logger_comprehensive.py` - Comprehensive logger tests

#### Middleware Tests (`unit/middleware/`)
Tests for FastAPI middleware:
- `test_logging_middleware.py` - Request/response logging middleware
- `test_middleware_logging_comprehensive.py` - Comprehensive middleware tests

### Edge Case Tests (`unit/edge_cases/`)

Edge case tests focus on boundary conditions, error handling, and unusual inputs. These are separated from regular unit tests to:
- Clearly identify tests for error conditions
- Facilitate testing of boundary values
- Make it easier to ensure comprehensive error handling coverage

**Files:**
- `test_upload_edge_cases.py` - Upload edge cases (invalid files, missing names, oversized files)
- `test_health_edge_cases.py` - Health endpoint edge cases (storage unavailable, invalid status)
- `test_pdf_service_edge_cases.py` - Service validation edge cases (invalid extensions, file size limits)
- `test_validation_edge_cases.py` - Validation utility edge cases (empty strings, None values)
- `test_pydantic_models_edge_cases.py` - Model validation edge cases (boundary values, invalid ranges)

### Sample PDF Tests (`samples/`)

Tests that use real-world sample PDF documents to verify correct handling of various PDF types:
- `test_epa_sample.py` - EPA government PDF sample
- `test_weblite_sample.py` - OCR scanned PDF sample
- `test_princexml_sample.py` - Large essay PDF sample
- `test_anyline_sample.py` - Complex image and barcode PDF sample
- `test_nhtsa_form.py` - PDF form with structured fields

### Integration Tests (`integration/`)

End-to-end integration tests for complete workflows:
- `api/test_pdf_workflow.py` - Complete PDF processing workflows
- `api/test_error_handling.py` - Error handling across components
- `api/test_performance.py` - Performance benchmarks
- `api/test_load_url.py` - URL loading integration tests

### E2E Tests (`e2e/`)

Browser-based end-to-end tests using Playwright:
- `tests/test_pdf_viewer.spec.ts` - PDF viewer UI tests
- `tests/test_pdf_loader_local.spec.ts` - Local PDF loading tests
- Additional UI interaction tests

## Running Tests

### Run All Tests
```bash
make test              # Run all unit and integration tests
make test-all          # Run all tests including E2E
```

### Run by Category
```bash
make test-unit              # All unit tests
make test-edge-cases        # Edge case tests only
make test-samples           # Sample PDF tests only
make test-integration       # Integration tests
make test-e2e              # E2E tests (requires servers running)
```

### Run Specific Module Tests
```bash
# Run tests for a specific module
pytest tests/unit/api                # All API tests
pytest tests/unit/services           # All service tests
pytest tests/unit/models             # All model tests
pytest tests/unit/utils              # All utility tests
pytest tests/unit/middleware         # All middleware tests

# Run a specific test file
pytest tests/unit/api/test_upload.py           # Upload tests
pytest tests/unit/edge_cases/test_upload_edge_cases.py  # Upload edge cases
```

### Run with Options
```bash
make test-coverage          # Run with coverage reports
make test-watch             # Run in watch mode
make test-debug             # Run with debugger
make test-parallel          # Run in parallel
```

## Test Organization Principles

### Separation of Concerns
- **Unit tests** focus on testing individual functions/methods in isolation
- **Edge case tests** focus on boundary conditions and error scenarios
- **Sample tests** verify behavior with real-world documents
- **Integration tests** verify component interactions and workflows
- **E2E tests** verify complete user workflows through the UI

### File Naming
- Unit tests: `test_<module_name>.py`
- Edge case tests: `test_<module_name>_edge_cases.py`
- Sample tests: `test_<sample_name>_sample.py`
- Comprehensive tests: `test_<module_name>_comprehensive.py`

### Test Naming
- Descriptive names: `test_<what_is_being_tested>`
- Valid scenarios: `test_upload_valid_pdf`
- Edge cases: `test_validate_file_missing_filename`
- Error conditions: `test_upload_invalid_file_type`

### Benefits of This Structure

1. **Clarity**: Easy to find tests for specific modules or scenarios
2. **Maintainability**: Changes to a module only affect tests in that module's directory
3. **Targeted Testing**: Run only relevant tests during development
4. **Coverage**: Edge cases are explicitly identified and tracked
5. **Scalability**: New test categories can be added without cluttering existing structure
6. **Documentation**: Directory structure serves as documentation of test coverage

## Adding New Tests

### Adding a Unit Test
1. Identify the module being tested (api, services, models, utils, middleware)
2. Create or update the test file in the appropriate directory
3. Follow existing test patterns and naming conventions

### Adding an Edge Case Test
1. Identify which module's edge cases you're testing
2. Create or update the corresponding `test_<module>_edge_cases.py` file
3. Focus on boundary conditions, invalid inputs, and error scenarios

### Adding a Sample PDF Test
1. Obtain or identify a sample PDF URL
2. Add fixture in `conftest.py` if needed
3. Create `test_<sample_name>_sample.py` in `tests/samples/`
4. Test upload, metadata extraction, and any special characteristics

### Adding an Integration Test
1. Identify the workflow or interaction being tested
2. Add test in appropriate `tests/integration/` subdirectory
3. Use real components (minimal mocking)
4. Test complete scenarios end-to-end

## Migration Notes

This structure was created by refactoring the original flat test structure. The following changes were made:

1. **Moved unit tests** from `tests/test_*.py` to `tests/unit/<module>/test_*.py`
2. **Extracted edge cases** from unit tests into `tests/unit/edge_cases/`
3. **Moved sample tests** to `tests/samples/`
4. **Updated Makefile** targets to reference new paths
5. **Updated documentation** to reflect new structure

All test functionality remains the same; only the organization has changed.

## Related Documentation

- [tests/README.md](README.md) - Main test documentation
- [CLAUDE.md](../CLAUDE.md) - Development guide
- [CONTRIBUTING.md](../docs/CONTRIBUTING.md) - Contribution guidelines
