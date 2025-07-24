#!/usr/bin/env python3
"""
Test Results Dashboard

Interactive web dashboard for analyzing test results, trends, and metrics.
Provides comprehensive visualization and analysis of test suite health.

Author: Dominic Fahey
License: MIT
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import argparse
import sys
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import socket

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.figure import Figure
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    import plotly.offline as pyo
    import pandas as pd
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False
    print("Warning: Plotting libraries not available. Install with: uv pip install matplotlib plotly pandas")


class TestDashboard:
    """Generate interactive test results dashboard."""
    
    def __init__(self, artifacts_dir: Path = Path("artifacts")):
        self.artifacts_dir = artifacts_dir
        self.db_path = artifacts_dir / "test_metrics.db"
        self.dashboard_dir = artifacts_dir / "dashboard"
        self.dashboard_dir.mkdir(exist_ok=True)
        
    def load_test_data(self, days: int = 30) -> Dict[str, Any]:
        """Load test data from database and artifacts."""
        data = {
            "historical_runs": [],
            "flaky_tests": [],
            "coverage_trends": [],
            "performance_data": [],
            "current_results": None
        }
        
        # Load from database if it exists
        if self.db_path.exists():
            with sqlite3.connect(self.db_path) as conn:
                # Historical test runs
                cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
                cursor = conn.execute("""
                    SELECT * FROM test_runs 
                    WHERE timestamp > ? 
                    ORDER BY timestamp
                """, (cutoff_date,))
                
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                data["historical_runs"] = [dict(zip(columns, row)) for row in rows]
                
                # Flaky tests
                cursor = conn.execute("""
                    SELECT * FROM flaky_tests 
                    WHERE flaky_score > 0.1 
                    ORDER BY flaky_score DESC
                    LIMIT 20
                """)
                
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                data["flaky_tests"] = [dict(zip(columns, row)) for row in rows]
        
        # Load current results
        current_summary = self.artifacts_dir / "ci_summary.json"
        if current_summary.exists():
            with open(current_summary, 'r') as f:
                data["current_results"] = json.load(f)
        
        return data
    
    def generate_trend_charts(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Generate trend charts and return file paths."""
        if not PLOTTING_AVAILABLE:
            return {}
        
        charts = {}
        historical_runs = data["historical_runs"]
        
        if not historical_runs:
            return charts
        
        # Convert to DataFrame for easier plotting
        df = pd.DataFrame(historical_runs)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['pass_rate'] = (df['passed_tests'] / df['total_tests'] * 100).fillna(0)
        
        # Pass Rate Trend
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Pass Rate Trend', 'Coverage Trend', 
                          'Execution Time Trend', 'Test Count Trend'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Pass rate
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'], 
                y=df['pass_rate'],
                mode='lines+markers',
                name='Pass Rate (%)',
                line=dict(color='green', width=2)
            ),
            row=1, col=1
        )
        
        # Coverage
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'], 
                y=df['coverage_percentage'].fillna(0),
                mode='lines+markers',
                name='Coverage (%)',
                line=dict(color='blue', width=2)
            ),
            row=1, col=2
        )
        
        # Execution time
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'], 
                y=df['execution_time'].fillna(0),
                mode='lines+markers',
                name='Execution Time (s)',
                line=dict(color='orange', width=2)
            ),
            row=2, col=1
        )
        
        # Test count
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'], 
                y=df['total_tests'],
                mode='lines+markers',
                name='Total Tests',
                line=dict(color='purple', width=2)
            ),
            row=2, col=2
        )
        
        fig.update_layout(
            height=600,
            title_text="Test Suite Trends",
            showlegend=False
        )
        
        trends_file = self.dashboard_dir / "trends.html"
        pyo.plot(fig, filename=str(trends_file), auto_open=False)
        charts["trends"] = "trends.html"
        
        # Flaky Tests Chart
        if data["flaky_tests"]:
            flaky_df = pd.DataFrame(data["flaky_tests"])
            
            fig_flaky = go.Figure(data=[
                go.Bar(
                    x=flaky_df['test_name'][:10],  # Top 10
                    y=flaky_df['flaky_score'] * 100,
                    marker_color='red',
                    text=[f"{score*100:.1f}%" for score in flaky_df['flaky_score'][:10]],
                    textposition='auto'
                )
            ])
            
            fig_flaky.update_layout(
                title="Top 10 Flaky Tests",
                xaxis_title="Test Name",
                yaxis_title="Failure Rate (%)",
                height=400
            )
            
            fig_flaky.update_xaxis(tickangle=45)
            
            flaky_file = self.dashboard_dir / "flaky_tests.html"
            pyo.plot(fig_flaky, filename=str(flaky_file), auto_open=False)
            charts["flaky_tests"] = "flaky_tests.html"
        
        return charts
    
    def generate_summary_stats(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics."""
        stats = {
            "total_runs": len(data["historical_runs"]),
            "avg_pass_rate": 0,
            "avg_coverage": 0,
            "avg_execution_time": 0,
            "total_flaky_tests": len(data["flaky_tests"]),
            "health_grade": "N/A"
        }
        
        if data["historical_runs"]:
            runs = data["historical_runs"]
            
            # Calculate averages
            pass_rates = []
            coverages = []
            exec_times = []
            
            for run in runs:
                if run["total_tests"] > 0:
                    pass_rate = (run["passed_tests"] / run["total_tests"]) * 100
                    pass_rates.append(pass_rate)
                
                if run["coverage_percentage"]:
                    coverages.append(run["coverage_percentage"])
                
                if run["execution_time"]:
                    exec_times.append(run["execution_time"])
            
            stats["avg_pass_rate"] = sum(pass_rates) / len(pass_rates) if pass_rates else 0
            stats["avg_coverage"] = sum(coverages) / len(coverages) if coverages else 0
            stats["avg_execution_time"] = sum(exec_times) / len(exec_times) if exec_times else 0
        
        # Calculate health grade
        health_score = 0
        if stats["avg_pass_rate"] >= 95:
            health_score += 40
        elif stats["avg_pass_rate"] >= 90:
            health_score += 30
        elif stats["avg_pass_rate"] >= 80:
            health_score += 20
        
        if stats["avg_coverage"] >= 90:
            health_score += 30
        elif stats["avg_coverage"] >= 80:
            health_score += 20
        elif stats["avg_coverage"] >= 70:
            health_score += 10
        
        if stats["total_flaky_tests"] == 0:
            health_score += 20
        elif stats["total_flaky_tests"] <= 5:
            health_score += 10
        
        if stats["avg_execution_time"] <= 60:
            health_score += 10
        elif stats["avg_execution_time"] <= 120:
            health_score += 5
        
        if health_score >= 90:
            stats["health_grade"] = "A"
        elif health_score >= 80:
            stats["health_grade"] = "B"
        elif health_score >= 70:
            stats["health_grade"] = "C"
        elif health_score >= 60:
            stats["health_grade"] = "D"
        else:
            stats["health_grade"] = "F"
        
        return stats
    
    def generate_html_dashboard(self, data: Dict[str, Any], charts: Dict[str, str], stats: Dict[str, Any]) -> str:
        """Generate main HTML dashboard."""
        
        current_results = data.get("current_results", {})
        current_env = current_results.get("environment", {})
        
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF Viewer Test Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}
        
        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            transition: transform 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        
        .stat-value {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        
        .stat-label {{
            color: #666;
            font-size: 1.1em;
        }}
        
        .grade-A {{ color: #28a745; }}
        .grade-B {{ color: #17a2b8; }}
        .grade-C {{ color: #ffc107; }}
        .grade-D {{ color: #fd7e14; }}
        .grade-F {{ color: #dc3545; }}
        
        .charts-section {{
            padding: 30px;
        }}
        
        .chart-container {{
            margin-bottom: 30px;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        }}
        
        .chart-title {{
            background: #343a40;
            color: white;
            padding: 15px 20px;
            font-size: 1.2em;
            font-weight: bold;
        }}
        
        .chart-content {{
            background: white;
            min-height: 400px;
        }}
        
        .info-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            padding: 30px;
            background: #f8f9fa;
        }}
        
        .info-card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        }}
        
        .info-card h3 {{
            color: #343a40;
            margin-bottom: 15px;
            font-size: 1.3em;
        }}
        
        .flaky-test {{
            padding: 10px;
            margin-bottom: 10px;
            background: #f8d7da;
            border-left: 4px solid #dc3545;
            border-radius: 5px;
        }}
        
        .flaky-test-name {{
            font-weight: bold;
            color: #721c24;
        }}
        
        .flaky-test-score {{
            color: #dc3545;
            font-size: 0.9em;
        }}
        
        .footer {{
            background: #343a40;
            color: white;
            text-align: center;
            padding: 20px;
        }}
        
        .refresh-btn {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: #007bff;
            color: white;
            border: none;
            padding: 15px 20px;
            border-radius: 50px;
            cursor: pointer;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            font-size: 1em;
            transition: all 0.3s ease;
        }}
        
        .refresh-btn:hover {{
            background: #0056b3;
            transform: scale(1.05);
        }}
        
        iframe {{
            width: 100%;
            height: 500px;
            border: none;
        }}
        
        @media (max-width: 768px) {{
            .info-grid {{
                grid-template-columns: 1fr;
            }}
            
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Test Dashboard</h1>
            <p>PDF Viewer Test Suite Analytics</p>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value grade-{stats['health_grade']}">{stats['health_grade']}</div>
                <div class="stat-label">Health Grade</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-value">{stats['avg_pass_rate']:.1f}%</div>
                <div class="stat-label">Average Pass Rate</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-value">{stats['avg_coverage']:.1f}%</div>
                <div class="stat-label">Average Coverage</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-value">{stats['avg_execution_time']:.1f}s</div>
                <div class="stat-label">Average Execution Time</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-value">{stats['total_runs']}</div>
                <div class="stat-label">Total Test Runs</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-value">{stats['total_flaky_tests']}</div>
                <div class="stat-label">Flaky Tests</div>
            </div>
        </div>
        
        <div class="charts-section">
            {'<div class="chart-container"><div class="chart-title">📈 Test Trends</div><div class="chart-content"><iframe src="trends.html"></iframe></div></div>' if 'trends' in charts else ''}
            
            {'<div class="chart-container"><div class="chart-title">🔥 Flaky Tests</div><div class="chart-content"><iframe src="flaky_tests.html"></iframe></div></div>' if 'flaky_tests' in charts else ''}
        </div>
        
        <div class="info-grid">
            <div class="info-card">
                <h3>🔧 Environment Info</h3>
                <p><strong>CI System:</strong> {current_env.get('ci_system', 'Unknown')}</p>
                <p><strong>Python Version:</strong> {current_env.get('python_version', 'Unknown')}</p>
                <p><strong>CPU Count:</strong> {current_env.get('cpu_count', 'Unknown')}</p>
                <p><strong>Memory:</strong> {current_env.get('memory_gb', 0):.1f} GB</p>
                <p><strong>Git Branch:</strong> {current_env.get('git_info', {}).get('branch', 'Unknown')}</p>
                <p><strong>Git Commit:</strong> {current_env.get('git_info', {}).get('commit_hash', 'Unknown')[:8] + '...' if current_env.get('git_info', {}).get('commit_hash') else 'Unknown'}</p>
            </div>
            
            <div class="info-card">
                <h3>⚠️ Top Flaky Tests</h3>
                {''.join([f'''
                <div class="flaky-test">
                    <div class="flaky-test-name">{test['test_name']}</div>
                    <div class="flaky-test-score">Failure Rate: {test['flaky_score']*100:.1f}%</div>
                </div>
                ''' for test in data['flaky_tests'][:5]]) if data['flaky_tests'] else '<p>No flaky tests detected! 🎉</p>'}
            </div>
        </div>
        
        <div class="footer">
            <p>© 2024 PDF Viewer Project | Test Dashboard v1.0</p>
            <p>Data retention: 30 days | Auto-refresh: Every test run</p>
        </div>
    </div>
    
    <button class="refresh-btn" onclick="location.reload()">🔄 Refresh</button>
    
    <script>
        // Auto-refresh every 5 minutes
        setTimeout(() => location.reload(), 300000);
        
        // Add some interactive effects
        document.querySelectorAll('.stat-card').forEach(card => {{
            card.addEventListener('click', () => {{
                card.style.transform = 'scale(0.95)';
                setTimeout(() => card.style.transform = '', 150);
            }});
        }});
    </script>
</body>
</html>
        """
        
        dashboard_file = self.dashboard_dir / "index.html"
        with open(dashboard_file, 'w') as f:
            f.write(html_template)
        
        return str(dashboard_file)
    
    def start_server(self, port: int = 8080) -> None:
        """Start a local web server to serve the dashboard."""
        
        class DashboardHandler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(self.dashboard_dir), **kwargs)
        
        # Find available port
        while port < 8090:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('localhost', port))
                break
            except OSError:
                port += 1
        
        server = HTTPServer(('localhost', port), DashboardHandler)
        
        print(f"📊 Test Dashboard running at: http://localhost:{port}")
        print("Press Ctrl+C to stop the server")
        
        # Open browser
        webbrowser.open(f"http://localhost:{port}")
        
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\\n🛑 Dashboard server stopped")
    
    def generate_dashboard(self, days: int = 30, serve: bool = False) -> str:
        """Generate the complete dashboard."""
        print("📊 Generating test dashboard...")
        
        # Load data
        data = self.load_test_data(days)
        print(f"   Loaded {len(data['historical_runs'])} historical runs")
        
        # Generate charts
        charts = self.generate_trend_charts(data)
        print(f"   Generated {len(charts)} charts")
        
        # Calculate stats
        stats = self.generate_summary_stats(data)
        print(f"   Health grade: {stats['health_grade']}")
        
        # Generate HTML
        dashboard_file = self.generate_html_dashboard(data, charts, stats)
        print(f"   Dashboard saved to: {dashboard_file}")
        
        if serve:
            self.start_server()
        
        return dashboard_file


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate interactive test dashboard")
    parser.add_argument("--artifacts-dir", type=Path, default=Path("artifacts"),
                       help="Directory containing test artifacts")
    parser.add_argument("--days", type=int, default=30,
                       help="Number of days of history to include")
    parser.add_argument("--serve", action="store_true",
                       help="Start web server to serve dashboard")
    parser.add_argument("--port", type=int, default=8080,
                       help="Port for web server")
    
    args = parser.parse_args()
    
    if not PLOTTING_AVAILABLE and not args.serve:
        print("Warning: Plotting libraries not available. Dashboard will have limited functionality.")
        print("Install with: uv pip install matplotlib plotly pandas")
    
    dashboard = TestDashboard(args.artifacts_dir)
    dashboard_file = dashboard.generate_dashboard(args.days, args.serve)
    
    if not args.serve:
        print(f"\\n✅ Dashboard generated successfully!")
        print(f"Open {dashboard_file} in your browser to view the dashboard.")


if __name__ == "__main__":
    main()