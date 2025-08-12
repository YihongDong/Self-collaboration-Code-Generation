import os
import copy
import json
import time
import re

from core import interface
from utils import construct_system_message


class WebVisualizationSpecialist(object):
    def __init__(self, team_description, specialist_description, requirement, project_type,
                 model='gpt-3.5-turbo', majority=1, max_tokens=2048, temperature=0.3, top_p=0.95):
        self.model = model
        self.majority = majority
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.history_message = []
        self.requirement = requirement
        self.project_type = project_type

        self.itf = interface.ProgramInterface(
            stop='',
            verbose=False,
            model=self.model,
        )

        system_message = construct_system_message(requirement, specialist_description, team_description)
        self.history_message_append(system_message)

    def create_visualization_plan(self, architecture_plan):
        """Create detailed visualization specifications"""
        
        visualization_prompt = f"""
        Based on the project requirements and architecture plan, create a comprehensive visualization specification.
        
        Project Type: {self.project_type}
        Requirements: {self.requirement}
        Architecture Plan: {architecture_plan}
        
        Please provide a detailed JSON specification that includes:
        
        {{
            "visualization_strategy": {{
                "primary_library": "Chart.js|D3.js|Plotly|ECharts",
                "secondary_libraries": ["Three.js", "Leaflet"],
                "data_processing": "client-side|server-side|hybrid",
                "performance_approach": "canvas|svg|webgl"
            }},
            "chart_specifications": [
                {{
                    "chart_type": "bar|line|pie|scatter|heatmap|treemap|3d",
                    "library": "Chart.js|D3.js|Plotly|ECharts",
                    "data_source": "static|api|realtime|uploaded",
                    "interactivity": ["hover", "click", "zoom", "brush", "filter"],
                    "animations": ["entrance", "update", "transition"],
                    "responsive": true,
                    "accessibility": ["aria-labels", "keyboard-nav", "screen-reader"]
                }}
            ],
            "interactive_features": {{
                "real_time_updates": true|false,
                "data_filters": ["date-range", "category", "search"],
                "cross_chart_interactions": true|false,
                "export_functionality": ["png", "pdf", "csv", "json"],
                "drill_down_capabilities": true|false
            }},
            "performance_optimizations": {{
                "lazy_loading": true|false,
                "data_virtualization": true|false,
                "web_workers": true|false,
                "caching_strategy": "memory|localStorage|sessionStorage",
                "progressive_loading": true|false
            }},
            "modern_features": {{
                "pwa_support": true|false,
                "offline_functionality": true|false,
                "web_components": true|false,
                "module_system": "es6|webpack|rollup",
                "typescript_support": true|false
            }},
            "sample_data_structure": {{
                "format": "json|csv|api_response",
                "schema": "describe expected data structure",
                "sample_size": "number of records for demo"
            }}
        }}
        
        Focus on creating specifications that will result in:
        1. High-performance visualizations
        2. Rich interactivity and user engagement
        3. Beautiful, modern aesthetics
        4. Responsive design for all devices
        5. Accessibility compliance
        6. Scalability for large datasets
        """
        
        self.history_message_append(visualization_prompt)
        
        try:
            responses = self.itf.run(prompt=self.history_message, majority_at=self.majority,
                                   max_tokens=self.max_tokens, temperature=self.temperature, top_p=self.top_p)
        except Exception as e:
            print(f"Visualization planning failed: {e}")
            time.sleep(5)
            return "error"

        visualization_plan = responses[0]
        self.history_message_append(visualization_plan, "assistant")
        
        return visualization_plan

    def generate_advanced_code_templates(self, visualization_plan, ui_design):
        """Generate advanced code templates with modern visualization libraries"""
        
        template_prompt = f"""
        Based on the visualization plan and UI design, generate comprehensive code templates.
        
        Visualization Plan: {visualization_plan}
        UI Design: {ui_design}
        
        Please provide complete code templates for the following files:
        
        === TEMPLATE: js/visualization-engine.js ===
        // Advanced visualization engine with multiple library support
        // Include: Chart.js, D3.js, and Plotly integration
        // Features: Dynamic chart switching, real-time updates, responsive design
        
        === TEMPLATE: js/data-manager.js ===  
        // Data management and processing utilities
        // Include: API integration, data transformation, caching, real-time updates
        
        === TEMPLATE: js/interaction-controller.js ===
        // Advanced interaction handling
        // Include: Cross-chart filtering, brush-zoom, touch support, keyboard navigation
        
        === TEMPLATE: css/visualization-styles.css ===
        // Modern CSS for visualizations
        // Include: CSS Grid layouts, animations, dark/light themes, responsive design
        
        === TEMPLATE: js/performance-optimizer.js ===
        // Performance optimization utilities
        // Include: Data virtualization, lazy loading, Web Workers integration
        
        Requirements for each template:
        1. Use modern ES6+ JavaScript features
        2. Include comprehensive error handling
        3. Implement responsive design patterns
        4. Add accessibility features (ARIA labels, keyboard navigation)
        5. Include performance optimizations
        6. Use modular, reusable code structure
        7. Add detailed comments explaining functionality
        8. Support multiple visualization libraries
        9. Include sample data and demo functionality
        10. Implement modern web standards (Progressive Web App features)
        
        Each template should be production-ready and demonstrate best practices.
        """
        
        self.history_message_append(template_prompt)
        
        try:
            responses = self.itf.run(prompt=self.history_message, majority_at=self.majority,
                                   max_tokens=self.max_tokens, temperature=self.temperature, top_p=self.top_p)
        except Exception as e:
            print(f"Template generation failed: {e}")
            time.sleep(5)
            return {}

        templates_response = responses[0]
        self.history_message_append(templates_response, "assistant")
        
        # Parse the templates from the response
        templates = self._parse_templates(templates_response)
        
        return templates

    def _parse_templates(self, templates_response):
        """Parse the templates response into separate files"""
        templates = {}
        
        # Pattern to match template sections
        template_pattern = r'=== TEMPLATE: (.+?) ===\n(.*?)(?=\n=== TEMPLATE:|$)'
        matches = re.findall(template_pattern, templates_response, re.DOTALL)
        
        for file_path, content in matches:
            file_path = file_path.strip()
            content = content.strip()
            templates[file_path] = content
        
        return templates

    def optimize_for_performance(self, project_files):
        """Provide performance optimization suggestions"""
        
        files_summary = "\n".join([f"{path}: {len(content)} characters" 
                                  for path, content in project_files.items()])
        
        optimization_prompt = f"""
        Analyze the following project files and provide performance optimization recommendations.
        
        Project Files Summary:
        {files_summary}
        
        Please provide specific recommendations for:
        1. JavaScript performance optimizations
        2. CSS optimization strategies
        3. Data loading and caching improvements
        4. Visualization rendering optimizations
        5. Mobile performance considerations
        6. Bundle size reduction techniques
        7. Progressive loading strategies
        8. Memory management improvements
        
        Focus on modern web performance best practices and visualization-specific optimizations.
        """
        
        self.history_message_append(optimization_prompt)
        
        try:
            responses = self.itf.run(prompt=self.history_message, majority_at=self.majority,
                                   max_tokens=self.max_tokens, temperature=self.temperature, top_p=self.top_p)
        except Exception as e:
            print(f"Performance optimization failed: {e}")
            time.sleep(5)
            return "error"

        optimization_suggestions = responses[0]
        self.history_message_append(optimization_suggestions, "assistant")
        
        return optimization_suggestions

    def history_message_append(self, message, role="user"):
        self.history_message.append({
            "role": role,
            "content": message
        })