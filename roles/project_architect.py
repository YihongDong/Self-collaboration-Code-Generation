import os
import copy
import json
import time

from core import interface
from utils import construct_system_message
from roles.enhanced_role import EnhancedRole


class ProjectArchitect(EnhancedRole):
    def __init__(self, team_description, architect_description, requirement, project_type,
                 model='gpt-3.5-turbo', majority=1, max_tokens=1024, temperature=0.2, top_p=0.95):
        # First call enhanced base class initialization
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

        system_message = construct_system_message(requirement, architect_description, team_description)
        self.history_message_append(system_message)
    
    def _adapt_to_project_type(self, project_type):
        """Adjust architect behavior based on project type"""
        super()._adapt_to_project_type(project_type)
        
        # Architect-specific adaptation logic
        adaptation_strategies = {
            "web_frontend": self._adapt_to_frontend_architecture,
            "web_backend": self._adapt_to_backend_architecture,
            "data_science": self._adapt_to_data_science_architecture,
            "mobile": self._adapt_to_mobile_architecture,
            "desktop": self._adapt_to_desktop_architecture,
            "fullstack": self._adapt_to_fullstack_architecture
        }
        
        strategy = adaptation_strategies.get(project_type, self._adapt_to_generic_architecture)
        strategy()
    
    def _adapt_to_frontend_architecture(self):
        """Adapt to frontend architecture design"""
        print("🎨 ProjectArchitect: Focusing on component-based frontend architecture")
    
    def _adapt_to_backend_architecture(self):
        """Adapt to backend architecture design"""
        print("⚙️ ProjectArchitect: Focusing on API and service architecture")
    
    def _adapt_to_data_science_architecture(self):
        """Adapt to data science architecture design"""
        print("📊 ProjectArchitect: Focusing on data pipeline and model architecture")
    
    def _adapt_to_mobile_architecture(self):
        """Adapt to mobile architecture design"""
        print("📱 ProjectArchitect: Focusing on mobile app architecture")
    
    def _adapt_to_desktop_architecture(self):
        """Adapt to desktop architecture design"""
        print("🖥️ ProjectArchitect: Focusing on desktop application architecture")
    
    def _adapt_to_fullstack_architecture(self):
        """Adapt to fullstack architecture design"""
        print("🌐 ProjectArchitect: Focusing on end-to-end system architecture")
    
    def _adapt_to_generic_architecture(self):
        """Adapt to generic architecture design"""
        print("🔧 ProjectArchitect: Using generic architecture patterns")

    def design_system_architecture(self, requirements=None):
        """Design system architecture - using enhanced quality gate process"""
        if requirements is None:
            requirements = {"description": self.requirement, "project_type": self.project_type}
        
        return self.execute_with_quality_gate(
            "architecture_design",
            self._design_architecture_internal,
            requirements
        )
    
    def _design_architecture_internal(self, requirements):
        """Internal architecture design logic"""
        # First determine project specification (if not already done)
        if not self.project_specification:
            spec_coordinator = self.get_tool("ProjectSpecificationCoordinator")
            project_spec_result = spec_coordinator.execute(
                requirements.get("project_type", self.project_type),
                requirements
            )
            self.set_project_specification(project_spec_result["project_specification"])
        
        # Design architecture based on project specification
        architecture = self._design_architecture_for_type(
            self.project_specification["type"],
            requirements,
            self.project_specification
        )
        
        return {
            "architecture": architecture,
            "project_specification": self.project_specification,
            "design_rationale": self._generate_design_rationale(architecture),
            "implementation_guidance": self._generate_implementation_guidance(architecture)
        }
    
    def _design_architecture_for_type(self, project_type, requirements, project_spec):
        """Design architecture based on project type"""
        architecture_designers = {
            "web_frontend": self._design_frontend_architecture,
            "web_backend": self._design_backend_architecture,
            "data_science": self._design_data_science_architecture,
            "mobile": self._design_mobile_architecture,
            "desktop": self._design_desktop_architecture,
            "fullstack": self._design_fullstack_architecture
        }
        
        designer = architecture_designers.get(project_type, self._design_generic_architecture)
        return designer(requirements, project_spec)
    
    def _design_frontend_architecture(self, requirements, project_spec):
        """Design frontend architecture"""
        tech_stack = project_spec["technology_stack"]
        
        return {
            "type": "frontend",
            "components": [
                {"name": "App", "responsibility": "Main application component", "type": "container"},
                {"name": "Header", "responsibility": "Navigation and branding", "type": "presentational"},
                {"name": "Sidebar", "responsibility": "Secondary navigation", "type": "presentational"},
                {"name": "MainContent", "responsibility": "Primary content display", "type": "container"},
                {"name": "Footer", "responsibility": "Footer information", "type": "presentational"}
            ],
            "state_management": {
                "pattern": "Component State" if "React" in tech_stack.get("frameworks", []) else "Global State",
                "tools": tech_stack.get("state_management", ["Context API"])
            },
            "routing": {
                "type": "client-side",
                "routes": [
                    {"path": "/", "component": "Home", "description": "Landing page"},
                    {"path": "/dashboard", "component": "Dashboard", "description": "Main dashboard"},
                    {"path": "/settings", "component": "Settings", "description": "User settings"}
                ]
            },
            "data_flow": "Component Props -> State -> UI Updates",
            "file_structure": {
                "src/": "Source code directory",
                "src/components/": "React/Vue components",
                "src/styles/": "CSS/SCSS files", 
                "src/utils/": "Utility functions",
                "public/": "Static assets"
            }
        }
    
    def _design_backend_architecture(self, requirements, project_spec):
        """Design backend architecture"""
        tech_stack = project_spec["technology_stack"]
        
        return {
            "type": "backend",
            "services": [
                {"name": "UserService", "responsibility": "User management", "endpoints": ["/users", "/auth"]},
                {"name": "DataService", "responsibility": "Data operations", "endpoints": ["/data", "/analytics"]},
                {"name": "NotificationService", "responsibility": "Notifications", "endpoints": ["/notifications"]}
            ],
            "api": {
                "style": "REST",
                "version": "v1",
                "endpoints": [
                    {"method": "GET", "path": "/api/v1/users", "description": "Get all users"},
                    {"method": "POST", "path": "/api/v1/users", "description": "Create user"},
                    {"method": "GET", "path": "/api/v1/data", "description": "Get data"}
                ]
            },
            "data_model": {
                "entities": [
                    {"name": "User", "fields": ["id", "name", "email", "created_at"]},
                    {"name": "DataRecord", "fields": ["id", "user_id", "data", "timestamp"]}
                ]
            },
            "middleware": ["Authentication", "CORS", "Rate Limiting", "Logging"],
            "file_structure": {
                "app/": "Main application code",
                "app/models/": "Data models",
                "app/services/": "Business logic services",
                "app/controllers/": "Request handlers",
                "config/": "Configuration files"
            }
        }
    
    def _design_data_science_architecture(self, requirements, project_spec):
        """Design data science architecture"""
        return {
            "type": "data_science",
            "pipeline": [
                {"stage": "Data Ingestion", "tools": ["pandas", "requests"], "responsibility": "Collect raw data"},
                {"stage": "Data Cleaning", "tools": ["pandas", "numpy"], "responsibility": "Clean and validate data"},
                {"stage": "Feature Engineering", "tools": ["scikit-learn"], "responsibility": "Create features"},
                {"stage": "Model Training", "tools": ["scikit-learn", "tensorflow"], "responsibility": "Train models"},
                {"stage": "Model Evaluation", "tools": ["scikit-learn", "matplotlib"], "responsibility": "Evaluate performance"},
                {"stage": "Deployment", "tools": ["flask", "docker"], "responsibility": "Deploy model"}
            ],
            "data_flow": "Raw Data -> Cleaned Data -> Features -> Model -> Predictions",
            "file_structure": {
                "data/": "Data files (raw, processed)",
                "notebooks/": "Jupyter notebooks for exploration", 
                "src/": "Python modules",
                "models/": "Trained model files",
                "config/": "Configuration files"
            }
        }
    
    def _design_mobile_architecture(self, requirements, project_spec):
        """Design mobile architecture"""
        return {
            "type": "mobile",
            "navigation": {
                "type": "Stack Navigation",
                "screens": [
                    {"name": "Home", "description": "Main screen"},
                    {"name": "Profile", "description": "User profile"},
                    {"name": "Settings", "description": "App settings"}
                ]
            },
            "components": [
                {"name": "AppNavigator", "responsibility": "Navigation container"},
                {"name": "HomeScreen", "responsibility": "Main application screen"},
                {"name": "CustomButton", "responsibility": "Reusable button component"}
            ],
            "file_structure": {
                "src/screens/": "Screen components",
                "src/components/": "Reusable components",
                "src/navigation/": "Navigation configuration",
                "src/services/": "API and data services"
            }
        }
    
    def _design_desktop_architecture(self, requirements, project_spec):
        """Design desktop architecture"""
        return {
            "type": "desktop",
            "windows": [
                {"name": "MainWindow", "description": "Primary application window"},
                {"name": "SettingsDialog", "description": "Settings configuration"},
                {"name": "AboutDialog", "description": "About information"}
            ],
            "components": [
                {"name": "MenuBar", "responsibility": "Application menu"},
                {"name": "StatusBar", "responsibility": "Status information"},
                {"name": "ContentArea", "responsibility": "Main content display"}
            ],
            "file_structure": {
                "src/": "Source code",
                "resources/": "Images, icons, etc.",
                "config/": "Configuration files"
            }
        }
    
    def _design_fullstack_architecture(self, requirements, project_spec):
        """Design fullstack architecture"""
        frontend_arch = self._design_frontend_architecture(requirements, project_spec)
        backend_arch = self._design_backend_architecture(requirements, project_spec)
        
        return {
            "type": "fullstack",
            "frontend": frontend_arch,
            "backend": backend_arch,
            "integration": {
                "api_communication": "REST API calls from frontend to backend",
                "authentication": "JWT tokens",
                "data_synchronization": "Real-time updates via WebSocket"
            },
            "deployment": {
                "frontend": "Static hosting (Vercel, Netlify)",
                "backend": "Container deployment (Docker + K8s)",
                "database": "Managed database service"
            }
        }
    
    def _design_generic_architecture(self, requirements, project_spec):
        """Design generic architecture"""
        return {
            "type": "generic",
            "components": [
                {"name": "Core", "responsibility": "Main application logic"},
                {"name": "Interface", "responsibility": "User interface"},
                {"name": "Data", "responsibility": "Data management"}
            ],
            "patterns": ["MVC", "Observer", "Factory"],
            "file_structure": {
                "src/": "Source code",
                "docs/": "Documentation",
                "tests/": "Test files"
            }
        }
    
    def _generate_design_rationale(self, architecture):
        """Generate design rationale"""
        return {
            "architectural_decisions": [
                f"Chose {architecture.get('type', 'generic')} architecture for project requirements",
                "Component-based design for maintainability",
                "Clear separation of concerns",
                "Scalable file structure"
            ],
            "trade_offs": [
                "Flexibility vs. Simplicity",
                "Performance vs. Maintainability",
                "Development Speed vs. Code Quality"
            ]
        }
    
    def _generate_implementation_guidance(self, architecture):
        """Generate implementation guidance"""
        return {
            "development_phases": [
                "1. Set up project structure",
                "2. Implement core components",
                "3. Add data layer",
                "4. Implement user interface",
                "5. Add testing",
                "6. Performance optimization"
            ],
            "best_practices": [
                "Follow naming conventions",
                "Write clean, readable code",
                "Include comprehensive tests",
                "Document API endpoints",
                "Use version control effectively"
            ]
        }

    def design_architecture(self):
        """Design the overall project architecture"""
        architecture_prompt = f"""
        Please design a complete project architecture for a {self.project_type} project.
        
        Project Requirements: {self.requirement}
        
        Provide a detailed JSON response with the following structure:
        {{
            "project_structure": {{
                "files": [
                    {{"path": "index.html", "description": "Main HTML file", "priority": 1}},
                    {{"path": "css/style.css", "description": "Main stylesheet", "priority": 2}},
                    {{"path": "js/main.js", "description": "Main JavaScript file", "priority": 2}}
                ]
            }},
            "technology_stack": {{
                "frontend": ["HTML5", "CSS3", "JavaScript"],
                "visualization": ["Chart.js", "D3.js"],
                "styling": ["Bootstrap", "CSS Grid", "Flexbox"]
            }},
            "implementation_phases": [
                {{"phase": 1, "description": "Create basic HTML structure and layout"}},
                {{"phase": 2, "description": "Implement styling and responsive design"}},
                {{"phase": 3, "description": "Add interactive visualizations and functionality"}}
            ],
            "component_interactions": [
                {{"source": "main.js", "target": "index.html", "description": "Dynamic content updates"}},
                {{"source": "style.css", "target": "index.html", "description": "Visual styling"}}
            ]
        }}
        
        For web visualization projects, prioritize creating interactive charts, beautiful UI, and responsive design.
        """
        
        self.history_message_append(architecture_prompt)
        
        try:
            responses = self.itf.run(prompt=self.history_message, majority_at=self.majority, 
                                   max_tokens=self.max_tokens, temperature=self.temperature, top_p=self.top_p)
        except Exception as e:
            print(f"Architecture design failed: {e}")
            time.sleep(5)
            return "error"

        architecture = responses[0]
        self.history_message_append(architecture, "assistant")
        
        return architecture
    
    def history_message_append(self, message, role="user"):
        self.history_message.append({
            "role": role,
            "content": message
        })
