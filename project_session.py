from roles.analyst import Analyst
from roles.coder import Coder
from roles.tester import Tester
from roles.project_architect import ProjectArchitect
from roles.project_developer import ProjectDeveloper
from roles.project_tester import ProjectTester
from roles.ui_designer import UIDesigner
from utils import find_method_name, construct_system_message
from tools import global_tool_orchestrator, CodeAnalyzer, FileManager, QualityChecker, APIIntegrationTool, AutomatedTester
import time
import os
import json
import re


class ProjectSession(object):
    def __init__(self, team_description, architect_description, developer_description, 
                 tester_description, ui_designer_description, requirement, project_type='web_visualization',
                 model='gpt-3.5-turbo', majority=1, max_tokens=1024,
                 temperature=0.2, top_p=0.95, max_round=3, output_dir='generated_project'):

        self.session_history = {}
        self.max_round = max_round
        self.requirement = requirement
        self.project_type = project_type
        self.output_dir = output_dir
        self.project_files = {}
        
        # Intelligently adjust max_tokens to avoid context length issues
        self.base_max_tokens = max_tokens
        self.current_max_tokens = max_tokens
        self.model = model
        
        # Dynamically adjust tokens based on model and rounds
        model_limits = {
            'gpt-3.5-turbo': 16385,
            'gpt-4': 16385,
        }
        self.model_limit = model_limits.get(model, 16385)
        
        # Initial token allocation: reserve space for multi-round iteration
        if max_round > 1:
            # Use smaller tokens for multi-round iteration, reserve space for history
            adjusted_max_tokens = min(max_tokens, self.model_limit // (max_round + 1))
        else:
            adjusted_max_tokens = max_tokens
        
        print(f"🔧 Token management: Model={model}, Limit={self.model_limit}, Base={max_tokens}, Adjusted={adjusted_max_tokens}")
        
        # Initialize tools
        self.tool_orchestrator = global_tool_orchestrator
        self.code_analyzer = CodeAnalyzer()
        self.file_manager = FileManager()
        self.quality_checker = QualityChecker()
        self.api_tool = APIIntegrationTool()
        self.automated_tester = AutomatedTester()
        
        # Initialize project roles with adjusted tokens
        self.architect = ProjectArchitect(team_description, architect_description, requirement, 
                                        project_type, model, majority, adjusted_max_tokens, temperature, top_p)
        self.developer = ProjectDeveloper(team_description, developer_description, requirement,
                                        project_type, model, majority, adjusted_max_tokens, temperature, top_p)
        self.tester = ProjectTester(team_description, tester_description, requirement,
                                  project_type, model, majority, adjusted_max_tokens, temperature, top_p)
        self.ui_designer = UIDesigner(team_description, ui_designer_description, requirement,
                                    project_type, model, majority, adjusted_max_tokens, temperature, top_p)
    
    def _adjust_tokens_for_round(self, round_num):
        """Dynamically adjust token allocation based on round number"""
        # As rounds increase, reduce token allocation to reserve space for conversation history
        reduction_factor = 1.0 #- (round_num * 0.1)  # Reduce 10% per round
        new_max_tokens = max(int(self.base_max_tokens * reduction_factor), 512)  # Minimum 512 tokens
        
        if new_max_tokens != self.current_max_tokens:
            print(f"🔄 Round {round_num + 1}: Adjusting max_tokens from {self.current_max_tokens} to {new_max_tokens}")
            self.current_max_tokens = new_max_tokens
            
            # Update token settings for all roles
            for role in [self.architect, self.developer, self.tester, self.ui_designer]:
                if hasattr(role, 'max_tokens'):
                    role.max_tokens = new_max_tokens
        
        return new_max_tokens
    
    def run_project_session(self):
        """Run the complete project generation session with integrated tools"""
        
        print("🔧 Phase 0: Initializing resources...")
        # Fetch external resources based on project type
        if self.project_type == 'web_visualization':
            external_resources = self.api_tool.execute(
                "fetch_cdn_libraries", 
                libraries=["chart.js", "d3.js", "bootstrap", "jquery"]
            )
            self.session_history["external_resources"] = external_resources
            print(f"✅ Fetched external resources: {len(external_resources.get('libraries', []))} libraries")
        
        # Phase 1: Planning and Architecture Design
        print("🏗️ Phase 1: Creating planning and architecture design...")
        architecture_plan = self.architect.design_architecture()
        self.session_history["architecture"] = architecture_plan
        
        if architecture_plan == "error":
            raise RuntimeError("Architecture design failed")
        
        # Use code analyzer to analyze architecture plan
        if isinstance(architecture_plan, str):
            arch_analysis = self.code_analyzer.execute(
                "analyze",
                code=architecture_plan,
                project_type=self.project_type
            )
            print(f"📊 Architecture analysis: {arch_analysis.get('summary', 'Analysis completed')}")
        
        # Phase 2: UI Design (for web projects) 
        ui_design = None
        if self.project_type in ['web_visualization', 'desktop_app']:
            print("🎨 Phase 2: Creating UI design...")
            ui_design = self.ui_designer.design_ui(architecture_plan)
            self.session_history["ui_design"] = ui_design
            
            # Fetch color palette and fonts for better design
            if ui_design != "error":
                design_resources = self.api_tool.execute("fetch_color_palette", theme="modern")
                fonts = self.api_tool.execute("get_web_fonts", font_name="Open Sans")
                self.session_history["design_resources"] = {
                    "colors": design_resources,
                    "fonts": fonts
                }
                print("🎨 Enhanced UI design with external resources")
        
        # Phase 3: Development with iterative improvement
        print("⚡ Phase 3: Implementing project iteratively...")
        for round_num in range(self.max_round):
            print(f"🔄 Development round {round_num + 1}/{self.max_round}")
            
            # Dynamically adjust token allocation
            self._adjust_tokens_for_round(round_num)
            
            # Development with file management
            try:
                project_files = self.developer.implement_project(architecture_plan, ui_design, 
                                                               self.project_files, round_num == 0)
            except Exception as e:
                error_str = str(e)
                if "context_length_exceeded" in error_str or "maximum context length" in error_str:
                    print(f"⚠️ Context length exceeded in round {round_num + 1}, reducing complexity...")
                    # Clear developer's message history
                    if hasattr(self.developer, 'itf') and hasattr(self.developer.itf, 'clear_history'):
                        self.developer.itf.clear_history()
                    # Retry once with fewer tokens
                    self.current_max_tokens = max(self.current_max_tokens // 2, 256)
                    self.developer.max_tokens = self.current_max_tokens
                    try:
                        project_files = self.developer.implement_project(architecture_plan, ui_design, 
                                                                       self.project_files, round_num == 0)
                    except Exception as e2:
                        print(f"❌ Failed after retry: {e2}")
                        if round_num == 0:
                            raise RuntimeError("Initial development failed")
                        else:
                            project_files = self.project_files
                            break
                else:
                    raise e
            
            if project_files == "error":
                if round_num == 0:
                    raise RuntimeError("Initial development failed")
                else:
                    # Use files from previous round
                    project_files = self.project_files
                    break
            
            # Use file manager to organize and validate files
            file_validation = self.file_manager.execute(
                "validate_structure",
                files=project_files,
                project_type=self.project_type
            )
            print(f"📁 File structure validation: {file_validation.get('status', 'completed')}")
            
            # Save generated files with backup
            self._save_project_files_with_tools(project_files)
            self.project_files = project_files
            
            # Quality checking with enhanced tools
            quality_report = self.quality_checker.execute(
                "comprehensive_check",
                files=project_files,
                project_type=self.project_type
            )
            print(f"🔍 Quality check score: {quality_report.get('overall_score', 'N/A')}")
            
            # Testing and feedback with automated tools (except last round)
            if round_num < self.max_round - 1:
                print("🧪 Testing with automated tools...")
                
                # Traditional testing
                test_report = self.tester.test_project(project_files, architecture_plan)
                
                # Enhanced automated testing
                automated_test_results = self.automated_tester.execute(
                    "full_suite",
                    files=project_files,
                    project_type=self.project_type
                )
                
                combined_test_report = {
                    "traditional_tests": test_report,
                    "automated_tests": automated_test_results,
                    "quality_metrics": quality_report
                }
                
                self.session_history[f'round_{round_num}'] = {
                    "files": list(project_files.keys()),
                    "test_report": combined_test_report,
                    "tool_reports": {
                        "file_validation": file_validation,
                        "quality_check": quality_report
                    }
                }
                
                if test_report == "error":
                    print("⚠️ Testing failed, continuing with current implementation")
                    break
                
                # Enhanced success criteria
                traditional_passed = ("all tests passed" in test_report.lower() or 
                                    "no issues found" in test_report.lower())
                automated_passed = automated_test_results.get("overall_status") == "passed"
                quality_good = quality_report.get("overall_score", 0) >= 7.0
                
                if traditional_passed and automated_passed and quality_good:
                    print("✅ All tests passed with high quality! Project completed successfully.")
                    break
                
                # Provide enhanced feedback combining all reports
                enhanced_feedback = self._generate_enhanced_feedback(
                    test_report, automated_test_results, quality_report
                )
                self.developer.receive_feedback(enhanced_feedback)
            
            # Adjust tokens for next round
            self._adjust_tokens_for_round(round_num)
        
        # Final tool report generation
        print("📊 Generating final tool usage report...")
        tool_usage_report = self.tool_orchestrator.generate_report()
        self.session_history["tool_usage_report"] = tool_usage_report
        
        # Clean up interfaces
        self.architect.itf.clear_history()
        self.developer.itf.clear_history() 
        self.tester.itf.clear_history()
        if hasattr(self.ui_designer, 'itf'):
            self.ui_designer.itf.clear_history()

        return self.project_files, self.session_history
    
    def _save_project_files(self, project_files):
        """Save generated project files to disk"""
        for file_path, content in project_files.items():
            full_path = os.path.join(self.output_dir, file_path)
            
            # Create directory if it doesn't exist
            dir_path = os.path.dirname(full_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            
            # Write file content
            try:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Saved: {file_path}")
            except Exception as e:
                print(f"Error saving {file_path}: {e}")
    
    def _save_project_files_with_tools(self, project_files):
        """Save project files with tool assistance and backup"""
        # Use file manager to organize files before saving
        organization_result = self.file_manager.execute(
            "organize_files",
            files=project_files,
            output_dir=self.output_dir
        )
        
        # Create backup if files already exist
        backup_result = self.file_manager.execute(
            "backup_existing",
            output_dir=self.output_dir
        )
        
        # Save files with the original method
        self._save_project_files(project_files)
        
        print(f"📁 File organization: {organization_result.get('status', 'completed')}")
        if backup_result.get('backup_created'):
            print(f"💾 Backup created: {backup_result.get('backup_path', 'N/A')}")
    
    def _generate_enhanced_feedback(self, traditional_report, automated_report, quality_report):
        """Generate simple, actionable feedback for the developer"""
        
        # Start with a simple structure
        issues = []
        
        # Check for test failures
        if automated_report.get("issues"):
            issues.extend(automated_report["issues"])
        
        # Traditional test issues
        if traditional_report and "error" in traditional_report.lower():
            issues.append("Fix syntax errors and runtime issues")
        
        # Generate simple feedback
        if not issues:
            return "✅ Good! Continue with current implementation approach."
        
        # Create actionable feedback
        feedback = "Please fix these issues:\n"
        for i, issue in enumerate(issues[:3], 1):  # Limit to 3 most important issues
            feedback += f"{i}. {issue}\n"
        
        feedback += "\nFocus on fixing issues for better results."
        return feedback


class FunctionSession(object):
    """Original function-level session for backwards compatibility"""
    def __init__(self, TEAM, ANALYST, PYTHON_DEVELOPER, TESTER, requirement, model='gpt-3.5-turbo', 
                 majority=1, max_tokens=512, temperature=0.0, top_p=0.95, max_round=4, before_func=''):

        self.session_history = {}
        self.max_round = max_round
        self.before_func = before_func
        self.requirement = requirement
        self.analyst = Analyst(TEAM, ANALYST, requirement, model, majority, max_tokens, temperature, top_p)
        self.coder = Coder(TEAM, PYTHON_DEVELOPER, requirement, model, majority, max_tokens, temperature, top_p)
        self.tester = Tester(TEAM, TESTER, requirement, model, majority, max_tokens, temperature, top_p)
    
    def run_session(self):
        # ... (keep original implementation from session.py)
        from session import Session
        original_session = Session(None, None, None, None, self.requirement, 
                                 model=self.analyst.model, majority=self.analyst.majority,
                                 max_tokens=self.analyst.max_tokens, temperature=self.analyst.temperature,
                                 top_p=self.analyst.top_p, max_round=self.max_round, 
                                 before_func=self.before_func)
        original_session.analyst = self.analyst
        original_session.coder = self.coder  
        original_session.tester = self.tester
        return original_session.run_session()
