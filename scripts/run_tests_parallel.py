#!/usr/bin/env python3
"""
Optimized test runner with parallel execution and performance monitoring.

This script runs tests with various optimization strategies and reports
performance improvements.
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional


class TestRunner:
    """Optimized test runner with performance monitoring."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.results = {}
    
    def run_tests(
        self,
        test_type: str = "all",
        parallel: bool = True,
        workers: Optional[int] = None,
        verbose: bool = True
    ) -> Dict[str, float]:
        """Run tests with specified configuration."""
        
        # Base pytest command
        cmd = ["python", "-m", "pytest"]
        
        # Add test path based on type
        if test_type == "unit":
            cmd.append("tests/unit")
            cmd.extend(["-m", "unit or not integration"])
        elif test_type == "integration":
            cmd.append("tests/integration")
            cmd.extend(["-m", "integration"])
        else:
            cmd.append("tests")
        
        # Parallel execution settings
        if parallel:
            if workers:
                cmd.extend(["-n", str(workers)])
            else:
                cmd.extend(["-n", "auto"])
            cmd.extend(["--dist", "worksteal"])
        
        # Performance optimizations
        cmd.extend([
            "--disable-warnings",
            "--tb=short",
            "--maxfail=10",
        ])
        
        if verbose:
            cmd.append("-v")
        else:
            cmd.append("-q")
        
        # Coverage settings (only for single-threaded to avoid conflicts)
        if not parallel:
            cmd.extend([
                "--cov=backend.app",
                "--cov-report=term-missing",
            ])
        
        print(f"Running: {' '.join(cmd)}")
        
        # Execute tests and measure time
        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            end_time = time.time()
            
            execution_time = end_time - start_time
            success = result.returncode == 0
            
            return {
                "execution_time": execution_time,
                "success": success,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": " ".join(cmd)
            }
            
        except subprocess.TimeoutExpired:
            return {
                "execution_time": 600.0,
                "success": False,
                "stdout": "",
                "stderr": "Test execution timed out",
                "command": " ".join(cmd)
            }
    
    def benchmark_configurations(self) -> Dict[str, Dict[str, float]]:
        """Benchmark different test configurations."""
        configurations = [
            {
                "name": "unit_tests_serial",
                "test_type": "unit",
                "parallel": False,
                "verbose": False
            },
            {
                "name": "unit_tests_parallel",
                "test_type": "unit", 
                "parallel": True,
                "workers": None,
                "verbose": False
            },
            {
                "name": "integration_tests_serial",
                "test_type": "integration",
                "parallel": False,
                "verbose": False
            },
            {
                "name": "integration_tests_parallel_2",
                "test_type": "integration",
                "parallel": True,
                "workers": 2,
                "verbose": False
            },
        ]
        
        results = {}
        
        for config in configurations:
            print(f"\n--- Running {config['name']} ---")
            
            result = self.run_tests(
                test_type=config["test_type"],
                parallel=config["parallel"],
                workers=config.get("workers"),
                verbose=config.get("verbose", False)
            )
            
            results[config["name"]] = result
            
            if result["success"]:
                print(f"✅ Completed in {result['execution_time']:.2f}s")
            else:
                print(f"❌ Failed after {result['execution_time']:.2f}s")
                if result["stderr"]:
                    print(f"Error: {result['stderr'][:200]}...")
        
        return results
    
    def generate_performance_report(self, results: Dict[str, Dict[str, float]]):
        """Generate performance comparison report."""
        print("\n" + "="*60)
        print("PERFORMANCE REPORT")
        print("="*60)
        
        # Sort by execution time
        sorted_results = sorted(
            results.items(),
            key=lambda x: x[1]["execution_time"]
        )
        
        print(f"{'Configuration':<30} {'Time (s)':<12} {'Status':<10}")
        print("-" * 55)
        
        for name, result in sorted_results:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"{name:<30} {result['execution_time']:<12.2f} {status:<10}")
        
        # Calculate improvements
        if len(sorted_results) >= 2:
            fastest = sorted_results[0]
            slowest = sorted_results[-1]
            
            if fastest[1]["success"] and slowest[1]["success"]:
                improvement = (
                    slowest[1]["execution_time"] - fastest[1]["execution_time"]
                ) / slowest[1]["execution_time"] * 100
                
                print(f"\n🚀 Best optimization: {fastest[0]}")
                print(f"⏱️  Performance improvement: {improvement:.1f}%")
                print(f"⚡ Time saved: {slowest[1]['execution_time'] - fastest[1]['execution_time']:.2f}s")
        
        # Identify failed configurations
        failed = [name for name, result in results.items() if not result["success"]]
        if failed:
            print(f"\n⚠️  Failed configurations: {', '.join(failed)}")
    
    def run_optimized_suite(self):
        """Run the full optimized test suite."""
        print("Starting optimized test suite...")
        
        # Run unit tests in parallel (fast)
        print("\n1. Running unit tests (parallel)...")
        unit_result = self.run_tests(
            test_type="unit",
            parallel=True,
            workers=None,
            verbose=True
        )
        
        if not unit_result["success"]:
            print("❌ Unit tests failed. Stopping.")
            return False
        
        print(f"✅ Unit tests completed in {unit_result['execution_time']:.2f}s")
        
        # Run integration tests with limited parallelism
        print("\n2. Running integration tests (limited parallel)...")
        integration_result = self.run_tests(
            test_type="integration",
            parallel=True,
            workers=2,  # Limited workers to avoid resource conflicts
            verbose=True
        )
        
        if not integration_result["success"]:
            print("❌ Integration tests failed.")
            return False
        
        print(f"✅ Integration tests completed in {integration_result['execution_time']:.2f}s")
        
        total_time = unit_result["execution_time"] + integration_result["execution_time"]
        print(f"\n🎉 Full test suite completed in {total_time:.2f}s")
        
        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Optimized test runner")
    parser.add_argument(
        "--mode",
        choices=["benchmark", "optimized", "unit", "integration"],
        default="optimized",
        help="Test execution mode"
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        default=True,
        help="Enable parallel execution"
    )
    parser.add_argument(
        "--workers",
        type=int,
        help="Number of parallel workers"
    )
    
    args = parser.parse_args()
    
    # Find project root
    project_root = Path(__file__).parent.parent
    runner = TestRunner(project_root)
    
    if args.mode == "benchmark":
        print("Running performance benchmark...")
        results = runner.benchmark_configurations()
        runner.generate_performance_report(results)
    
    elif args.mode == "optimized":
        success = runner.run_optimized_suite()
        sys.exit(0 if success else 1)
    
    else:
        result = runner.run_tests(
            test_type=args.mode,
            parallel=args.parallel,
            workers=args.workers
        )
        
        if result["success"]:
            print(f"✅ Tests completed in {result['execution_time']:.2f}s")
            sys.exit(0)
        else:
            print(f"❌ Tests failed after {result['execution_time']:.2f}s")
            print(result["stderr"])
            sys.exit(1)


if __name__ == "__main__":
    main()