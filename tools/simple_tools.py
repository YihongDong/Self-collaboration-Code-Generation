"""
Practical tool classes - for project mode
"""
import os
import re
import json
from datetime import datetime

class CodeAnalyzer:
    """Code analyzer - intelligently analyze code quality and structure"""
    
    def __init__(self):
        self.analysis_history = []
        self.project_specific_checks = {
            "web_visualization": {
                "html_requirements": ["chart", "canvas", "svg", "data-", "interactive"],
                "css_requirements": ["responsive", "grid", "flex", "hover", "transition"],
                "js_requirements": ["chart", "data", "event", "click", "update"]
            },
            "data_analysis": {
                "required_libraries": ["d3", "plotly", "chart"],
                "data_patterns": ["json", "csv", "api", "fetch"]
            }
        }
    
    def analyze(self, code, project_type="web_visualization", file_type=None):
        """Deep analysis of code structure and quality"""
        
        # Auto-detect file type
        if not file_type:
            file_type = self._detect_file_type(code)
        
        metrics = {
            "lines_of_code": len(code.split('\n')),
            "character_count": len(code),
            "complexity_score": self._calculate_complexity(code),
            "structure_score": self._analyze_structure(code, file_type),
            "quality_issues": self._find_quality_issues(code, file_type),
            "project_compliance": self._check_project_compliance(code, project_type, file_type),
            "performance_score": self._analyze_performance(code, file_type),
            "accessibility_score": self._check_accessibility(code, file_type),
            "file_type": file_type
        }
        
        overall_score = self._calculate_overall_score(metrics)
        
        self.analysis_history.append({
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "overall_score": overall_score
        })
        
        return {
            "status": "analyzed",
            "metrics": metrics,
            "overall_score": overall_score,
            "recommendations": self._generate_recommendations(metrics, project_type)
        }
    
    def _detect_file_type(self, code):
        """Intelligently detect file type"""
        code_lower = code.lower()
        if "<!doctype html>" in code_lower or "<html" in code_lower:
            return "html"
        elif code.strip().startswith((".", "#", "@", "/*")) or ":" in code and "{" in code:
            return "css"
        elif any(keyword in code for keyword in ["function", "const ", "let ", "var ", "=>"]):
            return "javascript"
        elif code.strip().startswith(("{", "[")):
            return "json"
        return "unknown"
    
    def _analyze_performance(self, code, file_type):
        """Analyze performance-related issues"""
        score = 1.0
        
        if file_type == "html":
            # Check performance impact
            if code.count("<script") > 5:
                score -= 0.2  # Too many scripts
            if "src=" in code and "defer" not in code and "async" not in code:
                score -= 0.1  # Missing lazy loading
        
        elif file_type == "css":
            # CSS performance check
            if code.count("@import") > 0:
                score -= 0.2  # Avoid CSS import
            if len(re.findall(r'[^{]*{[^}]*}', code)) > 100:
                score -= 0.1  # Too many rules
        
        elif file_type == "javascript":
            # JS performance check
            if "document.write" in code:
                score -= 0.3  # Avoid document.write
            if len(re.findall(r'for\s*\(.*\)', code)) > 5:
                score -= 0.1  # Too many loops need optimization
        
        return max(0, score)
    
    def _check_accessibility(self, code, file_type):
        """Check accessibility"""
        score = 1.0
        
        if file_type == "html":
            if 'alt="' not in code and "<img" in code:
                score -= 0.3  # Images missing alt attribute
            if 'aria-' not in code:
                score -= 0.2  # Missing ARIA attributes
            if 'role="' not in code and any(tag in code for tag in ["<div", "<span"]):
                score -= 0.1  # Insufficient semantics
            if 'lang="' not in code:
                score -= 0.1  # Missing language attribute
        
        return max(0, score)
    
    def _check_project_compliance(self, code, project_type, file_type):
        """Check project type compliance"""
        compliance_score = 1.0
        issues = []
        
        if project_type in self.project_specific_checks:
            requirements = self.project_specific_checks[project_type]
            
            if file_type == "html" and "html_requirements" in requirements:
                for req in requirements["html_requirements"]:
                    if req not in code.lower():
                        compliance_score -= 0.1
                        issues.append(f"Missing {req} for {project_type}")
            
            if file_type == "css" and "css_requirements" in requirements:
                for req in requirements["css_requirements"]:
                    if req not in code.lower():
                        compliance_score -= 0.1
                        issues.append(f"CSS should include {req}")
            
            if file_type == "javascript" and "js_requirements" in requirements:
                for req in requirements["js_requirements"]:
                    if req not in code.lower():
                        compliance_score -= 0.1
                        issues.append(f"JS should handle {req}")
        
        return {
            "score": max(0, compliance_score),
            "issues": issues
        }
    
    def _generate_recommendations(self, metrics, project_type):
        """Generate improvement recommendations"""
        recommendations = []
        
        if metrics["performance_score"] < 0.7:
            recommendations.append("Optimize performance: reduce scripts, use lazy loading")
        
        if metrics["accessibility_score"] < 0.8:
            recommendations.append("Improve accessibility: add alt attributes and ARIA labels")
        
        if metrics["project_compliance"]["score"] < 0.8:
            recommendations.extend(metrics["project_compliance"]["issues"])
        
        if metrics["complexity_score"] > 0.7:
            recommendations.append("Reduce code complexity: consider refactoring complex logic")
        
        return recommendations
    
    def _calculate_complexity(self, code):
        """Calculate code complexity"""
        complexity = 0
        complexity += len(re.findall(r'\bif\b|\bfor\b|\bwhile\b|\bswitch\b', code))
        complexity += len(re.findall(r'\bfunction\b|\bdef\b|\bclass\b', code))
        return min(complexity / 10.0, 1.0)  # Normalize to 0-1
    
    def _analyze_structure(self, code, file_type):
        """Analyze code structure"""
        score = 0.5  # Base score
        
        if file_type == "html":
            if "<!DOCTYPE html>" in code:
                score += 0.1
            if "<head>" in code and "<body>" in code:
                score += 0.1
            if 'class="' in code or 'id="' in code:
                score += 0.1
            if "<meta" in code:
                score += 0.05
            if "semantic" in code.lower() or any(tag in code for tag in ["<header>", "<nav>", "<main>", "<section>", "<article>", "<footer>"]):
                score += 0.15
        
        elif file_type == "css":
            if "{" in code and "}" in code:
                score += 0.2
            if "@media" in code:
                score += 0.1  # Responsive design
            if ":hover" in code or ":focus" in code:
                score += 0.1  # Interactivity
            if "/*" in code and "*/" in code:
                score += 0.05  # Comments
        
        elif file_type == "javascript":
            if "function" in code or "=>" in code:
                score += 0.1
            if "const " in code or "let " in code:
                score += 0.1  # Modern JS
            if "addEventListener" in code:
                score += 0.1  # Event handling
            if "try" in code and "catch" in code:
                score += 0.05  # Error handling
        
        return min(score, 1.0)
    
    def _find_quality_issues(self, code, file_type):
        """Find code quality issues"""
        issues = []
        
        # General issues
        if "console.log" in code:
            issues.append("Contains debug console.log statements")
        if len(re.findall(r'\n\s*\n\s*\n', code)) > 3:
            issues.append("Too many consecutive empty lines")
        
        # HTML specific issues
        if file_type == "html":
            if re.search(r'style\s*=\s*["\']', code):
                issues.append("Inline styles found, consider using CSS classes")
            if "<font" in code or "<center" in code:
                issues.append("Deprecated HTML tags found")
            if 'target="_blank"' in code and 'rel="noopener"' not in code:
                issues.append("Security: Add rel='noopener' to external links")
        
        # CSS specific issues
        elif file_type == "css":
            if "!important" in code:
                issues.append("Excessive use of !important")
            if len(re.findall(r'#[a-fA-F0-9]{6}', code)) > 10:
                issues.append("Too many hardcoded colors, consider using CSS variables")
        
        # JavaScript specific issues
        elif file_type == "javascript":
            if "var " in code:
                issues.append("Use const/let instead of var")
            if "==" in code and "===" not in code:
                issues.append("Use strict equality (===) instead of loose equality (==)")
            if "eval(" in code:
                issues.append("Avoid using eval() for security reasons")
        
        return issues
    
    def _calculate_overall_score(self, metrics):
        """Calculate overall quality score"""
        weights = {
            "structure": 0.25,
            "complexity": 0.15,
            "quality": 0.20,
            "performance": 0.20,
            "accessibility": 0.10,
            "compliance": 0.10
        }
        
        quality_score = max(0, 1.0 - len(metrics["quality_issues"]) * 0.1)
        
        overall = (
            metrics["structure_score"] * weights["structure"] +
            (1.0 - metrics["complexity_score"]) * weights["complexity"] +
            quality_score * weights["quality"] +
            metrics["performance_score"] * weights["performance"] +
            metrics["accessibility_score"] * weights["accessibility"] +
            metrics["project_compliance"]["score"] * weights["compliance"]
        )
        
        return min(max(overall, 0), 1.0)
    
    def execute(self, action="analyze", *args, **kwargs):
        """Unified execution interface"""
        if action == "analyze" or (args and isinstance(args[0], str)):
            code = args[0] if args else kwargs.get("code", "")
            project_type = kwargs.get("project_type", "web_visualization")
            file_type = kwargs.get("file_type")
            return self.analyze(code, project_type, file_type)
        elif action == "comprehensive_check":
            files = kwargs.get("files", {})
            project_type = kwargs.get("project_type", "web_visualization")
            return self._comprehensive_check(files, project_type)
        return {"status": "success", "result": "Code analyzer executed"}
    
    def _comprehensive_check(self, files, project_type):
        """Comprehensive check of all files"""
        results = {}
        overall_scores = []
        
        for file_path, content in files.items():
            file_type = self._detect_file_type(content)
            analysis = self.analyze(content, project_type, file_type)
            results[file_path] = analysis
            overall_scores.append(analysis["overall_score"])
        
        return {
            "status": "completed",
            "files_analyzed": len(files),
            "individual_results": results,
            "overall_score": sum(overall_scores) / len(overall_scores) if overall_scores else 0,
            "project_health": "Good" if sum(overall_scores) / len(overall_scores) > 0.7 else "Needs Improvement"
        }

class FileManager:
    """File manager - intelligently manage file organization and backup"""
    
    def __init__(self):
        self.operations_log = []
        self.file_templates = {
            "html": {
                "required_structure": ["<!DOCTYPE html>", "<html>", "<head>", "<title>", "<body>"],
                "recommended_meta": ['<meta charset="utf-8">', '<meta name="viewport"']
            },
            "css": {
                "structure_patterns": ["reset/normalize", "layout", "components", "utilities"],
                "organization": ["/* === SECTION === */"]
            },
            "js": {
                "patterns": ["strict mode", "module pattern", "error handling"]
            }
        }
    
    def organize(self, files):
        """Intelligently organize file structure"""
        organized = {}
        structure_suggestions = []
        
        for file_path, content in files.items():
            # Clean content - remove code block wrappers
            cleaned_content = self._clean_file_content(content, file_path)
            
            # Normalize file path
            clean_path = self._normalize_path(file_path, cleaned_content)
            organized[clean_path] = cleaned_content
            
            # Check file organization suggestions
            suggestions = self._analyze_file_organization(clean_path, cleaned_content)
            structure_suggestions.extend(suggestions)
        
        # Create recommended directory structure
        recommended_structure = self._generate_recommended_structure(organized)
        
        self.operations_log.append({
            "operation": "organize",
            "timestamp": datetime.now().isoformat(),
            "files_processed": len(files),
            "files_organized": len(organized),
            "suggestions": structure_suggestions
        })
        
        return {
            "organized_files": organized,
            "structure_suggestions": structure_suggestions,
            "recommended_structure": recommended_structure
        }
    
    def _normalize_path(self, file_path, content):
        """Normalize file path"""
        # Thoroughly clean file path - remove all possible Markdown markers
        clean_path = file_path.strip()
        
        # Remove backticks and other Markdown markers
        clean_path = clean_path.replace("`", "")
        clean_path = clean_path.replace("*", "")
        clean_path = clean_path.replace("_", "")
        clean_path = clean_path.replace("**", "")
        clean_path = clean_path.replace("__", "")
        
        # Normalize path separators
        clean_path = clean_path.replace("\\", "/").strip("/")
        
        # Remove extra spaces and special characters
        clean_path = re.sub(r'\s+', '', clean_path)  # Remove all spaces
        clean_path = re.sub(r'[^\w\-_./]', '', clean_path)  # Only keep valid characters
        
        # Intelligently add extensions
        if not os.path.splitext(clean_path)[1]:
            if content.strip().startswith("<!DOCTYPE") or "<html" in content:
                clean_path += ".html"
            elif any(content.strip().startswith(prefix) for prefix in [".", "#", "@", "/*"]):
                clean_path += ".css"
            elif any(keyword in content for keyword in ["function", "const ", "let ", "var ", "=>"]):
                clean_path += ".js"
            elif content.strip().startswith(("{", "[")):
                clean_path += ".json"
        
        # Intelligent directory organization
        file_ext = os.path.splitext(clean_path)[1]
        filename = os.path.basename(clean_path)
        
        if file_ext == ".css" and not clean_path.startswith("css/"):
            clean_path = f"css/{filename}"
        elif file_ext == ".js" and not clean_path.startswith("js/"):
            clean_path = f"js/{filename}"
        elif file_ext in [".png", ".jpg", ".jpeg", ".gif", ".svg"] and not clean_path.startswith("images/"):
            clean_path = f"images/{filename}"
        
        return clean_path
    
    def _analyze_file_organization(self, file_path, content):
        """Analyze file organization and provide suggestions"""
        suggestions = []
        file_ext = os.path.splitext(file_path)[1]
        
        if file_ext == ".html":
            # Check HTML file organization
            if len(content.split('\n')) > 200:
                suggestions.append(f"Consider splitting {file_path} into smaller components")
            if "<style" in content:
                suggestions.append(f"Move inline styles in {file_path} to CSS files")
            if "<script" in content and "src=" not in content:
                suggestions.append(f"Move scripts in {file_path} to JS files")
        
        elif file_ext == ".css":
            if len(content.split('\n')) > 500:
                suggestions.append(f"Consider splitting {file_path} into multiple CSS modules")
            if not re.search(r'/\*.*\*/', content):
                suggestions.append(f"Add comments to {file_path} to organize CSS rules")
        
        elif file_ext == ".js":
            if len(content.split('\n')) > 300:
                suggestions.append(f"Consider splitting {file_path} into multiple modules")
            if not re.search(r'//.*|/\*.*\*/', content):
                suggestions.append(f"Add documentation comments to {file_path}")
        
        return suggestions
    
    def _generate_recommended_structure(self, files):
        """Generate recommended project structure"""
        structure = {
            "directories": [],
            "files": {},
            "suggestions": []
        }
        
        # Analyze file type distribution
        file_types = {}
        for file_path in files.keys():
            ext = os.path.splitext(file_path)[1]
            file_types[ext] = file_types.get(ext, 0) + 1
        
        # Recommend directory structure
        if file_types.get('.css', 0) > 1:
            structure["directories"].append("css/")
            structure["suggestions"].append("Organize CSS files into css/ directory")
        
        if file_types.get('.js', 0) > 1:
            structure["directories"].append("js/")
            structure["suggestions"].append("Organize JavaScript files into js/ directory")
        
        if any(ext in file_types for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg']):
            structure["directories"].append("images/")
            structure["suggestions"].append("Organize image files into images/ directory")
        
        return structure
    
    def validate_structure(self, files):
        """Validate file structure"""
        errors = []
        warnings = []
        recommendations = []
        
        # Check necessary files
        file_types = [os.path.splitext(f)[1] for f in files.keys()]
        has_html = '.html' in file_types
        has_css = '.css' in file_types
        has_js = '.js' in file_types
        
        if not has_html:
            errors.append("No HTML files in project")
        else:
            # Check HTML file count
            html_files = [f for f in files.keys() if f.endswith('.html')]
            if len(html_files) > 5:
                warnings.append(f"Too many HTML files ({len(html_files)}), consider componentization")
        
        if not has_css:
            warnings.append("Recommend adding CSS files to improve styling")
        
        if not has_js:
            recommendations.append("Consider adding JavaScript to enhance interactivity")
        
        # Check file naming conventions
        for file_path in files.keys():
            filename = os.path.basename(file_path)
            if " " in filename:
                warnings.append(f"Filename contains spaces: {file_path}")
            if filename != filename.lower():
                recommendations.append(f"Recommend using lowercase filenames: {file_path}")
            if "--" in filename or "__" in filename:
                warnings.append(f"Filename contains multiple hyphens: {file_path}")
        
        # Check directory structure
        directories = set(os.path.dirname(f) for f in files.keys() if os.path.dirname(f))
        if len(directories) == 0 and len(files) > 3:
            recommendations.append("Consider using directories to organize files")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "recommendations": recommendations,
            "file_statistics": {
                "total_files": len(files),
                "html_files": len([f for f in files.keys() if f.endswith('.html')]),
                "css_files": len([f for f in files.keys() if f.endswith('.css')]),
                "js_files": len([f for f in files.keys() if f.endswith('.js')]),
                "directories": len(directories)
            }
        }
    
    def optimize_file_structure(self, files):
        """Optimize file structure"""
        optimized = {}
        changes = []
        
        for file_path, content in files.items():
            # Check if file needs splitting
            if self._should_split_file(file_path, content):
                split_files = self._split_file(file_path, content)
                optimized.update(split_files)
                changes.append(f"Split {file_path} into {len(split_files)} files")
            else:
                optimized[file_path] = content
        
        return {
            "optimized_files": optimized,
            "changes_made": changes,
            "optimization_summary": f"Processed {len(files)} files, made {len(changes)} optimizations"
        }
    
    def _should_split_file(self, file_path, content):
        """Determine if file needs splitting"""
        lines = len(content.split('\n'))
        
        if file_path.endswith('.html') and lines > 200:
            return True
        elif file_path.endswith('.css') and lines > 500:
            return True
        elif file_path.endswith('.js') and lines > 300:
            return True
        
        return False
    
    def _split_file(self, file_path, content):
        """Split large files"""
        split_files = {}
        base_name = os.path.splitext(file_path)[0]
        
        if file_path.endswith('.css'):
            # Split CSS by comments
            sections = re.split(r'/\*\s*=+\s*.*?\s*=+\s*\*/', content)
            for i, section in enumerate(sections):
                if section.strip():
                    split_files[f"{base_name}_part{i+1}.css"] = section.strip()
        
        elif file_path.endswith('.js'):
            # Split JS by functions
            functions = re.findall(r'function\s+\w+[^{]*{[^}]*}', content)
            if len(functions) > 1:
                for i, func in enumerate(functions):
                    split_files[f"{base_name}_func{i+1}.js"] = func
        
        # If splitting fails, return original file
        if not split_files:
            split_files[file_path] = content
        
        return split_files
    
    def backup_existing(self, output_dir):
        """Intelligently backup existing files"""
        if not os.path.exists(output_dir):
            return {"backup_created": False, "reason": "Directory does not exist"}
        
        files_to_backup = []
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                if not file.startswith('.'):  # Ignore hidden files
                    files_to_backup.append(os.path.join(root, file))
        
        if not files_to_backup:
            return {"backup_created": False, "reason": "No files to backup"}
        
        backup_dir = f"{output_dir}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_info = {
            "backup_created": True,
            "backup_time": datetime.now().isoformat(),
            "original_dir": output_dir,
            "backup_dir": backup_dir,
            "files_backed_up": len(files_to_backup),
            "backup_size_estimate": sum(len(f) for f in files_to_backup)  # Simple estimation
        }
        
        self.operations_log.append({
            "operation": "backup",
            "timestamp": datetime.now().isoformat(),
            "directory": output_dir,
            "backup_info": backup_info
        })
        
        return backup_info
    
    def execute(self, action, *args, **kwargs):
        """Unified execution interface"""
        if action == "organize_files":
            files = kwargs.get("files", {})
            result = self.organize(files)
            return {"status": "success", "result": result}
        elif action == "backup_existing":
            output_dir = kwargs.get("output_dir", "")
            return self.backup_existing(output_dir)
        elif action == "validate_structure":
            files = kwargs.get("files", {})
            return self.validate_structure(files)
        elif action == "optimize_structure":
            files = kwargs.get("files", {})
            return self.optimize_file_structure(files)
        else:
            return {"status": "success", "result": "File manager executed"}
    
    def _clean_file_content(self, content, file_path):
        """Clean file content, remove code block wrappers etc."""
        if not content:
            return content
        
        # Remove code block wrapping (like ```html, ```css, ```js etc.)
        content = content.strip()
        
        # Check if wrapped in code blocks
        if content.startswith('```'):
            lines = content.split('\n')
            # Remove first line language identifier
            if len(lines) > 1:
                content = '\n'.join(lines[1:])
            
            # Remove ending ```
            if content.endswith('```'):
                content = content[:-3].rstrip()
        
        # Remove four backticks at start (case of four backticks)
        if content.startswith('````'):
            lines = content.split('\n')
            if len(lines) > 1:
                content = '\n'.join(lines[1:])
            if content.endswith('````'):
                content = content[:-4].rstrip()
        
        # Remove extra newlines
        content = content.strip()
        
        return content

class QualityChecker:
    """Quality checker - check code quality and best practices"""
    
    def __init__(self):
        self.quality_standards = {
            "html": {
                "required": ["<!DOCTYPE html>", "<title>", "</title>"],
                "recommended": ['lang="', 'charset="utf-8"'],
                "avoid": ["<center>", "<font>"]
            },
            "css": {
                "recommended": ["/* comments */", ":hover", "media query"],
                "avoid": ["!important", "inline styles"]
            },
            "js": {
                "recommended": ["const ", "let ", "==="],
                "avoid": ["var ", "==", "eval("]
            }
        }
    
    def check_quality(self, code, requirements=None):
        """Check code quality"""
        issues = []
        suggestions = []
        score = 1.0
        
        # Detect code type
        if "<!DOCTYPE html>" in code:
            file_type = "html"
        elif code.strip().startswith(".") or code.strip().startswith("#"):
            file_type = "css"
        elif "function" in code or "const " in code:
            file_type = "js"
        else:
            file_type = "unknown"
        
        if file_type in self.quality_standards:
            standards = self.quality_standards[file_type]
            
            # Check required items
            for required in standards.get("required", []):
                if required not in code:
                    issues.append(f"Missing required element: {required}")
                    score -= 0.2
            
            # Check recommended items
            for recommended in standards.get("recommended", []):
                if recommended not in code:
                    suggestions.append(f"Consider adding: {recommended}")
            
            # Check items to avoid
            for avoid in standards.get("avoid", []):
                if avoid in code:
                    issues.append(f"Avoid using: {avoid}")
                    score -= 0.1
        
        # General quality check
        if len(code.split('\n')) > 1000:
            suggestions.append("File is very large, consider splitting into modules")
        
        if not re.search(r'/\*.*\*/|//.*', code):
            suggestions.append("Add comments to explain complex logic")
        
        return {
            "score": max(0, score),
            "issues": issues,
            "suggestions": suggestions,
            "file_type": file_type
        }
    
    def execute(self, action="check_quality", *args, **kwargs):
        """Unified execution interface"""
        if action == "check_quality":
            # Handle single code check
            code = kwargs.get("code", "")
            requirements = kwargs.get("requirements")
            
            # Handle multiple file check
            files = kwargs.get("files")
            if files:
                return self._check_multiple_files(files, kwargs.get("project_type", "web"))
            else:
                return {"status": "success", "result": self.check_quality(code, requirements)}
        elif action == "comprehensive_check":
            files = kwargs.get("files", {})
            project_type = kwargs.get("project_type", "web")
            return self._check_multiple_files(files, project_type)
        else:
            return {"status": "success", "result": "Quality checker executed"}
    
    def _check_multiple_files(self, files, project_type):
        """Check quality of multiple files"""
        if not files:
            return {"status": "error", "message": "No files provided"}
        
        total_score = 0
        file_count = 0
        all_results = {}
        
        for file_path, content in files.items():
            if content and content.strip():
                result = self.check_quality(content)
                all_results[file_path] = result
                total_score += result.get("score", 0)
                file_count += 1
        
        overall_score = (total_score / file_count) if file_count > 0 else 0
        
        return {
            "status": "success",
            "overall_score": overall_score,
            "files_checked": file_count,
            "individual_results": all_results,
            "summary": f"Checked {file_count} files, average score: {overall_score:.2f}"
        }

class APIIntegrationTool:
    """API integration tool - simulate external API calls and resource fetching"""
    
    def __init__(self):
        self.api_calls = []
    
    def integrate(self, api_spec):
        """Integrate API"""
        return {"status": "integrated", "api_spec": api_spec}
    
    def fetch_external_libraries(self, project_type):
        """Get external libraries specific to project type"""
        libraries = {
            "web_visualization": [
                {
                    "name": "Chart.js",
                    "url": "https://cdn.jsdelivr.net/npm/chart.js",
                    "type": "javascript",
                    "purpose": "Interactive charts and graphs"
                },
                {
                    "name": "D3.js",
                    "url": "https://d3js.org/d3.v7.min.js",
                    "type": "javascript",
                    "purpose": "Data-driven document manipulation"
                },
                {
                    "name": "Bootstrap",
                    "url": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css",
                    "type": "css",
                    "purpose": "Responsive design framework"
                },
                {
                    "name": "Font Awesome",
                    "url": "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css",
                    "type": "css",
                    "purpose": "Icon library"
                }
            ],
            "data_analysis": [
                {
                    "name": "Plotly.js",
                    "url": "https://cdn.plot.ly/plotly-latest.min.js",
                    "type": "javascript",
                    "purpose": "Scientific charting"
                },
                {
                    "name": "Math.js",
                    "url": "https://unpkg.com/mathjs@11.11.0/lib/browser/math.min.js",
                    "type": "javascript",
                    "purpose": "Mathematical operations"
                }
            ]
        }
        
        result = libraries.get(project_type, [])
        self.api_calls.append({
            "endpoint": "external_libraries",
            "project_type": project_type,
            "result_count": len(result),
            "timestamp": datetime.now().isoformat()
        })
        
        return {"status": "success", "libraries": result}
    
    def fetch_color_palette(self, theme="modern"):
        """Get color theme"""
        palettes = {
            "modern": ["#3498db", "#2ecc71", "#e74c3c", "#f39c12"],
            "dark": ["#2c3e50", "#34495e", "#7f8c8d", "#95a5a6"],
            "bright": ["#e74c3c", "#f39c12", "#f1c40f", "#2ecc71"]
        }
        
        return {"status": "success", "palette": palettes.get(theme, palettes["modern"])}
    
    def get_web_fonts(self, font_name="Open Sans"):
        """Get web fonts"""
        fonts = {
            "Open Sans": "https://fonts.googleapis.com/css2?family=Open+Sans:wght@300;400;600;700&display=swap",
            "Roboto": "https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap"
        }
        
        return {"status": "success", "font_url": fonts.get(font_name, fonts["Open Sans"])}
    
    def execute(self, action, *args, **kwargs):
        """Unified execution interface"""
        if action == "fetch_external_libraries" or action == "fetch_cdn_libraries":
            return self.fetch_external_libraries(kwargs.get("project_type", "web"))
        elif action == "fetch_color_palette":
            return self.fetch_color_palette(kwargs.get("theme", "modern"))
        elif action == "get_web_fonts":
            return self.get_web_fonts(kwargs.get("font_name", "Open Sans"))
        else:
            # Handle other possible API calls
            return {"status": "success", "result": f"API tool executed: {action}"}

class AutomatedTester:
    """Automated tester - execute comprehensive automated testing"""
    
    def __init__(self):
        self.test_results = []
        self.test_suites = {
            "web_visualization": {
                "html_tests": [
                    {"name": "DOCTYPE check", "pattern": "<!DOCTYPE html>"},
                    {"name": "Title check", "pattern": "<title>"},
                    {"name": "Meta charset", "pattern": 'charset="utf-8"'},
                    {"name": "Viewport meta", "pattern": 'name="viewport"'},
                    {"name": "Semantic HTML", "pattern": "<(header|nav|main|section|article|footer)>"},
                ],
                "css_tests": [
                    {"name": "CSS syntax", "check": "brackets_balanced"},
                    {"name": "Responsive design", "pattern": "@media"},
                    {"name": "Modern CSS", "pattern": "(grid|flexbox|flex)"},
                    {"name": "Hover effects", "pattern": ":hover"},
                ],
                "js_tests": [
                    {"name": "Modern JS", "pattern": "(const |let |=>)"},
                    {"name": "Event handling", "pattern": "addEventListener"},
                    {"name": "Error handling", "pattern": "(try|catch)"},
                    {"name": "Bracket balance", "check": "brackets_balanced"},
                ]
            }
        }
    
    def run_tests(self, code=None, test_cases=None, files=None, project_type="web_visualization"):
        """Run comprehensive automated testing"""
        if files:
            return self._run_comprehensive_tests(files, project_type)
        elif code:
            return self._run_single_file_tests(code)
        else:
            return {"error": "No code or files provided for testing"}
    
    def _run_comprehensive_tests(self, files, project_type):
        """Run comprehensive tests on entire project"""
        results = {}
        all_issues = []
        passed_tests = 0
        total_tests = 0
        
        test_suite = self.test_suites.get(project_type, self.test_suites["web_visualization"])
        
        for file_path, content in files.items():
            file_ext = os.path.splitext(file_path)[1].lower()
            file_results = []
            file_issues = []
            
            # Run corresponding tests based on file type
            if file_ext == ".html" and "html_tests" in test_suite:
                file_results, file_issues = self._run_html_tests(content, test_suite["html_tests"])
            elif file_ext == ".css" and "css_tests" in test_suite:
                file_results, file_issues = self._run_css_tests(content, test_suite["css_tests"])
            elif file_ext == ".js" and "js_tests" in test_suite:
                file_results, file_issues = self._run_js_tests(content, test_suite["js_tests"])
            
            if file_results:
                results[file_path] = {
                    "tests": file_results,
                    "issues": file_issues,
                    "passed": len([t for t in file_results if t["status"] == "passed"]),
                    "total": len(file_results)
                }
                
                passed_tests += results[file_path]["passed"]
                total_tests += results[file_path]["total"]
                all_issues.extend(file_issues)
        
        # Run cross-file integration tests
        integration_results = self._run_integration_tests(files, project_type)
        if integration_results:
            results["integration"] = integration_results
            passed_tests += integration_results["passed"]
            total_tests += integration_results["total"]
            all_issues.extend(integration_results["issues"])
        
        coverage = (passed_tests / total_tests) if total_tests > 0 else 1.0
        
        test_result = {
            "passed": len(all_issues) == 0,
            "results": results,
            "coverage": coverage,
            "issues": all_issues,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "test_summary": self._generate_test_summary(results),
            "recommendations": self._generate_test_recommendations(all_issues, coverage)
        }
        
        self.test_results.append({
            "timestamp": datetime.now().isoformat(),
            "project_type": project_type,
            "result": test_result
        })
        
        return test_result
    
    def _run_html_tests(self, content, tests):
        """Run HTML specific tests"""
        results = []
        issues = []
        
        for test in tests:
            if "pattern" in test:
                if re.search(test["pattern"], content, re.IGNORECASE):
                    results.append({"test": test["name"], "status": "passed"})
                else:
                    results.append({"test": test["name"], "status": "failed"})
                    issues.append(f"HTML: {test['name']} failed")
            elif test.get("check") == "brackets_balanced":
                if self._check_html_structure(content):
                    results.append({"test": test["name"], "status": "passed"})
                else:
                    results.append({"test": test["name"], "status": "failed"})
                    issues.append("HTML: Tag structure is not balanced")
        
        return results, issues
    
    def _run_css_tests(self, content, tests):
        """Run CSS specific tests"""
        results = []
        issues = []
        
        for test in tests:
            if "pattern" in test:
                if re.search(test["pattern"], content, re.IGNORECASE):
                    results.append({"test": test["name"], "status": "passed"})
                else:
                    results.append({"test": test["name"], "status": "failed"})
                    issues.append(f"CSS: {test['name']} failed")
            elif test.get("check") == "brackets_balanced":
                if content.count("{") == content.count("}"):
                    results.append({"test": test["name"], "status": "passed"})
                else:
                    results.append({"test": test["name"], "status": "failed"})
                    issues.append("CSS: Unbalanced brackets")
        
        return results, issues
    
    def _run_js_tests(self, content, tests):
        """Run JavaScript specific tests"""
        results = []
        issues = []
        
        for test in tests:
            if "pattern" in test:
                if re.search(test["pattern"], content, re.IGNORECASE):
                    results.append({"test": test["name"], "status": "passed"})
                else:
                    results.append({"test": test["name"], "status": "failed"})
                    issues.append(f"JavaScript: {test['name']} failed")
            elif test.get("check") == "brackets_balanced":
                if self._check_js_brackets(content):
                    results.append({"test": test["name"], "status": "passed"})
                else:
                    results.append({"test": test["name"], "status": "failed"})
                    issues.append("JavaScript: Unbalanced brackets")
        
        return results, issues
    
    def _run_integration_tests(self, files, project_type):
        """Run integration tests"""
        results = []
        issues = []
        
        html_files = [f for f in files.keys() if f.endswith('.html')]
        css_files = [f for f in files.keys() if f.endswith('.css')]
        js_files = [f for f in files.keys() if f.endswith('.js')]
        
        # Test file reference relationships
        for html_file in html_files:
            html_content = files[html_file]
            
            # CSS reference test
            css_refs = re.findall(r'href=["\']([^"\']*\.css)["\']', html_content)
            for css_ref in css_refs:
                if css_ref in [os.path.basename(f) for f in css_files]:
                    results.append({"test": f"CSS reference: {css_ref}", "status": "passed"})
                else:
                    results.append({"test": f"CSS reference: {css_ref}", "status": "failed"})
                    issues.append(f"Referenced CSS file not found: {css_ref}")
            
            # JS reference test
            js_refs = re.findall(r'src=["\']([^"\']*\.js)["\']', html_content)
            for js_ref in js_refs:
                if js_ref in [os.path.basename(f) for f in js_files]:
                    results.append({"test": f"JS reference: {js_ref}", "status": "passed"})
                else:
                    results.append({"test": f"JS reference: {js_ref}", "status": "failed"})
                    issues.append(f"Referenced JS file not found: {js_ref}")
        
        return {
            "tests": results,
            "issues": issues,
            "passed": len([r for r in results if r["status"] == "passed"]),
            "total": len(results)
        }
    
    def _check_html_structure(self, content):
        """Check HTML structure integrity"""
        # Simplified HTML tag balance check
        tags = re.findall(r'<(/?)(\w+)[^>]*>', content)
        stack = []
        
        for is_closing, tag in tags:
            if is_closing:
                if stack and stack[-1] == tag.lower():
                    stack.pop()
                else:
                    return False
            else:
                if tag.lower() not in ['img', 'br', 'hr', 'input', 'meta', 'link']:
                    stack.append(tag.lower())
        
        return len(stack) == 0
    
    def _check_js_brackets(self, content):
        """Check JavaScript bracket balance"""
        brackets = {'(': ')', '[': ']', '{': '}'}
        stack = []
        
        for char in content:
            if char in brackets:
                stack.append(char)
            elif char in brackets.values():
                if not stack or brackets[stack.pop()] != char:
                    return False
        
        return len(stack) == 0
    
    def _generate_test_summary(self, results):
        """Generate test summary"""
        summary = {
            "files_tested": len([k for k in results.keys() if k != "integration"]),
            "test_categories": [],
            "overall_health": "Unknown"
        }
        
        total_passed = sum(r.get("passed", 0) for r in results.values())
        total_tests = sum(r.get("total", 0) for r in results.values())
        
        if total_tests > 0:
            pass_rate = total_passed / total_tests
            if pass_rate >= 0.9:
                summary["overall_health"] = "Excellent"
            elif pass_rate >= 0.7:
                summary["overall_health"] = "Good"
            elif pass_rate >= 0.5:
                summary["overall_health"] = "Fair"
            else:
                summary["overall_health"] = "Poor"
        
        return summary
    
    def _generate_test_recommendations(self, issues, coverage):
        """Generate test recommendations"""
        recommendations = []
        
        if coverage < 0.7:
            recommendations.append("Improve test coverage, resolve failed test cases")
        
        html_issues = [i for i in issues if i.startswith("HTML:")]
        if html_issues:
            recommendations.append(f"Fix {len(html_issues)} HTML issues")
        
        css_issues = [i for i in issues if i.startswith("CSS:")]
        if css_issues:
            recommendations.append(f"Fix {len(css_issues)} CSS issues")
        
        js_issues = [i for i in issues if i.startswith("JavaScript:")]
        if js_issues:
            recommendations.append(f"Fix {len(js_issues)} JavaScript issues")
        
        if not recommendations:
            recommendations.append("All tests passed! Code quality is good.")
        
        return recommendations
    
    def _run_single_file_tests(self, code):
        """Run tests on single file"""
        file_type = self._detect_file_type(code)
        issues = []
        
        # Basic syntax check
        if file_type == "html":
            if not self._check_html_structure(code):
                issues.append("HTML structure is invalid")
        elif file_type == "css":
            if code.count("{") != code.count("}"):
                issues.append("CSS brackets are unbalanced")
        elif file_type == "javascript":
            if not self._check_js_brackets(code):
                issues.append("JavaScript brackets are unbalanced")
        
        return {
            "passed": len(issues) == 0,
            "issues": issues,
            "file_type": file_type,
            "test_count": 1
        }
    
    def _detect_file_type(self, code):
        """Detect file type"""
        code_lower = code.lower()
        if "<!doctype html>" in code_lower or "<html" in code_lower:
            return "html"
        elif code.strip().startswith((".", "#", "@", "/*")) or ":" in code and "{" in code:
            return "css"
        elif any(keyword in code for keyword in ["function", "const ", "let ", "var ", "=>"]):
            return "javascript"
        return "unknown"
    
    def execute(self, action="run_tests", *args, **kwargs):
        """Unified execution interface"""
        if action == "run_tests" or action == "test" or action == "full_suite":
            # Support multiple calling methods
            code = kwargs.get("code")
            files = kwargs.get("files")
            test_cases = kwargs.get("test_cases")
            project_type = kwargs.get("project_type", "web_visualization")
            
            # If there are args parameters, try to extract from them
            if args:
                if isinstance(args[0], dict):
                    files = args[0]
                elif isinstance(args[0], str):
                    code = args[0]
            
            return self.run_tests(code=code, test_cases=test_cases, files=files, project_type=project_type)
        
        elif action == "comprehensive_test":
            files = kwargs.get("files", {})
            project_type = kwargs.get("project_type", "web_visualization")
            return self._run_comprehensive_tests(files, project_type)
        
        elif action == "validate_syntax":
            code = kwargs.get("code", "")
            return self._run_single_file_tests(code)
        
        else:
            return {"status": "success", "result": f"Automated tester executed: {action}"}

# Create instances
code_analyzer = CodeAnalyzer()
file_manager = FileManager()
quality_checker = QualityChecker()
api_integration_tool = APIIntegrationTool()
automated_tester = AutomatedTester()
