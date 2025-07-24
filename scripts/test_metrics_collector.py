#!/usr/bin/env python3
"""
Test Metrics Collector

Collects, analyzes, and tracks test metrics over time including:
- Test execution trends
- Coverage evolution
- Performance benchmarks
- Flaky test detection
- Test health scoring

Author: Dominic Fahey
License: MIT
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import argparse
import statistics
import sys

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress
    from rich.tree import Tree
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False
    print("Warning: Visualization libraries not available. Install with: uv pip install rich matplotlib")


class TestMetricsDatabase:
    """SQLite database for storing test metrics."""
    
    def __init__(self, db_path: Path = Path("artifacts/test_metrics.db")):
        self.db_path = db_path
        self.db_path.parent.mkdir(exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """Initialize the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS test_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    commit_hash TEXT,
                    branch TEXT,
                    total_tests INTEGER,
                    passed_tests INTEGER,
                    failed_tests INTEGER,
                    skipped_tests INTEGER,
                    execution_time REAL,
                    coverage_percentage REAL,
                    test_data TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS test_cases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER,
                    test_name TEXT NOT NULL,
                    test_class TEXT,
                    status TEXT NOT NULL,
                    execution_time REAL,
                    error_message TEXT,
                    FOREIGN KEY (run_id) REFERENCES test_runs (id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS coverage_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER,
                    file_path TEXT NOT NULL,
                    line_coverage REAL,
                    branch_coverage REAL,
                    missing_lines TEXT,
                    FOREIGN KEY (run_id) REFERENCES test_runs (id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS flaky_tests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_name TEXT NOT NULL UNIQUE,
                    failure_count INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    first_seen TEXT,
                    last_failure TEXT,
                    flaky_score REAL DEFAULT 0.0
                )
            """)
    
    def store_test_run(self, metrics: Dict[str, Any]) -> int:
        """Store a test run and return the run ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO test_runs (
                    timestamp, commit_hash, branch, total_tests, passed_tests,
                    failed_tests, skipped_tests, execution_time, coverage_percentage, test_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics['timestamp'],
                metrics.get('commit_hash'),
                metrics.get('branch'),
                metrics['total_tests'],
                metrics['passed_tests'],
                metrics['failed_tests'],
                metrics['skipped_tests'],
                metrics['execution_time'],
                metrics['coverage_percentage'],
                json.dumps(metrics)
            ))
            
            return cursor.lastrowid
    
    def store_test_cases(self, run_id: int, test_cases: List[Dict[str, Any]]):
        """Store individual test case results."""
        with sqlite3.connect(self.db_path) as conn:
            for test_case in test_cases:
                conn.execute("""
                    INSERT INTO test_cases (
                        run_id, test_name, test_class, status, execution_time, error_message
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    run_id,
                    test_case['name'],
                    test_case.get('classname'),
                    test_case['status'],
                    test_case.get('time', 0.0),
                    test_case.get('failure') or test_case.get('error')
                ))
    
    def update_flaky_tests(self, test_cases: List[Dict[str, Any]]):
        """Update flaky test tracking."""
        with sqlite3.connect(self.db_path) as conn:
            for test_case in test_cases:
                test_name = test_case['name']
                status = test_case['status']
                timestamp = datetime.now().isoformat()
                
                # Get current flaky test record
                cursor = conn.execute(
                    "SELECT failure_count, success_count FROM flaky_tests WHERE test_name = ?",
                    (test_name,)
                )
                row = cursor.fetchone()
                
                if row:
                    failure_count, success_count = row
                    if status in ['failed', 'error']:
                        failure_count += 1
                        conn.execute("""
                            UPDATE flaky_tests 
                            SET failure_count = ?, last_failure = ?,
                                flaky_score = CAST(failure_count AS REAL) / (failure_count + success_count)
                            WHERE test_name = ?
                        """, (failure_count, timestamp, test_name))
                    else:
                        success_count += 1
                        conn.execute("""
                            UPDATE flaky_tests 
                            SET success_count = ?,
                                flaky_score = CAST(failure_count AS REAL) / (failure_count + success_count)
                            WHERE test_name = ?
                        """, (success_count, test_name))
                else:
                    # New test
                    if status in ['failed', 'error']:
                        conn.execute("""
                            INSERT INTO flaky_tests (test_name, failure_count, success_count, first_seen, last_failure, flaky_score)
                            VALUES (?, 1, 0, ?, ?, 1.0)
                        """, (test_name, timestamp, timestamp))
                    else:
                        conn.execute("""
                            INSERT INTO flaky_tests (test_name, failure_count, success_count, first_seen, flaky_score)
                            VALUES (?, 0, 1, ?, 0.0)
                        """, (test_name, timestamp))
    
    def get_trend_data(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get test trend data for the specified number of days."""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM test_runs 
                WHERE timestamp > ? 
                ORDER BY timestamp
            """, (cutoff_date,))
            
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            return [dict(zip(columns, row)) for row in rows]
    
    def get_flaky_tests(self, min_flaky_score: float = 0.1) -> List[Dict[str, Any]]:
        """Get tests identified as flaky."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM flaky_tests 
                WHERE flaky_score >= ? AND (failure_count + success_count) >= 3
                ORDER BY flaky_score DESC
            """, (min_flaky_score,))
            
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            return [dict(zip(columns, row)) for row in rows]


class TestMetricsCollector:
    """Main metrics collection and analysis class."""
    
    def __init__(self, artifacts_dir: Path = Path("artifacts")):
        self.artifacts_dir = artifacts_dir
        self.db = TestMetricsDatabase()
        self.console = Console() if VISUALIZATION_AVAILABLE else None
    
    def collect_current_metrics(self) -> Dict[str, Any]:
        """Collect metrics from the current test run artifacts."""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'commit_hash': self.get_git_commit_hash(),
            'branch': self.get_git_branch()
        }
        
        # Load test results
        junit_results = self.load_junit_results()
        if junit_results:
            metrics.update({
                'total_tests': junit_results['total_tests'],
                'passed_tests': junit_results['total_tests'] - junit_results['failures'] - junit_results['errors'],
                'failed_tests': junit_results['failures'] + junit_results['errors'],
                'skipped_tests': junit_results['skipped'],
                'execution_time': junit_results['time'],
                'test_cases': junit_results.get('test_cases', [])
            })
        
        # Load coverage results
        coverage_results = self.load_coverage_results()
        if coverage_results:
            metrics['coverage_percentage'] = coverage_results.get('total_coverage', 0.0)
        
        return metrics
    
    def get_git_commit_hash(self) -> Optional[str]:
        """Get current git commit hash."""
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                capture_output=True,
                text=True,
                cwd=self.artifacts_dir.parent
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except Exception:
            return None
    
    def get_git_branch(self) -> Optional[str]:
        """Get current git branch."""
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                capture_output=True,
                text=True,
                cwd=self.artifacts_dir.parent
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except Exception:
            return None
    
    def load_junit_results(self) -> Optional[Dict[str, Any]]:
        """Load JUnit XML test results."""
        junit_file = self.artifacts_dir / "test-results" / "junit.xml"
        if not junit_file.exists():
            return None
        
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(junit_file)
            root = tree.getroot()
            
            test_cases = []
            for testcase in root.findall(".//testcase"):
                case_data = {
                    "name": testcase.get("name"),
                    "classname": testcase.get("classname"),
                    "time": float(testcase.get("time", 0.0)),
                    "status": "passed"
                }
                
                if testcase.find("failure") is not None:
                    case_data["status"] = "failed"
                    case_data["failure"] = testcase.find("failure").text
                elif testcase.find("error") is not None:
                    case_data["status"] = "error"
                    case_data["error"] = testcase.find("error").text
                elif testcase.find("skipped") is not None:
                    case_data["status"] = "skipped"
                
                test_cases.append(case_data)
            
            return {
                "total_tests": int(root.get("tests", 0)),
                "failures": int(root.get("failures", 0)),
                "errors": int(root.get("errors", 0)),
                "skipped": int(root.get("skipped", 0)),
                "time": float(root.get("time", 0.0)),
                "test_cases": test_cases
            }
        except Exception as e:
            print(f"Error loading JUnit results: {e}")
            return None
    
    def load_coverage_results(self) -> Optional[Dict[str, Any]]:
        """Load coverage data."""
        coverage_file = self.artifacts_dir / "coverage.json"
        if not coverage_file.exists():
            return None
        
        try:
            with open(coverage_file, 'r') as f:
                coverage_data = json.load(f)
            
            return {
                "total_coverage": coverage_data.get("totals", {}).get("percent_covered", 0),
                "files": coverage_data.get("files", {})
            }
        except Exception as e:
            print(f"Error loading coverage results: {e}")
            return None
    
    def store_metrics(self, metrics: Dict[str, Any]):
        """Store metrics in the database."""
        run_id = self.db.store_test_run(metrics)
        
        if 'test_cases' in metrics:
            self.db.store_test_cases(run_id, metrics['test_cases'])
            self.db.update_flaky_tests(metrics['test_cases'])
    
    def generate_trend_analysis(self, days: int = 30) -> Dict[str, Any]:
        """Generate trend analysis for the specified period."""
        trend_data = self.db.get_trend_data(days)
        
        if not trend_data:
            return {"error": "No historical data available"}
        
        # Calculate trends
        pass_rates = [
            (run['passed_tests'] / run['total_tests'] * 100) if run['total_tests'] > 0 else 0
            for run in trend_data
        ]
        
        coverage_rates = [run['coverage_percentage'] or 0 for run in trend_data]
        execution_times = [run['execution_time'] or 0 for run in trend_data]
        
        return {
            "period_days": days,
            "total_runs": len(trend_data),
            "pass_rate": {
                "current": pass_rates[-1] if pass_rates else 0,
                "average": statistics.mean(pass_rates) if pass_rates else 0,
                "trend": self.calculate_trend(pass_rates)
            },
            "coverage": {
                "current": coverage_rates[-1] if coverage_rates else 0,
                "average": statistics.mean(coverage_rates) if coverage_rates else 0,
                "trend": self.calculate_trend(coverage_rates)
            },
            "execution_time": {
                "current": execution_times[-1] if execution_times else 0,
                "average": statistics.mean(execution_times) if execution_times else 0,
                "trend": self.calculate_trend(execution_times, reverse=True)  # Lower is better
            },
            "stability_score": self.calculate_stability_score(trend_data)
        }
    
    def calculate_trend(self, values: List[float], reverse: bool = False) -> str:
        """Calculate trend direction from a list of values."""
        if len(values) < 2:
            return "stable"
        
        # Use linear regression slope
        n = len(values)
        x_values = list(range(n))
        
        x_mean = sum(x_values) / n
        y_mean = sum(values) / n
        
        numerator = sum((x_values[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return "stable"
        
        slope = numerator / denominator
        
        # Adjust for reverse trends (like execution time where lower is better)
        if reverse:
            slope = -slope
        
        if slope > 0.1:
            return "improving"
        elif slope < -0.1:
            return "declining"
        else:
            return "stable"
    
    def calculate_stability_score(self, trend_data: List[Dict[str, Any]]) -> float:
        """Calculate overall test suite stability score (0-100)."""
        if not trend_data:
            return 0.0
        
        # Factors contributing to stability score
        factors = []
        
        # Pass rate stability
        pass_rates = [
            (run['passed_tests'] / run['total_tests']) if run['total_tests'] > 0 else 0
            for run in trend_data
        ]
        if pass_rates:
            pass_rate_stability = 100 - (statistics.stdev(pass_rates) * 100) if len(pass_rates) > 1 else 100
            factors.append(pass_rate_stability)
        
        # Coverage stability
        coverage_rates = [run['coverage_percentage'] or 0 for run in trend_data]
        if coverage_rates:
            coverage_stability = 100 - statistics.stdev(coverage_rates) if len(coverage_rates) > 1 else 100
            factors.append(coverage_stability)
        
        # Flaky test penalty
        flaky_tests = self.db.get_flaky_tests()
        flaky_penalty = min(len(flaky_tests) * 5, 50)  # Max 50 point penalty
        
        base_score = statistics.mean(factors) if factors else 50
        final_score = max(0, base_score - flaky_penalty)
        
        return final_score
    
    def generate_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive test suite health report."""
        current_metrics = self.collect_current_metrics()
        trend_analysis = self.generate_trend_analysis(30)
        flaky_tests = self.db.get_flaky_tests()
        
        # Calculate health score
        health_factors = []
        
        # Pass rate factor (0-40 points)
        pass_rate = (current_metrics.get('passed_tests', 0) / 
                    max(current_metrics.get('total_tests', 1), 1)) * 100
        health_factors.append(min(pass_rate * 0.4, 40))
        
        # Coverage factor (0-30 points)
        coverage = current_metrics.get('coverage_percentage', 0)
        health_factors.append(min(coverage * 0.3, 30))
        
        # Stability factor (0-20 points)
        stability = trend_analysis.get('stability_score', 0) * 0.2
        health_factors.append(stability)
        
        # Speed factor (0-10 points)
        exec_time = current_metrics.get('execution_time', 0)
        speed_score = max(0, 10 - (exec_time / 60))  # Penalty for slow tests
        health_factors.append(speed_score)
        
        health_score = sum(health_factors)
        
        return {
            "health_score": health_score,
            "grade": self.get_health_grade(health_score),
            "current_metrics": current_metrics,
            "trend_analysis": trend_analysis,
            "flaky_tests": flaky_tests[:10],  # Top 10 flaky tests
            "recommendations": self.generate_recommendations(
                current_metrics, trend_analysis, flaky_tests
            )
        }
    
    def get_health_grade(self, score: float) -> str:
        """Convert health score to letter grade."""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"  
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
    
    def generate_recommendations(
        self, 
        current_metrics: Dict[str, Any],
        trend_analysis: Dict[str, Any],
        flaky_tests: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate actionable recommendations for test suite improvement."""
        recommendations = []
        
        # Pass rate recommendations
        pass_rate = (current_metrics.get('passed_tests', 0) / 
                    max(current_metrics.get('total_tests', 1), 1)) * 100
        if pass_rate < 95:
            recommendations.append(f"Improve test pass rate (currently {pass_rate:.1f}%)")
        
        # Coverage recommendations
        coverage = current_metrics.get('coverage_percentage', 0)
        if coverage < 80:
            recommendations.append(f"Increase test coverage (currently {coverage:.1f}%)")
        
        # Flaky test recommendations
        if flaky_tests:
            recommendations.append(f"Fix {len(flaky_tests)} flaky tests")
        
        # Performance recommendations
        exec_time = current_metrics.get('execution_time', 0)
        if exec_time > 300:  # 5 minutes
            recommendations.append("Optimize slow-running tests")
        
        # Trend-based recommendations
        if trend_analysis.get('pass_rate', {}).get('trend') == 'declining':
            recommendations.append("Investigate declining test pass rate trend")
        
        if trend_analysis.get('coverage', {}).get('trend') == 'declining':
            recommendations.append("Address declining coverage trend")
        
        return recommendations
    
    def print_health_report(self, report: Dict[str, Any]):
        """Print health report to console."""
        if not self.console:
            self.print_simple_health_report(report)
            return
        
        # Header
        grade = report['grade']
        score = report['health_score']
        grade_color = {
            'A': 'green', 'B': 'yellow', 'C': 'orange', 'D': 'red', 'F': 'red'
        }.get(grade, 'white')
        
        self.console.print(Panel.fit(
            f"[bold blue]Test Suite Health Report[/bold blue]\\n"
            f"Overall Grade: [{grade_color}]{grade}[/{grade_color}] ({score:.1f}/100)",
            border_style="blue"
        ))
        
        # Current metrics
        current = report['current_metrics']
        total_tests = current.get('total_tests', 0)
        passed_tests = current.get('passed_tests', 0)
        failed_tests = current.get('failed_tests', 0)
        
        metrics_table = Table(title="Current Test Run", show_header=True)
        metrics_table.add_column("Metric", style="cyan")
        metrics_table.add_column("Value", style="green")
        
        metrics_table.add_row("Total Tests", str(total_tests))
        metrics_table.add_row("Passed", f"{passed_tests} ({(passed_tests/max(total_tests,1)*100):.1f}%)")
        metrics_table.add_row("Failed", str(failed_tests))
        metrics_table.add_row("Coverage", f"{current.get('coverage_percentage', 0):.1f}%")
        metrics_table.add_row("Execution Time", f"{current.get('execution_time', 0):.1f}s")
        
        self.console.print(metrics_table)
        
        # Recommendations
        if report['recommendations']:
            self.console.print("\\n[bold yellow]Recommendations:[/bold yellow]")
            for i, rec in enumerate(report['recommendations'], 1):
                self.console.print(f"  {i}. {rec}")
        
        # Flaky tests
        if report['flaky_tests']:
            self.console.print("\\n[bold red]Top Flaky Tests:[/bold red]")
            for test in report['flaky_tests'][:5]:
                flaky_score = test['flaky_score'] * 100
                self.console.print(f"  • {test['test_name']} ({flaky_score:.1f}% failure rate)")
    
    def print_simple_health_report(self, report: Dict[str, Any]):
        """Print simple text health report."""
        print("\\n" + "="*60)
        print("TEST SUITE HEALTH REPORT")
        print("="*60)
        print(f"Overall Grade: {report['grade']} ({report['health_score']:.1f}/100)")
        
        current = report['current_metrics']
        print(f"Total Tests: {current.get('total_tests', 0)}")
        print(f"Passed: {current.get('passed_tests', 0)}")
        print(f"Failed: {current.get('failed_tests', 0)}")
        print(f"Coverage: {current.get('coverage_percentage', 0):.1f}%")
        
        if report['recommendations']:
            print("\\nRecommendations:")
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"  {i}. {rec}")
        
        print("="*60)
    
    def run_collection(self):
        """Run the complete metrics collection process."""
        metrics = self.collect_current_metrics()
        self.store_metrics(metrics)
        
        health_report = self.generate_health_report()
        self.print_health_report(health_report)
        
        # Save health report
        report_file = self.artifacts_dir / "test_health_report.json"
        with open(report_file, 'w') as f:
            json.dump(health_report, f, indent=2, default=str)
        
        print(f"\\nHealth report saved to: {report_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Collect and analyze test metrics")
    parser.add_argument("--artifacts-dir", type=Path, default=Path("artifacts"),
                       help="Directory containing test artifacts")
    parser.add_argument("--days", type=int, default=30,
                       help="Number of days for trend analysis")
    
    args = parser.parse_args()
    
    collector = TestMetricsCollector(args.artifacts_dir)
    collector.run_collection()


if __name__ == "__main__":
    main()