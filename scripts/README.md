# Test System Scripts

This directory contains professional-grade testing scripts that provide comprehensive test execution, reporting, and analysis capabilities for the PDF Viewer project.

## 📁 Scripts Overview

### Core Testing Scripts

- **`ci_test_runner.py`** - CI/CD optimized test runner with smart parallelization and retry logic
- **`test_report_generator.py`** - Comprehensive test report generation (HTML, JSON, badges)
- **`test_metrics_collector.py`** - Test metrics collection and health scoring with trend analysis
- **`apply_test_markers.py`** - Automated test marker application based on file analysis
- **`test_dashboard.py`** - Interactive web dashboard for test analytics and visualization

## 🚀 Quick Start

### Run Tests in CI Mode
```bash
# Run full test suite with CI optimizations
python scripts/ci_test_runner.py --category full

# Run only smoke tests for quick feedback
python scripts/ci_test_runner.py --category smoke

# Run integration tests
python scripts/ci_test_runner.py --category integration
```

### Generate Test Reports
```bash
# Generate comprehensive HTML and JSON reports
python scripts/test_report_generator.py

# Generate reports from specific artifacts directory
python scripts/test_report_generator.py --artifacts-dir custom/path
```

### Collect and Analyze Metrics
```bash
# Collect current test metrics and generate health report
python scripts/test_metrics_collector.py

# Analyze trends over 60 days
python scripts/test_metrics_collector.py --days 60
```

### Launch Test Dashboard
```bash
# Generate and serve interactive dashboard
python scripts/test_dashboard.py --serve

# Generate dashboard for 90 days of history
python scripts/test_dashboard.py --days 90 --serve
```

### Apply Test Markers
```bash
# Analyze tests and suggest markers
python scripts/apply_test_markers.py tests/

# Apply markers automatically (dry run first)
python scripts/apply_test_markers.py tests/ --apply

# Actually apply markers (not dry run)
python scripts/apply_test_markers.py tests/ --apply --no-dry-run
```

## 📊 Test Configuration

### pytest.ini Configuration
The enhanced `pytest.ini` provides:
- **Comprehensive markers** for test categorization
- **Multi-format reporting** (HTML, XML, JSON)
- **Coverage integration** with branch coverage
- **Performance optimization** settings
- **CI/CD friendly** output formats

### Test Markers
The system includes professional test markers:

**Test Types:**
- `unit` - Fast, isolated unit tests
- `integration` - Component integration tests
- `api` - API endpoint tests
- `e2e` - End-to-end tests

**Performance:**
- `slow` - Tests taking >5 seconds
- `fast` - Tests taking <1 second
- `performance` - Performance benchmarks

**Features:**
- `pdf` - PDF processing tests
- `upload` - File upload tests
- `search` - Search functionality tests
- `viewer` - PDF viewer tests

**Environment:**
- `ci` - CI/CD environment tests
- `local` - Local development tests
- `docker` - Docker-specific tests

### Running Tests by Category
```bash
# Unit tests only
pytest -m unit

# Integration and API tests
pytest -m "integration or api"

# All tests except slow ones
pytest -m "not slow"

# Critical functionality only
pytest -m "critical"
```

## 📈 Reporting and Analytics

### Test Reports
The system generates multiple report formats:

1. **HTML Reports** (`artifacts/test-results/report.html`)
   - Interactive test results with filtering
   - Coverage integration
   - Execution time analysis

2. **JSON Reports** (`artifacts/test-results/report.json`)
   - Machine-readable test data
   - CI/CD integration friendly
   - Detailed test case information

3. **JUnit XML** (`artifacts/test-results/junit.xml`)
   - Standard CI/CD format
   - Jenkins/GitHub Actions compatible
   - Test case details and timing

4. **Coverage Reports** (`artifacts/htmlcov/index.html`)
   - Line and branch coverage
   - Missing coverage highlighting
   - File-by-file analysis

### Test Metrics Database
The system maintains a SQLite database (`artifacts/test_metrics.db`) tracking:
- Historical test runs
- Flaky test detection
- Performance trends
- Coverage evolution

### Health Scoring
Tests are assigned health scores (A-F) based on:
- **Pass Rate** (40 points) - Percentage of passing tests
- **Coverage** (30 points) - Code coverage percentage
- **Stability** (20 points) - Test result consistency
- **Performance** (10 points) - Execution speed

## 🔧 CI/CD Integration

### GitHub Actions
The provided workflow (`.github/workflows/test.yml`) includes:
- **Multi-OS testing** (Ubuntu, Windows, macOS)
- **Multi-Python version** support
- **Parallel test execution**
- **Artifact collection**
- **Badge generation**
- **PR comment integration**

### CI Test Categories
- **Smoke Tests** (2-5 minutes) - Critical functionality
- **Integration Tests** (10-15 minutes) - Component interactions
- **Full Test Suite** (20-30 minutes) - Complete validation
- **Performance Tests** - Benchmark tracking
- **Security Scans** - Safety and vulnerability checks

## 📱 Interactive Dashboard

The test dashboard provides:
- **Real-time metrics** - Current test status and trends
- **Interactive charts** - Plotly-powered visualizations
- **Flaky test tracking** - Identify unreliable tests
- **Health monitoring** - Overall test suite health
- **Historical analysis** - Trend identification

### Dashboard Features
- Responsive design for mobile/desktop
- Auto-refresh capabilities
- Drill-down analysis
- Export functionality
- CI/CD integration metrics

## 🛠️ Advanced Usage

### Custom Test Categories
Define custom test categories in CI runner config:
```json
{
  "test_categories": {
    "critical": ["unit", "critical"],
    "api_only": ["api"],
    "regression": ["regression", "critical"]
  }
}
```

### Parallel Test Execution
Automatic CPU-based parallelization:
```bash
# Auto-detect optimal workers
python scripts/ci_test_runner.py --category full

# Override worker count
pytest -n 4 tests/
```

### Custom Reporting
Generate reports with custom parameters:
```bash
# HTML only
python scripts/test_report_generator.py --no-ci --console

# Custom artifacts directory
python scripts/test_report_generator.py --artifacts-dir /tmp/test-results
```

## 📋 Maintenance

### Artifact Cleanup
Old artifacts are automatically cleaned up based on retention policies:
- Test results: 30 days
- Coverage reports: 30 days
- Performance data: 90 days
- Dashboard data: 90 days

### Database Maintenance
The metrics database includes automatic:
- Data pruning for old records
- Index optimization
- Flaky test score recalculation

## 🐛 Troubleshooting

### Common Issues

**Permission Errors:**
```bash
chmod +x scripts/*.py
```

**Missing Dependencies:**
```bash
uv pip install -e ".[dev]"
```

**Database Lock:**
```bash
rm artifacts/test_metrics.db
```

**Port Conflicts (Dashboard):**
```bash
python scripts/test_dashboard.py --serve --port 8081
```

### Debug Mode
Enable verbose logging:
```bash
pytest -v --tb=long --capture=no
```

## 📚 Dependencies

### Required Packages
- `pytest>=7.4.0` - Test framework
- `pytest-cov>=4.1.0` - Coverage integration
- `pytest-html>=3.1.0` - HTML reporting
- `pytest-json-report>=1.5.0` - JSON reporting
- `pytest-xdist>=3.0.0` - Parallel execution

### Optional Packages
- `rich>=13.7.0` - Enhanced console output
- `plotly>=5.0.0` - Interactive charts
- `matplotlib>=3.5.0` - Chart generation
- `pandas>=1.5.0` - Data analysis

## 🤝 Contributing

When adding new tests:
1. Use appropriate markers
2. Follow naming conventions
3. Include docstrings
4. Update test categories if needed
5. Run full test suite before committing

## 📄 License

MIT License - See project root for details.