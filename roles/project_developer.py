import os
import copy
import json
import time
import re
from datetime import datetime

from core import interface
from utils import construct_system_message, code_truncate
from tools import global_tool_orchestrator
from .enhanced_role import EnhancedRole


class ProjectDeveloper(EnhancedRole):
    def __init__(self, team_description, developer_description, requirement, project_type,
                 model='gpt-3.5-turbo', majority=1, max_tokens=1024, temperature=0.2, top_p=0.95):
        # Initialize base class
        super().__init__()
        
        self.model = model
        self.majority = majority
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.history_message = []
        self.requirement = requirement
        self.project_type = project_type
        self.feedback_history = []
        
        # Add tool orchestrator reference
        self.tool_orchestrator = global_tool_orchestrator

        self.itf = interface.ProgramInterface(
            stop='',
            verbose=False,
            model=self.model,
        )

        system_message = construct_system_message(requirement, developer_description, team_description)
        self.history_message_append(system_message)

    def implement_enhanced_project(self, architecture_plan, ui_design=None, visualization_plan=None, 
                                  code_templates=None, existing_files=None, is_initial=True):
        """Enhanced implementation with advanced HTML structure and modern web standards"""
        
        if is_initial:
            implementation_prompt = f"""
            Based on the following comprehensive plans, implement a state-of-the-art {self.project_type} project.
            
            Architecture Plan: {architecture_plan}
            UI Design Guidelines: {ui_design}
            Visualization Specifications: {visualization_plan}
            Code Templates: {list(code_templates.keys()) if code_templates else "None"}
            
            Project Requirements: {self.requirement}
            
            Please provide a complete implementation with modern web standards. Use this format:
            
            === FILENAME: path/to/file.ext ===
            [file content here]
            === END FILE ===
            
            CRITICAL REQUIREMENTS - Modern HTML Structure:
            
            1. **HTML5 Structure & Semantics**:
               - Use semantic HTML5 elements (header, nav, main, section, article, aside, footer)
               - Include proper meta tags for SEO and mobile optimization
               - Add Open Graph and Twitter Card meta tags
               - Include structured data (JSON-LD) for rich snippets
               - Use proper heading hierarchy (h1-h6)
               - Add ARIA labels and roles for accessibility
               - Include lang attribute and proper character encoding
            
            2. **Advanced CSS Architecture**:
               - Use CSS Custom Properties (CSS Variables) for theming
               - Implement CSS Grid and Flexbox for layout
               - Add smooth animations and transitions using CSS
               - Use modern CSS features (clamp(), min(), max(), aspect-ratio)
               - Implement mobile-first responsive design
               - Add dark/light theme support with CSS variables
               - Use CSS logical properties for internationalization
               - Include print styles and reduced motion preferences
            
            3. **Modern JavaScript Features**:
               - Use ES6+ features (modules, async/await, destructuring, arrow functions)
               - Implement proper error handling with try-catch blocks
               - Add Web APIs integration (Intersection Observer, ResizeObserver)
               - Use modern DOM methods (querySelector, addEventListener)
               - Implement Progressive Web App features (Service Worker, Web App Manifest)
               - Add Web Components where appropriate
               - Use modern build tools and bundling strategies
            
            4. **Performance & Optimization**:
               - Implement lazy loading for images and content
               - Add resource hints (preload, prefetch, preconnect)
               - Use modern image formats (WebP, AVIF) with fallbacks
               - Implement critical CSS inline loading
               - Add compression and minification
               - Use efficient data structures and algorithms
               - Implement virtual scrolling for large datasets
            
            5. **Accessibility (WCAG 2.1 AA)**:
               - Add proper ARIA labels, roles, and properties
               - Implement keyboard navigation for all interactive elements
               - Ensure sufficient color contrast ratios
               - Add focus management and skip links
               - Include alternative text for images and visualizations
               - Support screen readers with proper semantic markup
               - Add high contrast mode support
            
            6. **Advanced Visualization Features**:
               - Support multiple chart libraries (Chart.js, D3.js, Plotly)
               - Implement real-time data updates with WebSockets
               - Add interactive features (zoom, pan, brush, filter)
               - Create responsive charts that adapt to container size
               - Add export functionality (PNG, PDF, SVG, CSV)
               - Implement cross-chart interactions and filtering
               - Add animation and transition effects
            
            7. **Modern Web Standards**:
               - Use fetch API instead of XMLHttpRequest
               - Implement proper CSP (Content Security Policy) headers
               - Add integrity checks for external resources
               - Use modern authentication methods
               - Implement proper error boundaries and fallbacks
               - Add comprehensive logging and analytics
            
            **File Structure Requirements**:
            - index.html: Main HTML file with semantic structure
            - css/main.css: Primary stylesheet with CSS Grid/Flexbox
            - css/components.css: Component-specific styles
            - css/utilities.css: Utility classes and helpers
            - js/main.js: Core application logic
            - js/visualization.js: Visualization-specific code
            - js/utils.js: Utility functions and helpers
            - js/data.js: Data management and API integration
            - assets/: Images, icons, and other static assets
            - manifest.json: Web App Manifest for PWA support
            
            Create a professional, production-ready application that showcases modern web development best practices.
            """
        else:
            # Simple iterative improvement
            feedback_text = self.feedback_history[-1] if self.feedback_history else "No specific feedback"
            implementation_prompt = f"""
            Fix the issues in the existing project:
            
            Issues to fix: {feedback_text}
            
            Current files: {list(existing_files.keys()) if existing_files else "None"}
            
            Please update ONLY the files that need changes to fix these issues.
            Use the same file format:
            === FILENAME: path/to/file.ext ===
            [updated file content here]
            === END FILE ===
            
            Focus on making the minimal necessary changes to address the feedback.
            """
        
        self.history_message_append(implementation_prompt)
        
        try:
            responses = self.itf.run(prompt=self.history_message, majority_at=self.majority,
                                   max_tokens=self.max_tokens, temperature=self.temperature, top_p=self.top_p)
        except Exception as e:
            print(f"Enhanced project implementation failed: {e}")
            time.sleep(5)
            return "error"

        implementation = responses[0]
        self.history_message_append(implementation, "assistant")
        
        # Parse the implementation into separate files
        project_files = self._parse_implementation(implementation)
        
        # If parsing failed, create enhanced fallback files
        if not project_files:
            project_files = self._create_enhanced_fallback_files(implementation)
        
        return project_files

    def implement_project(self, architecture_plan, ui_design=None, existing_files=None, is_initial=True):
        """Implement the complete project based on architecture plan with tool assistance"""
        
        # Use tools to enhance the implementation process
        print("🔧 Using tools to enhance implementation...")
        
        # Get external resources suggestions from tools
        if self.project_type == 'web_visualization':
            api_tool = self.tool_orchestrator.get_tool("api_integration")
            if api_tool:
                cdn_resources = api_tool.execute("fetch_cdn_libraries", 
                                               libraries=["chart.js", "d3.js", "bootstrap"])
                color_palette = api_tool.execute("fetch_color_palette", theme="modern")
                print(f"🎨 Enhanced with external resources and color palette")
        
        if is_initial:
            implementation_prompt = f"""
            Based on the following architecture plan, implement a complete {self.project_type} project.
            
            Architecture Plan: {architecture_plan}
            
            {f"UI Design Guidelines: {ui_design}" if ui_design else ""}
            
            Please provide the complete implementation with multiple files. 
            For each file, use the following format:
            
            === FILENAME: path/to/file.ext ===
            [file content here]
            === END FILE ===
            
            Requirements:
            1. Create a fully functional {self.project_type} application
            2. For web visualization projects, include interactive charts and modern UI
            3. Use modern web technologies (HTML5, CSS3, ES6+)
            4. Implement responsive design with CSS Grid and Flexbox
            5. Add sample data for demonstrations
            6. Include error handling and user feedback
            7. Make the interface beautiful and user-friendly
            8. Use modern color schemes and typography
            9. Implement accessibility features (ARIA labels, keyboard navigation)
            10. Add loading states and smooth transitions
            
            Focus on creating a complete, working application that demonstrates the requested functionality.
            Use modern development practices and ensure cross-browser compatibility.
            """
        else:
            # Use code analyzer to analyze existing files before improvement
            code_analyzer = self.tool_orchestrator.get_tool("code_analyzer")
            analysis_results = []
            if code_analyzer and existing_files:
                for filename, content in existing_files.items():
                    file_ext = filename.split('.')[-1] if '.' in filename else 'text'
                    analysis = code_analyzer.execute(code=content, 
                                                   language=file_ext)
                    analysis_results.append(f"{filename}: {analysis.get('summary', 'analyzed')}")
            
            # Iterative improvement 
            feedback_text = self.feedback_history[-1] if self.feedback_history else "No specific feedback"
            analysis_text = "\n".join(analysis_results) if analysis_results else "No analysis available"
            
            implementation_prompt = f"""
            Fix the issues in the existing project:
            
            Issues to fix: {feedback_text}
            
            Current files: {list(existing_files.keys()) if existing_files else "None"}
            
            Please update ONLY the files that need changes to fix these issues:
            === FILENAME: path/to/file.ext ===
            [updated file content here]
            === END FILE ===
            
            Make minimal changes to fix the specific issues mentioned.
            """
        
        self.history_message_append(implementation_prompt)
        
        try:
            responses = self.itf.run(prompt=self.history_message, majority_at=self.majority,
                                   max_tokens=self.max_tokens, temperature=self.temperature, top_p=self.top_p)
        except Exception as e:
            print(f"Project implementation failed: {e}")
            time.sleep(5)
            return "error"

        implementation = responses[0]
        self.history_message_append(implementation, "assistant")
        
        # Parse the implementation into separate files
        project_files = self._parse_implementation(implementation)
        
        # Use quality checker to validate the generated files
        quality_checker = self.tool_orchestrator.get_tool("quality_checker")
        if quality_checker and project_files:
            quality_report = quality_checker.execute("check_quality", 
                                                    files=project_files,
                                                    project_type=self.project_type)
            print(f"✅ Quality check completed. Score: {quality_report.get('overall_score', 'N/A')}")
        
        return project_files

    def _create_enhanced_fallback_files(self, implementation):
        """Create enhanced fallback files based on project type"""
        if self.project_type == 'python_project':
            return self._create_python_fallback_files(implementation)
        else:
            return self._create_web_fallback_files(implementation)
    
    def _create_python_fallback_files(self, implementation):
        """Create fallback files for Python projects"""
        project_files = {}
        
        # Main application entry point
        project_files['main.py'] = '''#!/usr/bin/env python3
"""
Data Analysis Toolkit - Main Application
"""

import argparse
import sys
from data_analysis_toolkit import CSVReader, Statistics, Visualization

def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(description='Data Analysis Toolkit')
    parser.add_argument('--file', '-f', required=True, help='CSV file to analyze')
    parser.add_argument('--operation', '-o', choices=['stats', 'plot'], 
                       default='stats', help='Operation to perform')
    
    args = parser.parse_args()
    
    try:
        # Read CSV data
        reader = CSVReader()
        data = reader.read_csv(args.file)
        
        if args.operation == 'stats':
            # Perform statistical analysis
            stats = Statistics(data)
            print(f"Mean: {stats.mean()}")
            print(f"Median: {stats.median()}")
        
        elif args.operation == 'plot':
            # Create visualization
            viz = Visualization(data)
            viz.create_histogram()
            print("Histogram saved as histogram.png")
    
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''
        
        # Requirements file
        project_files['requirements.txt'] = '''pandas>=1.3.0
numpy>=1.20.0
matplotlib>=3.4.0
seaborn>=0.11.0
pytest>=6.0.0
'''
        
        # Package init
        project_files['data_analysis_toolkit/__init__.py'] = '''"""
Data Analysis Toolkit
"""
from .csv_reader import CSVReader
from .statistics import Statistics  
from .visualization import Visualization

__version__ = "1.0.0"
'''
        
        # Simple CSV reader
        project_files['data_analysis_toolkit/csv_reader.py'] = '''import pandas as pd

class CSVReader:
    def __init__(self):
        self.data = None
    
    def read_csv(self, file_path):
        """Read CSV file and return DataFrame"""
        self.data = pd.read_csv(file_path)
        return self.data
'''
        
        # Simple statistics
        project_files['data_analysis_toolkit/statistics.py'] = '''import pandas as pd
import numpy as np

class Statistics:
    def __init__(self, data):
        self.data = data
        self.numeric_cols = data.select_dtypes(include=[np.number]).columns
    
    def mean(self):
        return self.data[self.numeric_cols].mean()
    
    def median(self):
        return self.data[self.numeric_cols].median()
'''
        
        # Simple visualization
        project_files['data_analysis_toolkit/visualization.py'] = '''import matplotlib.pyplot as plt

class Visualization:
    def __init__(self, data):
        self.data = data
    
    def create_histogram(self):
        """Create histogram for numeric columns"""
        numeric_data = self.data.select_dtypes(include=['number'])
        for column in numeric_data.columns:
            plt.figure()
            plt.hist(numeric_data[column].dropna(), bins=20)
            plt.title(f'Histogram of {column}')
            plt.savefig(f'{column}_histogram.png')
            plt.close()
'''
        
        # README
        project_files['README.md'] = '''# Data Analysis Toolkit

A Python toolkit for CSV data analysis and visualization.

## Usage

```bash
python main.py --file data.csv --operation stats
python main.py --file data.csv --operation plot
```

## Installation

```bash
pip install -r requirements.txt
```
'''
        
        return project_files
    
    def _create_web_fallback_files(self, implementation):
        """Create enhanced fallback files with modern HTML structure and advanced CSS"""
        project_files = {}
        
        # Enhanced HTML file with semantic structure
        project_files['index.html'] = f'''<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Advanced {self.project_type.replace('_', ' ').title()} - Modern Web Application">
    <meta name="keywords" content="visualization, dashboard, data, interactive, modern, responsive">
    <meta name="author" content="Self-Collaboration Code Generation">
    
    <!-- Open Graph Meta Tags -->
    <meta property="og:title" content="{self.project_type.replace('_', ' ').title()} Application">
    <meta property="og:description" content="Advanced interactive web application with modern visualizations">
    <meta property="og:type" content="website">
    <meta property="og:image" content="/assets/og-image.jpg">
    
    <!-- Twitter Card Meta Tags -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{self.project_type.replace('_', ' ').title()} Application">
    <meta name="twitter:description" content="Advanced interactive web application">
    
    <title>Enhanced {self.project_type.replace('_', ' ').title()}</title>
    
    <!-- Preconnect to external resources -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://cdn.jsdelivr.net">
    
    <!-- Stylesheets -->
    <link rel="stylesheet" href="css/main.css">
    <link rel="stylesheet" href="css/components.css">
    <link rel="stylesheet" href="css/utilities.css">
    
    <!-- Web App Manifest -->
    <link rel="manifest" href="manifest.json">
    
    <!-- Favicon -->
    <link rel="icon" type="image/x-icon" href="/assets/favicon.ico">
    
    <!-- Theme Color -->
    <meta name="theme-color" content="#007bff">
</head>
<body>
    <!-- Skip to main content for accessibility -->
    <a href="#main-content" class="skip-link">Skip to main content</a>
    
    <!-- Header -->
    <header class="app-header" role="banner">
        <nav class="navbar" role="navigation" aria-label="Main navigation">
            <div class="navbar-brand">
                <h1 class="app-title">Enhanced {self.project_type.replace('_', ' ').title()}</h1>
            </div>
            <div class="navbar-controls">
                <button id="theme-toggle" class="btn btn-icon" aria-label="Toggle dark/light theme">
                    <span class="theme-icon">🌙</span>
                </button>
                <button id="fullscreen-toggle" class="btn btn-icon" aria-label="Toggle fullscreen">
                    <span class="fullscreen-icon">⛶</span>
                </button>
            </div>
        </nav>
    </header>
    
    <!-- Main Content -->
    <main id="main-content" class="app-main" role="main">
        <!-- Dashboard Grid -->
        <div class="dashboard-grid">
            <!-- KPI Cards Section -->
            <section class="kpi-section" aria-labelledby="kpi-heading">
                <h2 id="kpi-heading" class="section-title">Key Performance Indicators</h2>
                <div class="kpi-grid">
                    <div class="kpi-card" role="region" aria-labelledby="kpi-1">
                        <h3 id="kpi-1" class="kpi-title">Total Users</h3>
                        <div class="kpi-value" aria-live="polite">12,345</div>
                        <div class="kpi-trend positive">+5.2%</div>
                    </div>
                    <div class="kpi-card" role="region" aria-labelledby="kpi-2">
                        <h3 id="kpi-2" class="kpi-title">Revenue</h3>
                        <div class="kpi-value" aria-live="polite">$98,765</div>
                        <div class="kpi-trend positive">+12.8%</div>
                    </div>
                    <div class="kpi-card" role="region" aria-labelledby="kpi-3">
                        <h3 id="kpi-3" class="kpi-title">Conversion</h3>
                        <div class="kpi-value" aria-live="polite">3.45%</div>
                        <div class="kpi-trend negative">-1.2%</div>
                    </div>
                </div>
            </section>
            
            <!-- Visualization Section -->
            <section class="visualization-section" aria-labelledby="viz-heading">
                <h2 id="viz-heading" class="section-title">Data Visualizations</h2>
                <div class="chart-grid">
                    <div class="chart-container" role="img" aria-labelledby="chart-1-title">
                        <h3 id="chart-1-title" class="chart-title">Monthly Trends</h3>
                        <canvas id="chart-1" aria-label="Monthly trends line chart showing data over time"></canvas>
                        <div class="chart-loading" aria-hidden="true">Loading chart...</div>
                    </div>
                    <div class="chart-container" role="img" aria-labelledby="chart-2-title">
                        <h3 id="chart-2-title" class="chart-title">Category Distribution</h3>
                        <canvas id="chart-2" aria-label="Pie chart showing category distribution"></canvas>
                        <div class="chart-loading" aria-hidden="true">Loading chart...</div>
                    </div>
                </div>
            </section>
            
            <!-- Controls Section -->
            <aside class="controls-section" role="complementary" aria-labelledby="controls-heading">
                <h2 id="controls-heading" class="section-title">Filters & Controls</h2>
                <div class="control-group">
                    <label for="date-range" class="control-label">Date Range</label>
                    <select id="date-range" class="control-select" aria-describedby="date-help">
                        <option value="7d">Last 7 days</option>
                        <option value="30d" selected>Last 30 days</option>
                        <option value="90d">Last 90 days</option>
                        <option value="1y">Last year</option>
                    </select>
                    <div id="date-help" class="control-help">Select the time period for data display</div>
                </div>
                
                <div class="control-group">
                    <label for="category-filter" class="control-label">Category</label>
                    <select id="category-filter" class="control-select" multiple aria-describedby="category-help">
                        <option value="all">All Categories</option>
                        <option value="sales">Sales</option>
                        <option value="marketing">Marketing</option>
                        <option value="support">Support</option>
                    </select>
                    <div id="category-help" class="control-help">Filter data by category</div>
                </div>
                
                <button id="refresh-data" class="btn btn-primary" aria-describedby="refresh-help">
                    <span class="btn-icon">↻</span>
                    Refresh Data
                </button>
                <div id="refresh-help" class="control-help">Update all visualizations with latest data</div>
            </aside>
        </div>
        
        <!-- Status Bar -->
        <div class="status-bar" role="status" aria-live="polite">
            <span id="status-message">Dashboard loaded successfully</span>
            <span id="last-updated">Last updated: <time datetime="{datetime.now().isoformat()}">Just now</time></span>
        </div>
    </main>
    
    <!-- Footer -->
    <footer class="app-footer" role="contentinfo">
        <div class="footer-content">
            <p>&copy; 2024 Enhanced Project. Generated by Self-Collaboration Code Generation.</p>
            <div class="footer-links">
                <a href="#privacy" class="footer-link">Privacy</a>
                <a href="#terms" class="footer-link">Terms</a>
                <a href="#help" class="footer-link">Help</a>
            </div>
        </div>
    </footer>
    
    <!-- Loading overlay -->
    <div id="loading-overlay" class="loading-overlay" aria-hidden="true">
        <div class="loading-spinner" role="status" aria-label="Loading">
            <div class="spinner"></div>
            <span class="loading-text">Initializing application...</span>
        </div>
    </div>
    
    <!-- Scripts -->
    <script src="js/utils.js"></script>
    <script src="js/data.js"></script>
    <script src="js/visualization.js"></script>
    <script src="js/main.js"></script>
    
    <!-- External Libraries -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js" 
            integrity="sha384-..." crossorigin="anonymous"></script>
</body>
</html>'''
        
        # Enhanced CSS with modern features
        project_files['css/main.css'] = '''/* Enhanced Modern CSS with CSS Custom Properties */
:root {
    --color-primary: #007bff;
    --color-secondary: #6c757d;
    --bg-primary: #ffffff;
    --bg-card: #ffffff;
    --text-primary: #212529;
    --text-secondary: #6c757d;
    --border-radius: 0.375rem;
    --spacing-md: 1rem;
    --spacing-lg: 1.5rem;
    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    --transition-base: 250ms ease-in-out;
}

[data-theme="dark"] {
    --bg-primary: #1a1a1a;
    --bg-card: #2d2d2d;
    --text-primary: #ffffff;
    --text-secondary: #b3b3b3;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
    color: var(--text-primary);
    background-color: var(--bg-primary);
    transition: all var(--transition-base);
    margin: 0;
}

.dashboard-grid {
    display: grid;
    grid-template-columns: 1fr 300px;
    gap: var(--spacing-lg);
    padding: var(--spacing-lg);
    max-width: 1200px;
    margin: 0 auto;
}

.kpi-card, .chart-container {
    background: var(--bg-card);
    padding: var(--spacing-lg);
    border-radius: var(--border-radius);
    box-shadow: var(--shadow-sm);
    transition: transform var(--transition-base);
}

.kpi-card:hover, .chart-container:hover {
    transform: translateY(-2px);
}

.btn {
    padding: var(--spacing-md);
    border: none;
    border-radius: var(--border-radius);
    background: var(--color-primary);
    color: white;
    cursor: pointer;
    transition: all var(--transition-base);
}

.btn:hover {
    opacity: 0.9;
}

@media (max-width: 768px) {
    .dashboard-grid {
        grid-template-columns: 1fr;
    }
}'''

        # Enhanced JavaScript with modern features
        project_files['js/main.js'] = '''// Enhanced JavaScript Application
class EnhancedDashboard {
    constructor() {
        this.currentTheme = localStorage.getItem('theme') || 'light';
        this.init();
    }

    init() {
        this.setupTheme();
        this.setupEventListeners();
        this.loadData();
        console.log('Enhanced Dashboard initialized');
    }

    setupTheme() {
        document.documentElement.setAttribute('data-theme', this.currentTheme);
    }

    setupEventListeners() {
        const themeToggle = document.getElementById('theme-toggle');
        themeToggle?.addEventListener('click', () => this.toggleTheme());

        const refreshButton = document.getElementById('refresh-data');
        refreshButton?.addEventListener('click', () => this.refreshData());
    }

    toggleTheme() {
        this.currentTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', this.currentTheme);
        localStorage.setItem('theme', this.currentTheme);
        
        const icon = document.querySelector('.theme-icon');
        if (icon) icon.textContent = this.currentTheme === 'light' ? '🌙' : '☀️';
    }

    refreshData() {
        console.log('Refreshing data...');
        setTimeout(() => {
            console.log('Data refreshed');
        }, 1000);
    }

    loadData() {
        console.log('Loading data...');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new EnhancedDashboard();
});'''

        # Utility functions
        project_files['js/utils.js'] = '''// Utility functions
const utils = {
    formatNumber: (num) => {
        return new Intl.NumberFormat().format(num);
    },
    
    formatCurrency: (amount) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    },
    
    formatDate: (date) => {
        return new Intl.DateTimeFormat('en-US').format(new Date(date));
    }
};'''

        # Web App Manifest
        project_files['manifest.json'] = '''{
    "name": "Enhanced Dashboard Application",
    "short_name": "Dashboard",
    "description": "Advanced interactive dashboard with modern visualizations",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#ffffff",
    "theme_color": "#007bff",
    "orientation": "any",
    "icons": [
        {
            "src": "assets/icon-192.png",
            "sizes": "192x192",
            "type": "image/png"
        }
    ]
}'''
        
        return project_files

    def implement_project(self, architecture_plan, ui_design=None, existing_files=None, is_initial=True):
        """Implement the complete project based on architecture plan"""
        
        if is_initial:
            implementation_prompt = f"""
            Based on the following architecture plan, implement a complete {self.project_type} project.
            
            Architecture Plan: {architecture_plan}
            
            {f"UI Design Guidelines: {ui_design}" if ui_design else ""}
            
            Project Requirements: {self.requirement}
            
            Please provide the complete implementation with multiple files. 
            For each file, use the following format:
            
            === FILENAME: path/to/file.ext ===
            [file content here]
            === END FILE ===
            
            Requirements:
            1. Create a fully functional {self.project_type} application
            2. For web visualization projects, include interactive charts and modern UI
            3. Use modern web technologies (HTML5, CSS3, ES6+)
            4. Implement responsive design
            5. Add sample data for demonstrations
            6. Include error handling and user feedback
            7. Make the interface beautiful and user-friendly
            
            Focus on creating a complete, working application that demonstrates the requested functionality.
            """
        else:
            # Simple iterative improvement
            feedback_text = self.feedback_history[-1] if self.feedback_history else "No specific feedback"
            implementation_prompt = f"""
            Fix the issues in the existing project:
            
            Issues to fix: {feedback_text}
            
            Current files: {list(existing_files.keys()) if existing_files else "None"}
            
            Please update ONLY the files that need changes to fix these issues:
            === FILENAME: path/to/file.ext ===
            [updated file content here]
            === END FILE ===
            
            Make minimal changes to fix the specific issues mentioned.
            """
        
        self.history_message_append(implementation_prompt)
        
        try:
            responses = self.itf.run(prompt=self.history_message, majority_at=self.majority,
                                   max_tokens=self.max_tokens, temperature=self.temperature, top_p=self.top_p)
        except Exception as e:
            print(f"Project implementation failed: {e}")
            time.sleep(5)
            return "error"

        implementation = responses[0]
        self.history_message_append(implementation, "assistant")
        
        # Parse the implementation into separate files
        project_files = self._parse_implementation(implementation)
        
        # If parsing failed, create fallback files
        if not project_files:
            print("⚠️ Implementation parsing failed, creating fallback files...")
            project_files = self._create_fallback_files(implementation)
        
        return project_files
    
    def _parse_implementation(self, implementation):
        """Parse the implementation response into separate files"""
        project_files = {}
        
        # Pattern to match file sections
        file_pattern = r'=== FILENAME: (.+?) ===\n(.*?)\n=== END FILE ==='
        matches = re.findall(file_pattern, implementation, re.DOTALL)
        
        for file_path, content in matches:
            # Thoroughly clean file path
            file_path = self._clean_file_path(file_path.strip())
            content = self._clean_file_content(content.strip())
            
            # Validate file content quality
            if self._validate_file_content(file_path, content):
                project_files[file_path] = content
            else:
                print(f"⚠️ File {file_path} failed quality validation, using fallback")
        
        # If no files were parsed with the pattern, try alternative parsing
        if not project_files:
            project_files = self._alternative_parsing(implementation)
        
        # Use file manager tool to organize and clean files
        file_manager = self.tool_orchestrator.get_tool("file_manager")
        if file_manager and project_files:
            organized_result = file_manager.execute("organize", files=project_files)
            if organized_result and "organized_files" in organized_result:
                project_files = organized_result["organized_files"]
                print(f"📁 Files organized by FileManager: {len(project_files)} files")
        
        return project_files
    
    def _clean_file_path(self, file_path):
        """Clean file path, remove Markdown markers and invalid characters"""
        # Remove backticks and other Markdown markers
        clean_path = file_path.replace("`", "")
        clean_path = clean_path.replace("*", "")
        clean_path = clean_path.replace("**", "")
        clean_path = clean_path.replace("__", "")
        
        # Normalize path separators
        clean_path = clean_path.replace("\\", "/").strip("/")
        
        # Remove extra spaces while preserving reasonable spaces in filenames
        clean_path = re.sub(r'\s+', ' ', clean_path).strip()  # Replace multiple spaces with single space
        clean_path = clean_path.replace(" ", "_")  # Replace spaces with underscores
        
        # Remove other invalid characters while preserving valid filename characters
        clean_path = re.sub(r'[^\w\-_./ ]', '', clean_path)
        
        return clean_path
    
    def _clean_file_content(self, content):
        """Clean file content, remove Markdown wrapper"""
        if not content:
            return content
        
        # Remove code block wrapper (like ```html, ```css, ```js, etc.)
        content = content.strip()
        
        # Check if wrapped in code blocks
        if content.startswith('```'):
            lines = content.split('\n')
            # Remove the first line language identifier
            if len(lines) > 1:
                content = '\n'.join(lines[1:])
            
            # Remove ending ```
            if content.endswith('```'):
                content = content[:-3].rstrip()
        
        # Remove beginning ```` (four backticks case)
        if content.startswith('````'):
            lines = content.split('\n')
            if len(lines) > 1:
                content = '\n'.join(lines[1:])
            if content.endswith('````'):
                content = content[:-4].rstrip()
        
        # Remove extra line breaks
        content = content.strip()
        
        return content
    
    def _validate_file_content(self, file_path, content):
        """Validate file content quality"""
        if not content or len(content.strip()) < 10:
            return False
        
        # Check if content contains error messages or invalid content
        error_indicators = [
            "I'm sorry",
            "I cannot",
            "misunderstanding",
            "Implementation:",
            "error occurred"
        ]
        
        content_lower = content.lower()
        for indicator in error_indicators:
            if indicator.lower() in content_lower:
                return False
        
        # Basic validation by file type
        file_ext = file_path.split('.')[-1].lower()
        
        if file_ext == 'html':
            return '<!DOCTYPE' in content or '<html' in content
        elif file_ext == 'css':
            return '{' in content and '}' in content
        elif file_ext == 'js':
            return any(keyword in content for keyword in ['function', 'const', 'let', 'var', '=>'])
        elif file_ext == 'json':
            try:
                json.loads(content)
                return True
            except:
                return False
        
        return True

    def _create_fallback_files(self, implementation):
        """Create fallback files when parsing fails"""
        if self.project_type == 'python_project':
            return self._create_simple_python_files(implementation)
        else:
            return self._create_simple_web_files(implementation)
    
    def _create_simple_python_files(self, implementation):
        """Create simple Python fallback files"""
        project_files = {}
        
        project_files['main.py'] = f'''#!/usr/bin/env python3
"""
Generated Python Project - {self.project_type.replace('_', ' ').title()}
"""

def main():
    """Main function"""
    print("Hello from generated Python project!")
    print("Implementation details:")
    print("{implementation[:200]}...")

if __name__ == "__main__":
    main()
'''
        
        project_files['requirements.txt'] = '''# Generated requirements
pandas
numpy
matplotlib
'''
        
        project_files['README.md'] = f'''# {self.project_type.replace('_', ' ').title()}

This is a generated Python project.

## Usage

```bash
python main.py
```
'''
        
        return project_files
    
    def _create_simple_web_files(self, implementation):
        """Create fallback files when parsing fails"""
        project_files = {}
        
        # Create basic HTML file
        project_files['index.html'] = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.project_type.replace('_', ' ').title()}</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <div class="container">
        <h1>Generated Project</h1>
        <p>Implementation: {implementation[:500]}...</p>
    </div>
    <script src="js/main.js"></script>
</body>
</html>'''
        
        # Create basic CSS file
        project_files['css/style.css'] = '''
body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
    background-color: #f5f5f5;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

h1 {
    color: #333;
    text-align: center;
}
'''
        
        # Create basic JS file
        project_files['js/main.js'] = '''
document.addEventListener('DOMContentLoaded', function() {
    console.log('Project loaded successfully');
    // Generated implementation details would go here
});
'''
        
        return project_files
    
    def _adapt_to_frontend(self):
        """Adapt to frontend projects"""
        self.tech_stack = {
            "frameworks": ["React", "Vue.js", "Angular"],
            "tools": ["Webpack", "Vite", "ESLint", "Prettier"],
            "styling": ["CSS3", "SCSS", "Tailwind CSS", "CSS-in-JS"],
            "testing": ["Jest", "Cypress", "Testing Library"]
        }
        self.code_patterns = ["component_based", "responsive_design", "spa_routing"]
        
    def _adapt_to_backend(self):
        """Adapt to backend projects"""
        self.tech_stack = {
            "frameworks": ["Flask", "Django", "FastAPI", "Express.js"],
            "databases": ["PostgreSQL", "MongoDB", "Redis"],
            "tools": ["Docker", "pytest", "SQLAlchemy"],
            "apis": ["REST", "GraphQL", "WebSocket"]
        }
        self.code_patterns = ["mvc_architecture", "api_first", "microservices"]
        
    def _adapt_to_data_science(self):
        """Adapt to data science projects"""
        self.tech_stack = {
            "frameworks": ["pandas", "numpy", "scikit-learn", "plotly"],
            "tools": ["Jupyter", "Streamlit", "Dash"],
            "visualization": ["matplotlib", "seaborn", "plotly", "bokeh"],
            "ml_libs": ["tensorflow", "pytorch", "xgboost"]
        }
        self.code_patterns = ["notebook_based", "pipeline_architecture", "modular_analysis"]
        
    def _adapt_to_mobile(self):
        """Adapt to mobile application projects"""
        self.tech_stack = {
            "frameworks": ["React Native", "Flutter", "Ionic"],
            "tools": ["Expo", "Metro", "Flipper"],
            "platforms": ["iOS", "Android"],
            "testing": ["Detox", "Appium"]
        }
        self.code_patterns = ["cross_platform", "native_modules", "offline_first"]
        
    def _adapt_to_desktop(self):
        """Adapt to desktop application projects"""
        self.tech_stack = {
            "frameworks": ["Electron", "Tauri", "PyQt", "Tkinter"],
            "tools": ["electron-builder", "auto-updater"],
            "platforms": ["Windows", "macOS", "Linux"],
            "packaging": ["MSI", "DMG", "AppImage"]
        }
        self.code_patterns = ["desktop_conventions", "file_system_access", "native_integrations"]
        
    def _adapt_to_fullstack(self):
        """Adapt to full-stack projects"""
        self.tech_stack = {
            "frontend": ["React", "Next.js", "Vue.js"],
            "backend": ["Node.js", "Python", "Django"],
            "database": ["PostgreSQL", "MongoDB"],
            "deployment": ["Docker", "Vercel", "AWS"]
        }
        self.code_patterns = ["isomorphic_architecture", "api_backend", "ssr_support"]

    def history_message_append(self, message, role="user"):
        self.history_message.append({
            "role": role,
            "content": message
        })
        
    def receive_feedback(self, feedback):
        """Receive feedback and prepare for next iteration"""
        # Keep only the most recent feedback to avoid confusion
        self.feedback_history = [feedback]
        print(f"📝 Received feedback for improvement:\n{feedback[:200]}...")
        return "Feedback received, ready for next iteration"
        
    def _alternative_parsing(self, implementation):
        """Alternative parsing method for different response formats"""
        project_files = {}
        
        # Find common file patterns
        patterns = [
            (r'```html\n(.*?)\n```', 'index.html'),
            (r'```css\n(.*?)\n```', 'css/style.css'),
            (r'```javascript\n(.*?)\n```', 'js/main.js'),
            (r'```js\n(.*?)\n```', 'js/main.js'),
        ]
        
        for pattern, default_filename in patterns:
            matches = re.findall(pattern, implementation, re.DOTALL)
            if matches:
                # Use the first match of each file type
                project_files[default_filename] = matches[0].strip()
        
        return project_files