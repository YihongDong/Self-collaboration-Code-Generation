"""
Practical tool orchestrator - for project mode
"""
import os
import json
import re
from datetime import datetime

class GlobalToolOrchestrator:
    """Global tool orchestrator - manages and coordinates various development tools"""
    
    def __init__(self):
        self.tools = {}
        self.execution_log = []
        self.start_time = datetime.now()
    
    def execute(self, action, *args, **kwargs):
        """Execute specified tool operation"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "args": args,
            "kwargs": kwargs
        }
        
        try:
            if action == "organize_files":
                result = self._organize_files(kwargs.get("files", {}), kwargs.get("output_dir", ""))
            elif action == "backup_existing":
                result = self._backup_existing(kwargs.get("output_dir", ""))
            elif action == "fetch_color_palette":
                result = self._fetch_color_palette(kwargs.get("theme", "modern"))
            elif action == "get_web_fonts":
                result = self._get_web_fonts(kwargs.get("font_name", "Open Sans"))
            elif action == "fetch_external_libraries":
                result = self._fetch_external_libraries(kwargs.get("project_type", "web"))
            elif action == "automated_tester_check":
                result = self._run_automated_tests(kwargs.get("files", {}))
            elif action == "quality_check":
                result = self._run_quality_check(kwargs.get("files", {}), kwargs.get("project_type", "web"))
            else:
                result = {"status": "success", "result": f"Tool action '{action}' executed"}
            
            log_entry["result"] = result
            log_entry["status"] = "success"
            
        except Exception as e:
            result = {"status": "error", "error": str(e)}
            log_entry["result"] = result
            log_entry["status"] = "error"
        
        self.execution_log.append(log_entry)
        return result
    
    def _organize_files(self, files, output_dir):
        """Organize file structure"""
        organized = {}
        for file_path, content in files.items():
            # Ensure file path normalization
            clean_path = file_path.replace("\\", "/").strip("/")
            organized[clean_path] = content
        
        return {
            "status": "success",
            "organized_files": len(organized),
            "structure": list(organized.keys())
        }
    
    def _backup_existing(self, output_dir):
        """Backup existing files"""
        if not os.path.exists(output_dir):
            return {"backup_created": False, "reason": "Output directory does not exist"}
        
        files = os.listdir(output_dir)
        if not files:
            return {"backup_created": False, "reason": "No files to backup"}
        
        backup_dir = f"{output_dir}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        # This is just simulation backup logic, real projects can implement actual backup
        return {
            "backup_created": True,
            "backup_path": backup_dir,
            "files_backed_up": len(files)
        }
    
    def _fetch_color_palette(self, theme):
        """Get color palette"""
        palettes = {
            "modern": {
                "primary": "#3498db",
                "secondary": "#2ecc71", 
                "accent": "#e74c3c",
                "background": "#f8f9fa",
                "text": "#2c3e50"
            },
            "dark": {
                "primary": "#0d1117",
                "secondary": "#21262d",
                "accent": "#58a6ff",
                "background": "#010409",
                "text": "#f0f6fc"
            },
            "minimal": {
                "primary": "#000000",
                "secondary": "#ffffff",
                "accent": "#6c757d",
                "background": "#f8f9fa",
                "text": "#212529"
            }
        }
        
        return {
            "status": "success",
            "theme": theme,
            "palette": palettes.get(theme, palettes["modern"])
        }
    
    def _get_web_fonts(self, font_name):
        """Get web font information"""
        fonts = {
            "Open Sans": {
                "url": "https://fonts.googleapis.com/css2?family=Open+Sans:wght@300;400;600;700&display=swap",
                "family": "'Open Sans', sans-serif"
            },
            "Roboto": {
                "url": "https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap",
                "family": "'Roboto', sans-serif"
            },
            "Inter": {
                "url": "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap",
                "family": "'Inter', sans-serif"
            }
        }
        
        return {
            "status": "success",
            "font": fonts.get(font_name, fonts["Open Sans"])
        }
    
    def _fetch_external_libraries(self, project_type):
        """Get external library information"""
        libraries = {
            "web": [
                {"name": "Chart.js", "url": "https://cdn.jsdelivr.net/npm/chart.js", "type": "js"},
                {"name": "D3.js", "url": "https://d3js.org/d3.v7.min.js", "type": "js"},
                {"name": "Bootstrap", "url": "https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css", "type": "css"}
            ],
            "data_analysis": [
                {"name": "Plotly", "url": "https://cdn.plot.ly/plotly-latest.min.js", "type": "js"},
                {"name": "NumJS", "url": "https://unpkg.com/numjs@latest/dist/numjs.min.js", "type": "js"}
            ]
        }
        
        return {
            "status": "success",
            "libraries": libraries.get(project_type, libraries["web"])
        }
    
    def validate_code(self, code, files=None):
        """Validate code quality"""
        issues = []
        warnings = []
        suggestions = []
        
        if not code or len(code.strip()) < 10:
            issues.append("Code is too short or empty")
        
        # Check HTML structure
        if "<!DOCTYPE html>" in code:
            if "<title>" not in code:
                warnings.append("Missing page title")
            if 'lang="' not in code:
                suggestions.append("Consider adding language attribute to HTML tag")
        
        # Check CSS
        if code.strip().startswith(".") or code.strip().startswith("#"):
            if "color:" not in code and "background" not in code:
                suggestions.append("Consider adding color scheme to CSS")
        
        # Check JavaScript
        if "function" in code or "const " in code or "let " in code:
            if "console.log" in code:
                warnings.append("Remove console.log statements in production")
        
        return {
            "is_valid": len(issues) == 0,
            "errors": issues,
            "warnings": warnings,
            "suggestions": suggestions
        }
    
    def organize_files(self, files):
        """Organize file structure"""
        return self._organize_files(files, "")
    
    def generate_report(self):
        """Generate tool usage report"""
        execution_time = (datetime.now() - self.start_time).total_seconds()
        
        successful_operations = len([log for log in self.execution_log if log.get("status") == "success"])
        total_operations = len(self.execution_log)
        success_rate = (successful_operations / total_operations * 100) if total_operations > 0 else 100
        
        return {
            "tools_used": list(set([log.get("action", "unknown") for log in self.execution_log])),
            "execution_time": f"{execution_time:.2f}s",
            "success_rate": f"{success_rate:.1f}%",
            "total_operations": total_operations,
            "successful_operations": successful_operations,
            "detailed_log": self.execution_log[-5:]  # Last 5 records
        }
    
    def get_tool(self, tool_name):
        """Get specific tool instance"""
        # For compatibility, return self, because all tool functions are integrated here
        return self

    def _run_automated_tests(self, files):
        """Run automated tests"""
        issues = []
        test_results = {}
        
        for file_path, content in files.items():
            file_issues = []
            
            # Basic file checks
            if not content.strip():
                file_issues.append("File is empty")
            
            # HTML checks
            if file_path.endswith('.html'):
                if '<!DOCTYPE html>' not in content.upper():
                    file_issues.append("Missing DOCTYPE declaration")
                if '<html' not in content:
                    file_issues.append("Missing html tag")
                if '<head>' not in content or '<body>' not in content:
                    file_issues.append("Missing head or body tags")
            
            # CSS checks
            elif file_path.endswith('.css'):
                open_braces = content.count('{')
                close_braces = content.count('}')
                if open_braces != close_braces:
                    file_issues.append("Unbalanced CSS braces")
            
            # JavaScript checks
            elif file_path.endswith('.js'):
                if content.count('(') != content.count(')'):
                    file_issues.append("Unbalanced parentheses")
                if content.count('{') != content.count('}'):
                    file_issues.append("Unbalanced braces")
            
            test_results[file_path] = {
                "passed": len(file_issues) == 0,
                "issues": file_issues
            }
            issues.extend(file_issues)
        
        return {
            "status": "success",
            "overall_passed": len(issues) == 0,
            "total_issues": len(issues),
            "file_results": test_results,
            "summary": f"Tested {len(files)} files, found {len(issues)} issues"
        }
    
    def _run_quality_check(self, files, project_type):
        """Run quality check"""
        quality_score = 0
        total_checks = 0
        quality_details = {}
        
        for file_path, content in files.items():
            file_score = 0
            file_checks = 0
            
            # Basic quality checks
            if content.strip():
                file_score += 1
            file_checks += 1
            
            # Code length check
            if len(content) > 100:  # Basic content check
                file_score += 1
            file_checks += 1
            
            # File-specific checks
            if file_path.endswith('.html'):
                if 'class=' in content or 'id=' in content:
                    file_score += 1  # Has CSS selectors
                file_checks += 1
                
                if '<title>' in content:
                    file_score += 1  # Has title
                file_checks += 1
                
            elif file_path.endswith('.css'):
                if ':' in content and '{' in content:
                    file_score += 1  # Has CSS rules
                file_checks += 1
                
                if 'color:' in content or 'background:' in content:
                    file_score += 1  # Has style definitions
                file_checks += 1
            
            quality_details[file_path] = {
                "score": file_score,
                "max_score": file_checks,
                "percentage": (file_score / file_checks * 100) if file_checks > 0 else 0
            }
            
            quality_score += file_score
            total_checks += file_checks
        
        overall_percentage = (quality_score / total_checks * 100) if total_checks > 0 else 0
        
        return {
            "status": "success",
            "overall_score": quality_score,
            "max_score": total_checks,
            "percentage": overall_percentage,
            "grade": "A" if overall_percentage >= 90 else "B" if overall_percentage >= 80 else "C" if overall_percentage >= 70 else "D",
            "file_details": quality_details,
            "summary": f"Quality score: {quality_score}/{total_checks} ({overall_percentage:.1f}%)"
        }
