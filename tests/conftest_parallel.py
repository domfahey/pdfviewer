"""
Parallel execution configuration and fixtures.

This module provides fixtures and configuration optimized for
pytest-xdist parallel execution with proper worker isolation.
"""

import os
import tempfile
import uuid
from pathlib import Path
from typing import Dict, Any

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app


@pytest.fixture(scope="session")
def worker_id(request):
    """Get the current worker ID for parallel execution."""
    if hasattr(request.config, "workerinput"):
        return request.config.workerinput["workerid"]
    return "master"


@pytest.fixture(scope="session")
def worker_temp_dir(worker_id):
    """Create worker-specific temporary directory."""
    base_temp = Path(tempfile.gettempdir())
    worker_temp = base_temp / f"pytest_worker_{worker_id}"
    worker_temp.mkdir(exist_ok=True)

    yield worker_temp

    # Cleanup worker temp directory
    import shutil

    if worker_temp.exists():
        shutil.rmtree(worker_temp, ignore_errors=True)


@pytest.fixture(scope="session")
def worker_uploads_dir(worker_temp_dir):
    """Create worker-specific uploads directory."""
    uploads_dir = worker_temp_dir / "uploads"
    uploads_dir.mkdir(exist_ok=True)

    # Set worker-specific upload directory
    original_upload_dir = os.environ.get("UPLOAD_DIR")
    os.environ["UPLOAD_DIR"] = str(uploads_dir)

    yield uploads_dir

    # Restore original upload directory
    if original_upload_dir:
        os.environ["UPLOAD_DIR"] = original_upload_dir
    else:
        os.environ.pop("UPLOAD_DIR", None)


@pytest.fixture(scope="session")
def worker_client(worker_uploads_dir):
    """Create worker-specific test client."""
    return TestClient(app)


@pytest.fixture(scope="session")
def parallel_safe_pdf_content():
    """PDF content safe for parallel execution."""
    return b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj  
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>
endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer
<< /Size 4 /Root 1 0 R >>
startxref
175
%%EOF"""


@pytest.fixture(scope="session")
def parallel_safe_file_factory(worker_temp_dir, parallel_safe_pdf_content):
    """Factory for creating worker-safe test files."""
    created_files = []

    def create_file(filename: str = None, content: bytes = None) -> Path:
        """Create a test file in worker-specific directory."""
        if filename is None:
            filename = f"test_{uuid.uuid4().hex}.pdf"
        if content is None:
            content = parallel_safe_pdf_content

        file_path = worker_temp_dir / filename
        file_path.write_bytes(content)
        created_files.append(file_path)
        return file_path

    yield create_file

    # Cleanup created files
    for file_path in created_files:
        if file_path.exists():
            file_path.unlink()


@pytest.fixture(scope="session")
def parallel_performance_tracker():
    """Track performance metrics per worker."""
    metrics = {}

    def record_metric(test_name: str, worker_id: str, metric_name: str, value: float):
        """Record performance metric for worker."""
        key = f"{worker_id}:{test_name}"
        if key not in metrics:
            metrics[key] = {}
        metrics[key][metric_name] = value

    def get_worker_metrics(worker_id: str) -> Dict[str, Any]:
        """Get metrics for specific worker."""
        return {k: v for k, v in metrics.items() if k.startswith(f"{worker_id}:")}

    def get_all_metrics() -> Dict[str, Any]:
        """Get all worker metrics."""
        return metrics

    tracker = type(
        "ParallelTracker",
        (),
        {
            "record": record_metric,
            "get_worker_metrics": get_worker_metrics,
            "get_all_metrics": get_all_metrics,
            "metrics": metrics,
        },
    )()

    yield tracker


@pytest.fixture(autouse=True)
def isolate_worker_state(worker_id, request):
    """Ensure proper isolation between workers."""
    # Add worker ID to test node for identification
    if hasattr(request.node, "add_marker"):
        request.node.add_marker(pytest.mark.worker(worker_id))

    # Clear any global state that might interfere
    # This is where you'd add any app-specific cleanup

    yield

    # Post-test cleanup for worker isolation
    pass


# Parallel execution utilities
class ParallelTestUtils:
    """Utilities for parallel test execution."""

    @staticmethod
    def is_parallel_execution(config=None):
        """Check if running in parallel mode.
        
        Args:
            config: pytest config object (pytestconfig or request.config)
            
        Returns:
            bool: True if running under pytest-xdist parallel execution
        """
        if config is None:
            # Fallback: try to detect without config by checking environment
            import os
            return os.environ.get("PYTEST_XDIST_WORKER") is not None
        
        # Check if xdist plugin is active and we have worker input
        return (
            config.pluginmanager.hasplugin("xdist") and 
            hasattr(config, "workerinput")
        )

    @staticmethod
    def skip_if_parallel(reason="Not compatible with parallel execution", config=None):
        """Skip test if running in parallel.
        
        Args:
            reason: Reason for skipping the test
            config: pytest config object (optional)
        """
        if ParallelTestUtils.is_parallel_execution(config):
            pytest.skip(reason)

    @staticmethod
    def require_serial_execution():
        """Mark test as requiring serial execution."""
        return pytest.mark.serial


@pytest.fixture(scope="session")
def parallel_utils():
    """Parallel execution utilities."""
    return ParallelTestUtils()
