#!/bin/bash
# Script to run different test suites

set -e

echo "PDF Viewer Test Suite Runner"
echo "============================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to run a test suite
run_test_suite() {
    local suite_name=$1
    local command=$2
    
    echo -e "${YELLOW}Running $suite_name...${NC}"
    if eval "$command"; then
        echo -e "${GREEN}✓ $suite_name passed${NC}\n"
        return 0
    else
        echo -e "${RED}✗ $suite_name failed${NC}\n"
        return 1
    fi
}

# Check if specific test suite was requested
if [ "$1" = "unit" ]; then
    echo "Running unit tests only..."
    run_test_suite "Backend Unit Tests" "pytest tests/test_*.py -v"
    run_test_suite "Frontend Unit Tests" "cd frontend && npm test -- --run"
elif [ "$1" = "integration" ]; then
    echo "Running integration tests only..."
    # Download sample PDFs if needed
    python tests/integration/fixtures/download_samples.py
    run_test_suite "API Integration Tests" "pytest tests/integration/api/ -v"
elif [ "$1" = "e2e" ]; then
    echo "Running E2E tests only..."
    run_test_suite "E2E Tests" "npm run test:e2e"
elif [ "$1" = "coverage" ]; then
    echo "Running tests with coverage..."
    run_test_suite "Backend Coverage" "pytest --cov=backend.app --cov-report=html --cov-report=term"
    run_test_suite "Frontend Coverage" "cd frontend && npm run test:coverage"
else
    # Run all tests
    echo "Running all test suites..."
    echo ""
    
    # Download sample PDFs if needed
    echo -e "${YELLOW}Preparing test fixtures...${NC}"
    python tests/integration/fixtures/download_samples.py
    echo ""
    
    # Run each test suite
    failed=0
    
    if ! run_test_suite "Backend Unit Tests" "pytest tests/test_*.py -v --tb=short"; then
        ((failed++))
    fi
    
    if ! run_test_suite "Frontend Unit Tests" "cd frontend && npm test -- --run"; then
        ((failed++))
    fi
    
    if ! run_test_suite "API Integration Tests" "pytest tests/integration/api/ -v --tb=short"; then
        ((failed++))
    fi
    
    if ! run_test_suite "E2E Tests" "npm run test:e2e"; then
        ((failed++))
    fi
    
    # Summary
    echo "============================"
    if [ $failed -eq 0 ]; then
        echo -e "${GREEN}All tests passed!${NC}"
        exit 0
    else
        echo -e "${RED}$failed test suite(s) failed${NC}"
        exit 1
    fi
fi