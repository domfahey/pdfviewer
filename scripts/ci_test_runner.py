#!/usr/bin/env python3
"""
CI/CD Test Runner

Optimized test runner for continuous integration environments with:
- Smart test selection and parallelization
- Artifact generation for CI/CD pipelines
- Failure handling and retry logic
- Performance optimizations
- Docker and container support

Author: Dominic Fahey
License: MIT
"""

import os
import sys
import json
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
import argparse
from datetime import datetime
import tempfile


class CITestRunner:
    """CI/CD optimized test runner."""
    
    def __init__(self, 
                 test_dir: Path = Path("tests"),
                 artifacts_dir: Path = Path("artifacts"),
                 config_file: Optional[Path] = None):
        self.test_dir = test_dir
        self.artifacts_dir = artifacts_dir
        self.config_file = config_file
        self.config = self.load_config()
        
        # Ensure directories exist
        self.artifacts_dir.mkdir(exist_ok=True)
        (self.artifacts_dir / "test-results").mkdir(exist_ok=True)
        (self.artifacts_dir / "test-logs").mkdir(exist_ok=True)
        
    def load_config(self) -> Dict[str, Any]:
        """Load CI configuration."""
        default_config = {
            "parallel_workers": "auto",
            "max_workers": 4,
            "timeout": 300,
            "retry_failed": True,
            "max_retries": 2,
            "fast_fail": False,
            "coverage_threshold": 80,
            "artifacts_retention_days": 30,
            "test_categories": {
                "smoke": ["unit", "critical"],
                "integration": ["integration", "api"],
                "full": ["unit", "integration", "api", "e2e"]
            },
            "docker": {
                "enabled": False,
                "image": "python:3.11-slim",
                "volumes": []
            }
        }
        
        if self.config_file and self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                print(f"Warning: Could not load config file {self.config_file}: {e}")
        
        return default_config
    
    def detect_environment(self) -> Dict[str, Any]:
        """Detect CI/CD environment and capabilities."""
        env_info = {
            "ci_system": "unknown",
            "is_ci": bool(os.getenv("CI")),
            "is_docker": Path("/.dockerenv").exists(),
            "cpu_count": os.cpu_count() or 2,
            "memory_gb": self.get_memory_info(),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
            "git_info": self.get_git_info()
        }
        
        # Detect specific CI systems
        if os.getenv("GITHUB_ACTIONS"):
            env_info["ci_system"] = "github_actions"
            env_info["runner_os"] = os.getenv("RUNNER_OS", "unknown")
        elif os.getenv("GITLAB_CI"):
            env_info["ci_system"] = "gitlab_ci"
        elif os.getenv("JENKINS_URL"):
            env_info["ci_system"] = "jenkins"
        elif os.getenv("BUILDKITE"):
            env_info["ci_system"] = "buildkite"
        
        return env_info
    
    def get_memory_info(self) -> float:
        """Get available memory in GB."""
        try:
            if sys.platform == "linux":
                with open("/proc/meminfo", "r") as f:
                    for line in f:
                        if line.startswith("MemAvailable:"):
                            kb = int(line.split()[1])
                            return kb / 1024 / 1024  # Convert to GB
            return 4.0  # Default assumption
        except Exception:
            return 4.0
    
    def get_git_info(self) -> Dict[str, Optional[str]]:
        """Get git repository information."""
        git_info = {
            "commit_hash": None,
            "branch": None,
            "tag": None,
            "is_dirty": False
        }
        
        try:
            # Commit hash
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True, text=True, check=True
            )
            git_info["commit_hash"] = result.stdout.strip()
            
            # Branch
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True, text=True, check=True
            )
            git_info["branch"] = result.stdout.strip()
            
            # Check if dirty
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True, text=True, check=True
            )
            git_info["is_dirty"] = bool(result.stdout.strip())
            
        except subprocess.CalledProcessError:
            pass
        
        return git_info
    
    def optimize_test_execution(self, test_category: str = "full") -> Dict[str, Any]:
        """Optimize test execution based on environment and category."""
        env_info = self.detect_environment()
        
        # Calculate optimal worker count
        cpu_count = env_info["cpu_count"]
        memory_gb = env_info["memory_gb"]
        
        if self.config["parallel_workers"] == "auto":
            # Conservative parallelization in CI
            if env_info["is_ci"]:
                workers = min(cpu_count, self.config["max_workers"], int(memory_gb // 2))
                workers = max(1, workers)
            else:
                workers = min(cpu_count - 1, self.config["max_workers"])
                workers = max(1, workers)
        else:
            workers = int(self.config["parallel_workers"])
        
        # Select tests based on category
        test_markers = self.config["test_categories"].get(test_category, ["unit"])
        
        optimization = {
            "workers": workers,
            "test_markers": test_markers,
            "timeout": self.config["timeout"],
            "memory_limit": f"{int(memory_gb * 0.8)}g" if env_info["is_docker"] else None,
            "cache_dir": self.artifacts_dir / ".pytest_cache"
        }
        
        return optimization
    
    def build_pytest_command(self, 
                           test_category: str = "full",
                           extra_args: List[str] = None) -> List[str]:
        """Build optimized pytest command."""
        optimization = self.optimize_test_execution(test_category)
        
        cmd = ["python", "-m", "pytest"]
        
        # Test selection
        if optimization["test_markers"]:
            marker_expr = " or ".join(optimization["test_markers"])
            cmd.extend(["-m", marker_expr])
        
        # Parallelization
        if optimization["workers"] > 1:
            cmd.extend(["-n", str(optimization["workers"])])
            cmd.append("--maxprocesses=" + str(optimization["workers"]))
        
        # Output and reporting
        cmd.extend([
            "--tb=short",
            "--strict-markers",
            "--strict-config",
            "-v",
            "--durations=10",
            "--durations-min=1.0"
        ])
        
        # Coverage
        cmd.extend([
            "--cov=backend.app",
            "--cov-branch",
            "--cov-report=term-missing:skip-covered",
            "--cov-report=html:" + str(self.artifacts_dir / "htmlcov"),
            "--cov-report=xml:" + str(self.artifacts_dir / "coverage.xml"),
            "--cov-report=json:" + str(self.artifacts_dir / "coverage.json"),
            f"--cov-fail-under={self.config['coverage_threshold']}"
        ])
        
        # Test results
        cmd.extend([
            "--junitxml=" + str(self.artifacts_dir / "test-results" / "junit.xml"),
            "--html=" + str(self.artifacts_dir / "test-results" / "report.html"),
            "--self-contained-html"
        ])
        
        # JSON reporting
        cmd.extend([
            "--json-report",
            "--json-report-file=" + str(self.artifacts_dir / "test-results" / "report.json")
        ])
        
        # Timeout
        cmd.extend(["--timeout", str(optimization["timeout"])])
        
        # Cache
        cmd.append("--cache-dir=" + str(optimization["cache_dir"]))
        
        # Fast fail option
        if self.config["fast_fail"]:
            cmd.append("--maxfail=1")
        else:
            cmd.append("--maxfail=10")
        
        # Additional arguments
        if extra_args:
            cmd.extend(extra_args)
        
        # Test directory
        cmd.append(str(self.test_dir))
        
        return cmd
    
    def run_tests_with_retry(self, 
                           test_category: str = "full",
                           extra_args: List[str] = None) -> Dict[str, Any]:
        """Run tests with retry logic for failed tests."""
        results = {
            "attempts": [],
            "final_result": None,
            "total_time": 0.0,
            "retry_count": 0
        }
        
        start_time = datetime.now()
        
        # First attempt
        cmd = self.build_pytest_command(test_category, extra_args)
        result = self.execute_pytest(cmd, attempt=1)
        results["attempts"].append(result)
        
        # Retry failed tests if enabled
        if (self.config["retry_failed"] and 
            result["returncode"] != 0 and 
            self.config["max_retries"] > 0):
            
            # Get failed test names
            failed_tests = self.extract_failed_tests(result)
            
            for retry in range(1, self.config["max_retries"] + 1):
                if not failed_tests:
                    break
                
                print(f"\\n🔄 Retry attempt {retry} for {len(failed_tests)} failed tests")
                
                # Build retry command with only failed tests
                retry_cmd = self.build_pytest_command(test_category, extra_args)
                retry_cmd.extend(failed_tests)
                
                retry_result = self.execute_pytest(retry_cmd, attempt=retry + 1)
                results["attempts"].append(retry_result)
                results["retry_count"] = retry
                
                # Update failed tests list
                failed_tests = self.extract_failed_tests(retry_result)
                
                # If retry succeeded, break
                if retry_result["returncode"] == 0:
                    break
        
        # Set final result
        results["final_result"] = results["attempts"][-1]
        results["total_time"] = (datetime.now() - start_time).total_seconds()
        
        return results
    
    def execute_pytest(self, cmd: List[str], attempt: int = 1) -> Dict[str, Any]:
        """Execute pytest command and capture results."""
        print(f"\\n🧪 Running tests (attempt {attempt})")
        print(f"Command: {' '.join(cmd)}")
        
        start_time = datetime.now()
        
        # Create log file for this attempt
        log_file = (self.artifacts_dir / "test-logs" / 
                   f"pytest_attempt_{attempt}_{start_time.strftime('%Y%m%d_%H%M%S')}.log")
        
        try:
            with open(log_file, 'w') as log:
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=Path.cwd(),
                    timeout=self.config["timeout"] + 60  # Extra buffer
                )
                
                # Write output to log
                log.write(result.stdout)
                
                # Also print to console (for CI visibility)
                print(result.stdout)
        
        except subprocess.TimeoutExpired:
            result = subprocess.CompletedProcess(
                cmd, 124, stdout="Test execution timed out", stderr=""
            )
        except Exception as e:
            result = subprocess.CompletedProcess(
                cmd, 1, stdout=f"Test execution failed: {e}", stderr=""
            )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "attempt": attempt,
            "returncode": result.returncode,
            "execution_time": execution_time,
            "log_file": str(log_file),
            "timestamp": start_time.isoformat()
        }
    
    def extract_failed_tests(self, result: Dict[str, Any]) -> List[str]:
        """Extract failed test names from pytest output."""
        failed_tests = []
        
        # Try to read from JUnit XML first
        junit_file = self.artifacts_dir / "test-results" / "junit.xml"
        if junit_file.exists():
            try:
                import xml.etree.ElementTree as ET
                tree = ET.parse(junit_file)
                root = tree.getroot()
                
                for testcase in root.findall(".//testcase"):
                    if (testcase.find("failure") is not None or 
                        testcase.find("error") is not None):
                        
                        test_name = f"{testcase.get('classname')}::{testcase.get('name')}"
                        failed_tests.append(test_name)
                        
            except Exception as e:
                print(f"Could not parse JUnit XML: {e}")
        
        return failed_tests
    
    def generate_ci_artifacts(self, results: Dict[str, Any]):
        """Generate CI/CD specific artifacts."""
        env_info = self.detect_environment()
        
        # CI summary
        ci_summary = {
            "timestamp": datetime.now().isoformat(),
            "environment": env_info,
            "test_results": results,
            "artifacts_location": str(self.artifacts_dir),
            "success": results["final_result"]["returncode"] == 0
        }
        
        # Write CI summary
        summary_file = self.artifacts_dir / "ci_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(ci_summary, f, indent=2, default=str)
        
        # Generate status badges
        self.generate_status_badges(results)
        
        # Generate CI-specific outputs
        if env_info["ci_system"] == "github_actions":
            self.generate_github_outputs(results)
        elif env_info["ci_system"] == "gitlab_ci":
            self.generate_gitlab_outputs(results)
    
    def generate_status_badges(self, results: Dict[str, Any]):
        """Generate status badge data."""
        final_result = results["final_result"]
        success = final_result["returncode"] == 0
        
        # Test status badge
        test_badge = {
            "schemaVersion": 1,
            "label": "tests",
            "message": "passing" if success else "failing",
            "color": "green" if success else "red"
        }
        
        badge_file = self.artifacts_dir / "test_badge.json"
        with open(badge_file, 'w') as f:
            json.dump(test_badge, f, indent=2)
    
    def generate_github_outputs(self, results: Dict[str, Any]):
        """Generate GitHub Actions specific outputs."""
        if not os.getenv("GITHUB_OUTPUT"):
            return
        
        final_result = results["final_result"]
        success = final_result["returncode"] == 0
        
        outputs = [
            f"test-success={str(success).lower()}",
            f"test-time={final_result['execution_time']:.1f}",
            f"retry-count={results['retry_count']}"
        ]
        
        with open(os.getenv("GITHUB_OUTPUT"), 'a') as f:
            for output in outputs:
                f.write(f"{output}\\n")
    
    def generate_gitlab_outputs(self, results: Dict[str, Any]):
        """Generate GitLab CI specific outputs."""
        # GitLab uses artifacts and reports
        pass
    
    def cleanup_old_artifacts(self):
        """Clean up old test artifacts."""
        if not self.artifacts_dir.exists():
            return
        
        retention_days = self.config["artifacts_retention_days"]
        cutoff_time = datetime.now().timestamp() - (retention_days * 24 * 3600)
        
        for item in self.artifacts_dir.iterdir():
            if item.is_file() and item.stat().st_mtime < cutoff_time:
                item.unlink()
                print(f"Cleaned up old artifact: {item.name}")
    
    def run(self, 
            test_category: str = "full",
            extra_args: List[str] = None,
            cleanup: bool = True) -> int:
        """Run the complete CI test process."""
        print("🚀 Starting CI Test Runner")
        print(f"Test category: {test_category}")
        
        # Environment detection
        env_info = self.detect_environment()
        print(f"Environment: {env_info['ci_system']} (CI: {env_info['is_ci']})")
        print(f"Python: {env_info['python_version']}, CPUs: {env_info['cpu_count']}")
        
        # Cleanup old artifacts
        if cleanup:
            self.cleanup_old_artifacts()
        
        # Run tests
        results = self.run_tests_with_retry(test_category, extra_args)
        
        # Generate artifacts
        self.generate_ci_artifacts(results)
        
        # Final status
        success = results["final_result"]["returncode"] == 0
        total_time = results["total_time"]
        
        if success:
            print(f"\\n✅ All tests passed in {total_time:.1f}s")
            if results["retry_count"] > 0:
                print(f"   (after {results['retry_count']} retries)")
        else:
            print(f"\\n❌ Tests failed after {total_time:.1f}s")
            if results["retry_count"] > 0:
                print(f"   (with {results['retry_count']} retries)")
        
        return 0 if success else 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="CI/CD optimized test runner")
    parser.add_argument(
        "--category", 
        choices=["smoke", "integration", "full"],
        default="full",
        help="Test category to run"
    )
    parser.add_argument(
        "--test-dir",
        type=Path,
        default=Path("tests"),
        help="Test directory"
    )
    parser.add_argument(
        "--artifacts-dir",
        type=Path,
        default=Path("artifacts"),
        help="Artifacts directory"
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Configuration file"
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Skip cleanup of old artifacts"
    )
    parser.add_argument(
        "pytest_args",
        nargs="*",
        help="Additional arguments to pass to pytest"
    )
    
    args = parser.parse_args()
    
    runner = CITestRunner(
        test_dir=args.test_dir,
        artifacts_dir=args.artifacts_dir,
        config_file=args.config
    )
    
    exit_code = runner.run(
        test_category=args.category,
        extra_args=args.pytest_args,
        cleanup=not args.no_cleanup
    )
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()