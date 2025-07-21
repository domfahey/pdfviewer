"""
Test configuration settings for integration tests.
"""
import os
from pathlib import Path

# Test environment settings
TEST_ENV = os.getenv("TEST_ENV", "local")
BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("TEST_FRONTEND_URL", "http://localhost:5173")

# Test data paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
TEST_DATA_DIR = PROJECT_ROOT / "tests" / "fixtures"
INTEGRATION_TEST_DIR = PROJECT_ROOT / "tests" / "integration"

# Performance test thresholds (in milliseconds)
UPLOAD_TIMEOUT_MS = 5000
ANALYSIS_TIMEOUT_MS = 10000
PAGE_RENDER_TIMEOUT_MS = 3000

# Concurrent test settings
MAX_CONCURRENT_UPLOADS = 20
MAX_CONCURRENT_REQUESTS = 50

# File size limits for tests
MAX_TEST_FILE_SIZE_MB = 50
LARGE_FILE_SIZE_MB = 25

# Retry settings for flaky tests
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 1

# E2E test settings
E2E_HEADLESS = os.getenv("E2E_HEADLESS", "true").lower() == "true"
E2E_SLOW_MO = int(os.getenv("E2E_SLOW_MO", "0"))
E2E_TIMEOUT = int(os.getenv("E2E_TIMEOUT", "30000"))

# Database settings for integration tests
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///./test.db")

# Logging settings
TEST_LOG_LEVEL = os.getenv("TEST_LOG_LEVEL", "INFO")
CAPTURE_LOGS = os.getenv("CAPTURE_LOGS", "false").lower() == "true"

# Feature flags for tests
ENABLE_PERFORMANCE_TESTS = os.getenv("ENABLE_PERFORMANCE_TESTS", "true").lower() == "true"
ENABLE_STRESS_TESTS = os.getenv("ENABLE_STRESS_TESTS", "false").lower() == "true"
ENABLE_CONTRACT_TESTS = os.getenv("ENABLE_CONTRACT_TESTS", "true").lower() == "true"

# API settings
API_KEY = os.getenv("TEST_API_KEY", "test-api-key")
API_VERSION = "v1"

# Clean up settings
CLEANUP_AFTER_TESTS = os.getenv("CLEANUP_AFTER_TESTS", "true").lower() == "true"
PRESERVE_FAILED_TEST_DATA = os.getenv("PRESERVE_FAILED_TEST_DATA", "true").lower() == "true"