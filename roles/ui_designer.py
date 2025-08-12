import os
import copy
import json
import time

from core import interface
from utils import construct_system_message
from .enhanced_role import EnhancedRole


class UIDesigner(EnhancedRole):
    def __init__(self, team_description, designer_description, requirement, project_type,
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

        self.itf = interface.ProgramInterface(
            stop='',
            verbose=False,
            model=self.model,
        )

        system_message = construct_system_message(requirement, designer_description, team_description)
        self.history_message_append(system_message)

    def design_ui(self, architecture_plan):
        """Design the user interface for the project"""
        
        ui_design_prompt = f"""
        Based on the following architecture plan and project requirements, create a comprehensive UI design.
        
        Project Type: {self.project_type}
        Requirements: {self.requirement}
        Architecture Plan: {architecture_plan}
        
        Please provide a detailed UI design specification in JSON format:
        
        {{
            "design_system": {{
                "colors": {{
                    "primary": "#007bff",
                    "secondary": "#6c757d",
                    "background": "#f8f9fa",
                    "text": "#333333"
                }},
                "typography": {{
                    "font_family": "Arial, sans-serif",
                    "headings": "bold",
                    "body_size": "16px"
                }},
                "spacing": {{
                    "base_unit": "8px",
                    "container_padding": "20px",
                    "section_margin": "40px"
                }}
            }},
            "layout": {{
                "type": "responsive",
                "grid_system": "CSS Grid / Flexbox",
                "breakpoints": {{
                    "mobile": "768px",
                    "tablet": "992px",
                    "desktop": "1200px"
                }}
            }},
            "components": [
                {{
                    "name": "header",
                    "description": "Main navigation and branding",
                    "styling": "Modern, clean design with navigation menu"
                }},
                {{
                    "name": "main_content",
                    "description": "Primary content area",
                    "styling": "Card-based layout with proper spacing"
                }},
                {{
                    "name": "footer",
                    "description": "Footer information",
                    "styling": "Minimal, informational"
                }}
            ],
            "interactions": [
                {{
                    "element": "buttons",
                    "behavior": "Hover effects with smooth transitions"
                }},
                {{
                    "element": "forms",
                    "behavior": "Real-time validation with clear feedback"
                }}
            ],
            "accessibility": [
                "ARIA labels for interactive elements",
                "Keyboard navigation support",
                "High contrast color ratios",
                "Responsive text sizing"
            ]
        }}
        
        For web visualization projects, emphasize:
        - Modern, clean aesthetic
        - Interactive data visualization elements
        - Responsive design for all devices
        - Professional color scheme
        - Clear typography hierarchy
        - Intuitive user interactions
        """
        
        self.history_message_append(ui_design_prompt)
        
        try:
            responses = self.itf.run(prompt=self.history_message, majority_at=self.majority,
                                   max_tokens=self.max_tokens, temperature=self.temperature, top_p=self.top_p)
        except Exception as e:
            print(f"UI design failed: {e}")
            time.sleep(5)
            return "error"

        ui_design = responses[0]
        self.history_message_append(ui_design, "assistant")
        
        return ui_design
    
    def _adapt_to_frontend(self):
        """Adapt to frontend projects"""
        self.design_priorities = [
            "responsive_design",
            "modern_ui_components", 
            "cross_browser_compatibility",
            "performance_optimization",
            "accessibility"
        ]
        
    def _adapt_to_backend(self):
        """Adapt to backend projects"""
        self.design_priorities = [
            "admin_interface",
            "api_documentation_ui",
            "monitoring_dashboard",
            "simple_clean_design"
        ]
        
    def _adapt_to_data_science(self):
        """Adapt to data science projects"""
        self.design_priorities = [
            "data_visualization",
            "interactive_charts",
            "dashboard_layout",
            "analytical_ui_components",
            "filtering_controls"
        ]
        
    def _adapt_to_mobile(self):
        """Adapt to mobile application projects"""
        self.design_priorities = [
            "mobile_first_design",
            "touch_friendly_interface",
            "native_app_feel",
            "gesture_support",
            "offline_ui_states"
        ]
        
    def _adapt_to_desktop(self):
        """Adapt to desktop application projects"""
        self.design_priorities = [
            "desktop_conventions",
            "keyboard_shortcuts",
            "menu_systems",
            "toolbar_design",
            "window_management"
        ]
        
    def _adapt_to_fullstack(self):
        """Adapt to fullstack projects"""
        self.design_priorities = [
            "unified_design_system",
            "admin_and_user_interfaces",
            "responsive_components",
            "consistent_branding"
        ]

    def history_message_append(self, message, role="user"):
        self.history_message.append({
            "role": role,
            "content": message
        })
