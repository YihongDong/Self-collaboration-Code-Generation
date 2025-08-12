"""
Enhanced Tool System for Project-Level Code Generation
Provides powerful tool invocation capabilities to enhance project code generation quality and functionality
"""

import os
import re
import json
import subprocess
import requests
import ast
import time
from typing import Dict, List, Any, Optional, Tuple
from abc import ABC, abstractmethod
from pathlib import Path


class BaseTool(ABC):
    """Base tool class"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.usage_count = 0
        self.last_used = None
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Dict[str, Any]:
        """Execute tool function"""
        pass
    
    def log_usage(self):
        """Log tool usage"""
        self.usage_count += 1
        self.last_used = time.time()
    
    def get_info(self) -> Dict[str, Any]:
        """Get tool information"""
        return {
            "name": self.name,
            "description": self.description,
            "usage_count": self.usage_count,
            "last_used": self.last_used
        }


class CodeAnalyzer(BaseTool):
    """Code analysis tool"""
    
    def __init__(self):
        super().__init__(
            "code_analyzer",
            "Analyze code quality, complexity and potential issues"
        )
    
    def execute(self, code: str, language: str = "javascript") -> Dict[str, Any]:
        """Analyze code quality"""
        self.log_usage()
        
        result = {
            "language": language,
            "metrics": {},
            "issues": [],
            "suggestions": []
        }
        
        if language.lower() in ["javascript", "js"]:
            result.update(self._analyze_javascript(code))
        elif language.lower() in ["python", "py"]:
            result.update(self._analyze_python(code))
        elif language.lower() in ["html"]:
            result.update(self._analyze_html(code))
        elif language.lower() in ["css"]:
            result.update(self._analyze_css(code))
        
        return result
    
    def _analyze_javascript(self, code: str) -> Dict[str, Any]:
        """Analyze JavaScript code"""
        metrics = {
            "lines_of_code": len(code.splitlines()),
            "functions_count": len(re.findall(r'function\s+\w+|=>\s*{|\w+\s*:\s*function', code)),
            "classes_count": len(re.findall(r'class\s+\w+', code)),
            "complexity_score": self._calculate_complexity(code)
        }
        
        issues = []
        suggestions = []
        
        # Check common issues
        if 'var ' in code:
            issues.append({
                "type": "style",
                "message": "Recommend using 'let' or 'const' instead of 'var'",
                "severity": "warning"
            })
            suggestions.append("Use modern ES6+ syntax, replace var with let/const")
        
        if '==' in code and '===' not in code:
            issues.append({
                "type": "quality",
                "message": "Recommend using strict equality '===' instead of '=='",
                "severity": "warning"
            })
        
        if 'console.log' in code:
            issues.append({
                "type": "production",
                "message": "Should remove console.log in production code",
                "severity": "info"
            })
        
        # Check for modern features usage
        modern_features = ['async', 'await', '=>', 'const', 'let', 'destructuring']
        used_features = [f for f in modern_features if f in code]
        if used_features:
            suggestions.append(f"Uses modern JavaScript features: {', '.join(used_features)}")
        
        return {
            "metrics": metrics,
            "issues": issues,
            "suggestions": suggestions
        }
    
    def _analyze_python(self, code: str) -> Dict[str, Any]:
        """Analyze Python code"""
        try:
            tree = ast.parse(code)
            
            metrics = {
                "lines_of_code": len(code.splitlines()),
                "functions_count": len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]),
                "classes_count": len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]),
                "imports_count": len([n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))])
            }
            
            return {
                "metrics": metrics,
                "issues": [],
                "suggestions": ["Python code syntax is correct"]
            }
        except SyntaxError as e:
            return {
                "metrics": {"lines_of_code": len(code.splitlines())},
                "issues": [{
                    "type": "syntax",
                    "message": f"Syntax error: {str(e)}",
                    "severity": "error"
                }],
                "suggestions": ["Fix syntax errors"]
            }
    
    def _analyze_html(self, code: str) -> Dict[str, Any]:
        """Analyze HTML code"""
        metrics = {
            "lines_of_code": len(code.splitlines()),
            "elements_count": len(re.findall(r'<\w+', code)),
            "semantic_elements": len(re.findall(r'<(header|nav|main|section|article|aside|footer)', code)),
            "images_count": len(re.findall(r'<img', code))
        }
        
        issues = []
        suggestions = []
        
        # Check semantics
        if metrics["semantic_elements"] > 0:
            suggestions.append("Uses HTML5 semantic elements")
        else:
            issues.append({
                "type": "accessibility",
                "message": "Recommend using HTML5 semantic elements",
                "severity": "warning"
            })
        
        # Check accessibility
        if 'alt=' not in code and '<img' in code:
            issues.append({
                "type": "accessibility",
                "message": "Images missing alt attributes",
                "severity": "warning"
            })
        
        if 'aria-' in code:
            suggestions.append("Uses ARIA attributes for better accessibility")
        
        return {
            "metrics": metrics,
            "issues": issues,
            "suggestions": suggestions
        }
    
    def _analyze_css(self, code: str) -> Dict[str, Any]:
        """Analyze CSS code"""
        metrics = {
            "lines_of_code": len(code.splitlines()),
            "rules_count": len(re.findall(r'{[^}]*}', code)),
            "custom_properties": len(re.findall(r'--[\w-]+:', code)),
            "media_queries": len(re.findall(r'@media', code))
        }
        
        issues = []
        suggestions = []
        
        # Check modern CSS features
        if metrics["custom_properties"] > 0:
            suggestions.append("Uses CSS custom properties (variables)")
        
        if 'grid' in code or 'flexbox' in code:
            suggestions.append("Uses modern CSS layout (Grid/Flexbox)")
        
        if metrics["media_queries"] > 0:
            suggestions.append("Implements responsive design")
        
        return {
            "metrics": metrics,
            "issues": issues,
            "suggestions": suggestions
        }
    
    def _calculate_complexity(self, code: str) -> int:
        """Calculate code complexity"""
        complexity = 1  # Base complexity
        
        # Add complexity for decision points
        decision_points = ['if', 'else', 'while', 'for', 'case', 'catch', '&&', '||', '?']
        for point in decision_points:
            complexity += len(re.findall(rf'\b{point}\b', code))
        
        return complexity


class FileManager(BaseTool):
    """File system management tool"""
    
    def __init__(self):
        super().__init__(
            "file_manager",
            "Manage project file structure and operations"
        )
    
    def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute file operations"""
        self.log_usage()
        
        try:
            if action == "create_structure":
                return self._create_project_structure(kwargs.get("structure", {}))
            elif action == "validate_structure":
                return self._validate_structure(kwargs.get("path", "."))
            elif action == "optimize_structure":
                return self._optimize_structure(kwargs.get("files", {}))
            elif action == "generate_tree":
                return self._generate_directory_tree(kwargs.get("path", "."))
            else:
                return {"error": f"Unknown operation: {action}"}
        except Exception as e:
            return {"error": str(e)}
    
    def _create_project_structure(self, structure: Dict[str, str]) -> Dict[str, Any]:
        """Create project file structure"""
        created_dirs = []
        created_files = []
        
        for path, content in structure.items():
            full_path = Path(path)
            
            # Create directories
            if full_path.suffix == "":  # Directory
                full_path.mkdir(parents=True, exist_ok=True)
                created_dirs.append(str(full_path))
            else:  # File
                full_path.parent.mkdir(parents=True, exist_ok=True)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content if content else "")
                created_files.append(str(full_path))
        
        return {
            "success": True,
            "created_directories": created_dirs,
            "created_files": created_files
        }
    
    def _validate_structure(self, path: str) -> Dict[str, Any]:
        """Validate project structure"""
        path_obj = Path(path)
        if not path_obj.exists():
            return {"error": "Path does not exist"}
        
        structure_info = {
            "is_valid_project": False,
            "has_index_html": False,
            "has_css_folder": False,
            "has_js_folder": False,
            "has_manifest": False,
            "suggestions": []
        }
        
        # Check key files and directories
        files_and_dirs = list(path_obj.iterdir())
        file_names = [f.name for f in files_and_dirs]
        
        structure_info["has_index_html"] = "index.html" in file_names
        structure_info["has_css_folder"] = any(f.name == "css" and f.is_dir() for f in files_and_dirs)
        structure_info["has_js_folder"] = any(f.name == "js" and f.is_dir() for f in files_and_dirs)
        structure_info["has_manifest"] = "manifest.json" in file_names
        
        # Generate suggestions
        if not structure_info["has_index_html"]:
            structure_info["suggestions"].append("Recommend adding index.html as the main page")
        
        if not structure_info["has_css_folder"]:
            structure_info["suggestions"].append("Recommend creating css folder to organize style files")
        
        if not structure_info["has_js_folder"]:
            structure_info["suggestions"].append("Recommend creating js folder to organize script files")
        
        if not structure_info["has_manifest"]:
            structure_info["suggestions"].append("Recommend adding manifest.json for PWA support")
        
        structure_info["is_valid_project"] = all([
            structure_info["has_index_html"],
            structure_info["has_css_folder"],
            structure_info["has_js_folder"]
        ])
        
        return structure_info
    
    def _optimize_structure(self, files: Dict[str, str]) -> Dict[str, Any]:
        """Optimize file structure"""
        optimized_structure = {}
        recommendations = []
        
        # Reorganize by file type
        for file_path, content in files.items():
            path_obj = Path(file_path)
            extension = path_obj.suffix.lower()
            
            if extension == '.html':
                if path_obj.name == 'index.html':
                    optimized_structure['index.html'] = content
                else:
                    optimized_structure[f'pages/{path_obj.name}'] = content
            elif extension == '.css':
                optimized_structure[f'css/{path_obj.name}'] = content
            elif extension in ['.js', '.ts']:
                optimized_structure[f'js/{path_obj.name}'] = content
            elif extension in ['.png', '.jpg', '.jpeg', '.svg', '.ico']:
                optimized_structure[f'assets/images/{path_obj.name}'] = content
            elif extension == '.json':
                if 'manifest' in path_obj.name:
                    optimized_structure['manifest.json'] = content
                else:
                    optimized_structure[f'data/{path_obj.name}'] = content
            else:
                optimized_structure[file_path] = content
        
        # Generate optimization suggestions
        if len([f for f in files.keys() if f.endswith('.css')]) > 3:
            recommendations.append("Consider splitting CSS files further into main.css, components.css, utilities.css")
        
        if len([f for f in files.keys() if f.endswith('.js')]) > 5:
            recommendations.append("Consider using modular JavaScript, split files by functionality")
        
        return {
            "optimized_structure": optimized_structure,
            "recommendations": recommendations,
            "original_files_count": len(files),
            "optimized_files_count": len(optimized_structure)
        }
    
    def _generate_directory_tree(self, path: str) -> Dict[str, Any]:
        """Generate directory tree"""
        def build_tree(dir_path: Path, prefix: str = "") -> List[str]:
            tree_lines = []
            if not dir_path.is_dir():
                return tree_lines
            
            items = sorted(dir_path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
            
            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                current_prefix = "└── " if is_last else "├── "
                tree_lines.append(f"{prefix}{current_prefix}{item.name}")
                
                if item.is_dir():
                    extension_prefix = "    " if is_last else "│   "
                    tree_lines.extend(build_tree(item, prefix + extension_prefix))
            
            return tree_lines
        
        path_obj = Path(path)
        if not path_obj.exists():
            return {"error": "Path does not exist"}
        
        tree = build_tree(path_obj)
        
        return {
            "tree": tree,
            "tree_string": "\n".join([path_obj.name + "/"] + tree)
        }


class QualityChecker(BaseTool):
    """Code quality checking tool"""
    
    def __init__(self):
        super().__init__(
            "quality_checker",
            "Check code quality, security and best practices"
        )
    
    def execute(self, files: Dict[str, str], project_type: str = "web_visualization") -> Dict[str, Any]:
        """Execute quality check"""
        self.log_usage()
        
        results = {
            "overall_score": 0,
            "file_scores": {},
            "security_issues": [],
            "performance_issues": [],
            "best_practices": [],
            "accessibility_score": 0,
            "recommendations": []
        }
        
        total_score = 0
        file_count = 0
        
        for file_path, content in files.items():
            file_result = self._check_file_quality(file_path, content)
            results["file_scores"][file_path] = file_result
            total_score += file_result.get("score", 0)
            file_count += 1
            
            # Collect various issues
            results["security_issues"].extend(file_result.get("security_issues", []))
            results["performance_issues"].extend(file_result.get("performance_issues", []))
            results["best_practices"].extend(file_result.get("best_practices", []))
        
        # Calculate overall score
        results["overall_score"] = total_score / file_count if file_count > 0 else 0
        
        # Calculate accessibility score
        results["accessibility_score"] = self._calculate_accessibility_score(files)
        
        # Generate recommendations
        results["recommendations"] = self._generate_quality_recommendations(results)
        
        return results
    
    def _check_file_quality(self, file_path: str, content: str) -> Dict[str, Any]:
        """Check individual file quality"""
        path_obj = Path(file_path)
        extension = path_obj.suffix.lower()
        
        if extension == '.html':
            return self._check_html_quality(content)
        elif extension == '.css':
            return self._check_css_quality(content)
        elif extension in ['.js', '.ts']:
            return self._check_js_quality(content)
        else:
            return {"score": 70, "issues": [], "suggestions": []}
    
    def _check_html_quality(self, content: str) -> Dict[str, Any]:
        """Check HTML quality"""
        score = 100
        issues = []
        best_practices = []
        security_issues = []
        performance_issues = []
        
        # Check DOCTYPE
        if '<!DOCTYPE html>' not in content:
            score -= 10
            issues.append("Missing HTML5 DOCTYPE declaration")
        else:
            best_practices.append("Uses HTML5 DOCTYPE")
        
        # Check language declaration
        if 'lang=' not in content:
            score -= 5
            issues.append("Missing language declaration (lang attribute)")
        
        # Check meta viewport
        if 'viewport' not in content:
            score -= 10
            issues.append("Missing viewport meta tag")
        
        # Check semantics
        semantic_elements = ['header', 'nav', 'main', 'section', 'article', 'aside', 'footer']
        used_semantic = [elem for elem in semantic_elements if f'<{elem}' in content]
        if len(used_semantic) >= 3:
            best_practices.append("Uses semantic HTML5 elements")
        elif len(used_semantic) > 0:
            best_practices.append(f"Uses some semantic elements: {', '.join(used_semantic)}")
        else:
            score -= 15
            issues.append("Recommend using semantic HTML5 elements")
        
        # Check accessibility
        if 'aria-' in content:
            best_practices.append("Uses ARIA attributes")
            score += 5
        
        if 'alt=' in content:
            best_practices.append("Images include alt attributes")
        elif '<img' in content:
            score -= 10
            issues.append("Images missing alt attributes")
        
        # Check security
        if 'javascript:' in content:
            security_issues.append("Avoid using javascript: protocol")
            score -= 20
        
        # Check performance
        if 'preload' in content or 'preconnect' in content:
            performance_issues.append("Uses resource preloading optimization")
            score += 5
        
        return {
            "score": max(0, score),
            "issues": issues,
            "best_practices": best_practices,
            "security_issues": security_issues,
            "performance_issues": performance_issues
        }
    
    def _check_css_quality(self, content: str) -> Dict[str, Any]:
        """Check CSS quality"""
        score = 100
        issues = []
        best_practices = []
        performance_issues = []
        
        # Check CSS custom properties
        if '--' in content and ':root' in content:
            best_practices.append("Uses CSS custom properties (variables)")
            score += 10
        
        # Check modern layout
        if 'display: grid' in content or 'display: flex' in content:
            best_practices.append("Uses modern CSS layout")
            score += 5
        
        # Check responsive design
        if '@media' in content:
            best_practices.append("Implements responsive design")
            score += 10
        
        # Check performance issues
        if '*' in content and 'box-sizing' in content:
            performance_issues.append("Uses universal selector for box-sizing reset")
        
        # Check maintainability
        if len(content.splitlines()) > 500:
            issues.append("CSS file too long, recommend splitting into multiple files")
            score -= 10
        
        return {
            "score": max(0, score),
            "issues": issues,
            "best_practices": best_practices,
            "performance_issues": performance_issues
        }
    
    def _check_js_quality(self, content: str) -> Dict[str, Any]:
        """Check JavaScript quality"""
        score = 100
        issues = []
        best_practices = []
        security_issues = []
        performance_issues = []
        
        # Check modern JavaScript features
        modern_features = ['const ', 'let ', '=>', 'async ', 'await ', '...']
        used_features = [f.strip() for f in modern_features if f in content]
        if len(used_features) >= 3:
            best_practices.append(f"Uses modern ES6+ features: {', '.join(used_features)}")
            score += 10
        
        # Check bad practices
        if 'var ' in content:
            issues.append("Recommend using let/const instead of var")
            score -= 5
        
        if 'eval(' in content:
            security_issues.append("Avoid using eval() function")
            score -= 20
        
        if '==' in content and '===' not in content:
            issues.append("Recommend using strict equality operator (===)")
            score -= 5
        
        # Check error handling
        if 'try' in content and 'catch' in content:
            best_practices.append("Implements error handling")
            score += 5
        
        # Check performance
        if 'addEventListener' in content:
            best_practices.append("Uses event listeners")
        
        if 'querySelector' in content:
            best_practices.append("Uses modern DOM query methods")
        
        return {
            "score": max(0, score),
            "issues": issues,
            "best_practices": best_practices,
            "security_issues": security_issues,
            "performance_issues": performance_issues
        }
    
    def _calculate_accessibility_score(self, files: Dict[str, str]) -> int:
        """Calculate accessibility score"""
        score = 0
        total_checks = 0
        
        for file_path, content in files.items():
            if file_path.endswith('.html'):
                total_checks += 10
                
                # ARIA attributes
                if 'aria-' in content:
                    score += 2
                
                # Semantic elements
                semantic_count = len(re.findall(r'<(header|nav|main|section|article|aside|footer)', content))
                if semantic_count >= 3:
                    score += 2
                
                # Image alt attributes
                if '<img' in content:
                    if 'alt=' in content:
                        score += 1
                else:
                    score += 1  # No images also passes
                
                # Form labels
                if '<input' in content:
                    if '<label' in content:
                        score += 1
                else:
                    score += 1
                
                # Skip links
                if 'skip' in content.lower():
                    score += 1
                
                # Role attributes
                if 'role=' in content:
                    score += 1
                
                # Color contrast indication
                if 'color:' in content and '#' in content:
                    score += 1  # Simplified check
                
                # Keyboard navigation
                if 'tabindex' in content:
                    score += 1
        
        return int((score / max(total_checks, 1)) * 100) if total_checks > 0 else 80
    
    def _generate_quality_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate quality improvement recommendations"""
        recommendations = []
        
        overall_score = results["overall_score"]
        
        if overall_score < 70:
            recommendations.append("Overall code quality needs improvement, focus on basic standards")
        elif overall_score < 85:
            recommendations.append("Code quality is good, can further optimize performance and accessibility")
        else:
            recommendations.append("Code quality is excellent, continue maintaining best practices")
        
        # Security recommendations
        if results["security_issues"]:
            recommendations.append("Fix discovered security issues to ensure application security")
        
        # Performance recommendations
        if results["performance_issues"]:
            recommendations.append("Optimize performance-related issues to improve user experience")
        
        # Accessibility recommendations
        accessibility_score = results["accessibility_score"]
        if accessibility_score < 70:
            recommendations.append("Significantly improve accessibility, add ARIA attributes and semantic tags")
        elif accessibility_score < 90:
            recommendations.append("Further improve accessibility features")
        else:
            recommendations.append("Excellent accessibility performance")
        
        return recommendations


class ToolOrchestrator:
    """Tool orchestrator - manage and coordinate all tool usage"""
    
    def __init__(self):
        self.tools = {
            "code_analyzer": CodeAnalyzer(),
            "file_manager": FileManager(),
            "quality_checker": QualityChecker()
        }
        self.execution_history = []
    
    def get_available_tools(self) -> Dict[str, str]:
        """Get available tools list"""
        return {name: tool.description for name, tool in self.tools.items()}
    
    def get_tool(self, tool_name: str):
        """Get specified tool instance"""
        return self.tools.get(tool_name)
    
    def execute_tool(self, tool_name: str, *args, **kwargs) -> Dict[str, Any]:
        """Execute specified tool"""
        if tool_name not in self.tools:
            return {"error": f"Tool {tool_name} does not exist"}
        
        try:
            result = self.tools[tool_name].execute(*args, **kwargs)
            
            # Record execution history
            self.execution_history.append({
                "tool": tool_name,
                "timestamp": time.time(),
                "args": args,
                "kwargs": kwargs,
                "success": "error" not in result
            })
            
            return result
        except Exception as e:
            error_result = {"error": f"Tool execution failed: {str(e)}"}
            self.execution_history.append({
                "tool": tool_name,
                "timestamp": time.time(),
                "args": args,
                "kwargs": kwargs,
                "success": False,
                "error": str(e)
            })
            return error_result
    
    def get_tool_usage_stats(self) -> Dict[str, Any]:
        """Get tool usage statistics"""
        stats = {}
        for name, tool in self.tools.items():
            stats[name] = tool.get_info()
        
        return {
            "tools": stats,
            "total_executions": len(self.execution_history),
            "recent_executions": self.execution_history[-10:]  # Last 10 executions
        }
    
    def recommend_tools(self, context: str) -> List[str]:
        """Recommend suitable tools based on context"""
        recommendations = []
        
        context_lower = context.lower()
        
        if any(keyword in context_lower for keyword in ["analyze", "check", "quality", "complexity"]):
            recommendations.append("code_analyzer")
        
        if any(keyword in context_lower for keyword in ["file", "structure", "directory", "organize"]):
            recommendations.append("file_manager")
        
        if any(keyword in context_lower for keyword in ["quality", "security", "performance", "best practices"]):
            recommendations.append("quality_checker")
        
        return recommendations if recommendations else ["code_analyzer", "file_manager", "quality_checker"]
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate tool usage report"""
        report = {
            "timestamp": time.time(),
            "tools_stats": self.get_tool_usage_stats(),
            "execution_summary": {
                "total_executions": len(self.execution_history),
                "successful_executions": len([h for h in self.execution_history if h["success"]]),
                "failed_executions": len([h for h in self.execution_history if not h["success"]]),
            },
            "most_used_tools": self._get_most_used_tools(),
            "recommendations": self._generate_usage_recommendations()
        }
        return report
    
    def _get_most_used_tools(self) -> List[Tuple[str, int]]:
        """Get most used tools"""
        usage_count = {}
        for tool_name, tool in self.tools.items():
            usage_count[tool_name] = tool.usage_count
        return sorted(usage_count.items(), key=lambda x: x[1], reverse=True)
    
    def _generate_usage_recommendations(self) -> List[str]:
        """Generate usage recommendations"""
        recommendations = []
        total_executions = len(self.execution_history)
        
        if total_executions > 0:
            successful_rate = len([h for h in self.execution_history if h["success"]]) / total_executions
            if successful_rate < 0.8:
                recommendations.append("Tool execution success rate is low, recommend checking input parameters")
            else:
                recommendations.append("Tool usage is effective, continue maintaining")
        
        most_used = self._get_most_used_tools()
        if most_used and most_used[0][1] > total_executions * 0.6:
            recommendations.append(f"Over-reliance on {most_used[0][0]} tool, recommend balanced use of other tools")
        
        return recommendations


# Global tool orchestrator instance
global_tool_orchestrator = ToolOrchestrator()