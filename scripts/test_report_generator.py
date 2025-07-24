#!/usr/bin/env python3
"""
Professional Test Report Generator

Generates comprehensive test reports including:
- Test execution summary
- Coverage analysis
- Performance metrics
- Test categorization breakdown
- Historical trend analysis
- CI/CD artifacts

Author: Dominic Fahey
License: MIT
"""

import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import argparse
import sys

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.tree import Tree
    from tabulate import tabulate
    from jinja2 import Template
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Warning: rich, tabulate, or jinja2 not available. Install with: uv pip install rich tabulate jinja2")


class TestReportGenerator:
    """Generate comprehensive test reports from pytest artifacts."""
    
    def __init__(self, artifacts_dir: Path = Path("artifacts")):
        self.artifacts_dir = artifacts_dir
        self.console = Console() if RICH_AVAILABLE else None
        self.report_data = {}
        
    def load_test_results(self) -> Dict[str, Any]:
        """Load test results from various artifact formats."""
        results = {
            "timestamp": datetime.now().isoformat(),
            "junit": self.load_junit_results(),
            "json": self.load_json_results(),
            "coverage": self.load_coverage_results(),
            "performance": self.load_performance_results()
        }
        
        # Calculate summary metrics
        results["summary"] = self.calculate_summary(results)
        return results
    
    def load_junit_results(self) -> Optional[Dict[str, Any]]:
        """Load JUnit XML test results."""
        junit_file = self.artifacts_dir / "test-results" / "junit.xml"
        if not junit_file.exists():
            return None
            
        try:
            tree = ET.parse(junit_file)
            root = tree.getroot()
            
            return {
                "total_tests": int(root.get("tests", 0)),
                "failures": int(root.get("failures", 0)),
                "errors": int(root.get("errors", 0)),
                "skipped": int(root.get("skipped", 0)),
                "time": float(root.get("time", 0.0)),
                "test_cases": self.parse_test_cases(root)
            }
        except Exception as e:
            print(f"Error loading JUnit results: {e}")
            return None
    
    def load_json_results(self) -> Optional[Dict[str, Any]]:
        """Load JSON test report."""
        json_file = self.artifacts_dir / "test-results" / "report.json"
        if not json_file.exists():
            return None
            
        try:
            with open(json_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading JSON results: {e}")
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
                "line_coverage": coverage_data.get("totals", {}).get("percent_covered_display", "0%"),
                "branch_coverage": coverage_data.get("totals", {}).get("percent_covered", 0),
                "files": coverage_data.get("files", {}),
                "missing_lines": self.calculate_missing_lines(coverage_data)
            }
        except Exception as e:
            print(f"Error loading coverage results: {e}")
            return None
    
    def load_performance_results(self) -> Dict[str, Any]:
        """Load performance and benchmark data."""
        # This would integrate with pytest-benchmark if available
        return {
            "slow_tests": [],
            "benchmarks": [],
            "memory_usage": {}
        }
    
    def parse_test_cases(self, root) -> List[Dict[str, Any]]:
        """Parse individual test cases from JUnit XML."""
        test_cases = []
        
        for testcase in root.findall(".//testcase"):
            case_data = {
                "name": testcase.get("name"),
                "classname": testcase.get("classname"),
                "time": float(testcase.get("time", 0.0)),
                "status": "passed"
            }
            
            # Check for failures, errors, or skips
            if testcase.find("failure") is not None:
                case_data["status"] = "failed"
                case_data["failure"] = testcase.find("failure").text
            elif testcase.find("error") is not None:
                case_data["status"] = "error"
                case_data["error"] = testcase.find("error").text
            elif testcase.find("skipped") is not None:
                case_data["status"] = "skipped"
                case_data["skip_reason"] = testcase.find("skipped").get("message", "")
            
            test_cases.append(case_data)
        
        return test_cases
    
    def calculate_missing_lines(self, coverage_data: Dict) -> Dict[str, List[int]]:
        """Calculate missing lines per file."""
        missing = {}
        for filename, file_data in coverage_data.get("files", {}).items():
            missing_lines = file_data.get("missing_lines", [])
            if missing_lines:
                missing[filename] = missing_lines
        return missing
    
    def calculate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate high-level summary metrics."""
        junit = results.get("junit", {})
        coverage = results.get("coverage", {})
        
        total_tests = junit.get("total_tests", 0)
        passed_tests = total_tests - junit.get("failures", 0) - junit.get("errors", 0)
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": junit.get("failures", 0) + junit.get("errors", 0),
            "skipped_tests": junit.get("skipped", 0),
            "pass_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "total_coverage": coverage.get("total_coverage", 0),
            "execution_time": junit.get("time", 0.0),
            "test_categories": self.categorize_tests(results)
        }
    
    def categorize_tests(self, results: Dict[str, Any]) -> Dict[str, int]:
        """Categorize tests by type based on naming conventions."""
        categories = {
            "unit": 0,
            "integration": 0,
            "api": 0,
            "performance": 0,
            "e2e": 0
        }
        
        test_cases = results.get("junit", {}).get("test_cases", [])
        for test_case in test_cases:
            name = test_case.get("name", "").lower()
            classname = test_case.get("classname", "").lower()
            
            if "integration" in name or "integration" in classname:
                categories["integration"] += 1
            elif "api" in name or "api" in classname:
                categories["api"] += 1
            elif "performance" in name or "benchmark" in name:
                categories["performance"] += 1
            elif "e2e" in name or "end_to_end" in name:
                categories["e2e"] += 1
            else:
                categories["unit"] += 1
        
        return categories
    
    def generate_console_report(self, results: Dict[str, Any]) -> None:
        """Generate a rich console report."""
        if not RICH_AVAILABLE or not self.console:
            self.generate_simple_report(results)
            return
        
        summary = results["summary"]
        
        # Header
        self.console.print(Panel.fit(
            f"[bold blue]PDF Viewer Test Report[/bold blue]\\n"
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            border_style="blue"
        ))
        
        # Summary table
        summary_table = Table(title="Test Execution Summary", show_header=True, header_style="bold magenta")
        summary_table.add_column("Metric", style="cyan", no_wrap=True)
        summary_table.add_column("Value", style="green")
        summary_table.add_column("Details", style="yellow")
        
        summary_table.add_row("Total Tests", str(summary["total_tests"]), "")
        summary_table.add_row("Passed", str(summary["passed_tests"]), f"✅ {summary['pass_rate']:.1f}%")
        summary_table.add_row("Failed", str(summary["failed_tests"]), "❌" if summary["failed_tests"] > 0 else "✅")
        summary_table.add_row("Skipped", str(summary["skipped_tests"]), "⏭️" if summary["skipped_tests"] > 0 else "")
        summary_table.add_row("Coverage", f"{summary['total_coverage']:.1f}%", 
                             "✅" if summary["total_coverage"] >= 80 else "⚠️")
        summary_table.add_row("Execution Time", f"{summary['execution_time']:.2f}s", "")
        
        self.console.print(summary_table)
        
        # Test categories
        if summary["test_categories"]:
            categories_table = Table(title="Test Categories", show_header=True, header_style="bold cyan")
            categories_table.add_column("Category", style="cyan")
            categories_table.add_column("Count", style="green")
            categories_table.add_column("Percentage", style="yellow")
            
            total_categorized = sum(summary["test_categories"].values())
            for category, count in summary["test_categories"].items():
                percentage = (count / total_categorized * 100) if total_categorized > 0 else 0
                categories_table.add_row(
                    category.title(),
                    str(count),
                    f"{percentage:.1f}%"
                )
            
            self.console.print(categories_table)
        
        # Coverage details
        if results.get("coverage"):
            self.print_coverage_details(results["coverage"])
    
    def print_coverage_details(self, coverage: Dict[str, Any]) -> None:
        """Print detailed coverage information."""
        if not self.console:
            return
            
        missing_lines = coverage.get("missing_lines", {})
        if missing_lines:
            self.console.print("\\n[bold red]Files with Missing Coverage:[/bold red]")
            
            for filename, lines in list(missing_lines.items())[:10]:  # Top 10
                self.console.print(f"  📄 {filename}: lines {', '.join(map(str, lines[:5]))}"
                                 f"{'...' if len(lines) > 5 else ''}")
    
    def generate_simple_report(self, results: Dict[str, Any]) -> None:
        """Generate a simple text report when rich is not available."""
        summary = results["summary"]
        
        print("\\n" + "="*60)
        print("PDF VIEWER TEST REPORT")
        print("="*60)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']} ({summary['pass_rate']:.1f}%)")
        print(f"Failed: {summary['failed_tests']}")
        print(f"Skipped: {summary['skipped_tests']}")
        print(f"Coverage: {summary['total_coverage']:.1f}%")
        print(f"Execution Time: {summary['execution_time']:.2f}s")
        print("="*60)
    
    def generate_html_report(self, results: Dict[str, Any], output_file: Path) -> None:
        """Generate a comprehensive HTML report."""
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>PDF Viewer Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                 color: white; padding: 20px; border-radius: 8px; margin-bottom: 30px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                  gap: 20px; margin-bottom: 30px; }
        .metric-card { background: #f8f9fa; padding: 20px; border-radius: 8px; 
                      border-left: 4px solid #007bff; }
        .metric-value { font-size: 2em; font-weight: bold; color: #007bff; }
        .table { width: 100%; border-collapse: collapse; margin-bottom: 30px; }
        .table th, .table td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        .table th { background-color: #f8f9fa; font-weight: bold; }
        .passed { color: #28a745; }
        .failed { color: #dc3545; }
        .skipped { color: #ffc107; }
        .coverage-high { color: #28a745; }
        .coverage-medium { color: #ffc107; }
        .coverage-low { color: #dc3545; }
    </style>
</head>
<body>
    <div class="header">
        <h1>PDF Viewer Test Report</h1>
        <p>Generated: {{ timestamp }}</p>
    </div>
    
    <div class="summary">
        <div class="metric-card">
            <div class="metric-value">{{ summary.total_tests }}</div>
            <div>Total Tests</div>
        </div>
        <div class="metric-card">
            <div class="metric-value passed">{{ summary.passed_tests }}</div>
            <div>Passed ({{ "%.1f"|format(summary.pass_rate) }}%)</div>
        </div>
        <div class="metric-card">
            <div class="metric-value failed">{{ summary.failed_tests }}</div>
            <div>Failed</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{{ "%.1f"|format(summary.total_coverage) }}%</div>
            <div>Coverage</div>
        </div>
    </div>
    
    {% if summary.test_categories %}
    <h2>Test Categories</h2>
    <table class="table">
        <thead>
            <tr><th>Category</th><th>Count</th><th>Percentage</th></tr>
        </thead>
        <tbody>
            {% for category, count in summary.test_categories.items() %}
            <tr>
                <td>{{ category.title() }}</td>
                <td>{{ count }}</td>
                <td>{{ "%.1f"|format((count / summary.total_tests * 100) if summary.total_tests > 0 else 0) }}%</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% endif %}
    
    {% if junit and junit.test_cases %}
    <h2>Test Results Details</h2>
    <table class="table">
        <thead>
            <tr><th>Test</th><th>Status</th><th>Time (s)</th><th>Details</th></tr>
        </thead>
        <tbody>
            {% for test in junit.test_cases[:50] %}
            <tr>
                <td>{{ test.name }}</td>
                <td class="{{ test.status }}">{{ test.status.title() }}</td>
                <td>{{ "%.3f"|format(test.time) }}</td>
                <td>
                    {% if test.failure %}{{ test.failure[:100] }}...{% endif %}
                    {% if test.error %}{{ test.error[:100] }}...{% endif %}
                    {% if test.skip_reason %}{{ test.skip_reason }}{% endif %}
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% endif %}
</body>
</html>
        """
        
        try:
            template = Template(html_template)
            html_content = template.render(**results)
            
            with open(output_file, 'w') as f:
                f.write(html_content)
                
            print(f"HTML report generated: {output_file}")
        except Exception as e:
            print(f"Error generating HTML report: {e}")
    
    def generate_ci_artifacts(self, results: Dict[str, Any]) -> None:
        """Generate CI/CD friendly artifacts."""
        # Generate badge data
        summary = results["summary"]
        badge_data = {
            "schemaVersion": 1,
            "label": "tests",
            "message": f"{summary['passed_tests']}/{summary['total_tests']} passed",
            "color": "green" if summary["pass_rate"] >= 90 else "orange" if summary["pass_rate"] >= 70 else "red"
        }
        
        badge_file = self.artifacts_dir / "test-badge.json"
        with open(badge_file, 'w') as f:
            json.dump(badge_data, f, indent=2)
        
        # Generate metrics file for trend analysis
        metrics_data = {
            "timestamp": results["timestamp"],
            "total_tests": summary["total_tests"],
            "passed_tests": summary["passed_tests"],
            "failed_tests": summary["failed_tests"],
            "pass_rate": summary["pass_rate"],
            "coverage": summary["total_coverage"],
            "execution_time": summary["execution_time"]
        }
        
        metrics_file = self.artifacts_dir / "test-metrics.json"
        with open(metrics_file, 'w') as f:
            json.dump(metrics_data, f, indent=2)
    
    def run(self, console: bool = True, html: bool = True, ci: bool = True) -> None:
        """Run the complete report generation process."""
        # Ensure artifacts directory exists
        self.artifacts_dir.mkdir(exist_ok=True)
        (self.artifacts_dir / "test-results").mkdir(exist_ok=True)
        (self.artifacts_dir / "test-logs").mkdir(exist_ok=True)
        
        # Load all test results
        results = self.load_test_results()
        
        # Generate reports
        if console:
            self.generate_console_report(results)
        
        if html:
            html_file = self.artifacts_dir / "test-results" / "comprehensive_report.html"
            self.generate_html_report(results, html_file)
        
        if ci:
            self.generate_ci_artifacts(results)
        
        # Save raw results for further analysis
        results_file = self.artifacts_dir / "test-results" / "complete_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate comprehensive test reports")
    parser.add_argument("--artifacts-dir", type=Path, default=Path("artifacts"),
                       help="Directory containing test artifacts")
    parser.add_argument("--no-console", action="store_true", help="Skip console output")
    parser.add_argument("--no-html", action="store_true", help="Skip HTML report")
    parser.add_argument("--no-ci", action="store_true", help="Skip CI artifacts")
    
    args = parser.parse_args()
    
    generator = TestReportGenerator(args.artifacts_dir)
    generator.run(
        console=not args.no_console,
        html=not args.no_html,
        ci=not args.no_ci
    )


if __name__ == "__main__":
    main()