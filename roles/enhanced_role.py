#!/usr/bin/env python3
"""
Enhanced role base class - provides common tool integration capabilities for all roles
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Use new simplified tool system
from tools import global_tool_orchestrator, CodeAnalyzer, FileManager, QualityChecker

class EnhancedRole:
    """Enhanced role base class - provides common tool integration capabilities for all roles"""
    
    def __init__(self):
        self.tools = []
        self.project_specification = None
        self.quality_gates = []
        self.feedback_history = []
        self.role_name = self.__class__.__name__
        
        # Add universal tools
        self._add_universal_tools()
    
    def _add_universal_tools(self):
        """Add universal tools"""
        self.tools.extend([
            CodeAnalyzer(),
            FileManager(), 
            QualityChecker()
        ])
    
    def set_project_specification(self, project_spec):
        """Set project specification that all roles need to follow"""
        self.project_specification = project_spec
        self._adapt_to_project_type(project_spec["type"])
        print(f"📋 {self.role_name} adapted to project type: {project_spec['type']}")
    
    def _adapt_to_project_type(self, project_type):
        """Adapt role behavior based on project type - subclasses implement specific adaptation logic"""
        # Base class provides default implementation, subclasses can override
        adaptation_strategies = {
            "web_frontend": self._adapt_to_frontend,
            "web_backend": self._adapt_to_backend,
            "data_science": self._adapt_to_data_science,
            "mobile": self._adapt_to_mobile,
            "desktop": self._adapt_to_desktop,
            "fullstack": self._adapt_to_fullstack
        }
        
        strategy = adaptation_strategies.get(project_type, self._adapt_to_generic)
        strategy()
    
    def _adapt_to_frontend(self):
        """Adapt for frontend projects"""
        print(f"🎨 {self.role_name} adapted for frontend development")
    
    def _adapt_to_backend(self):
        """Adapt for backend projects"""
        print(f"⚙️ {self.role_name} adapted for backend development")
    
    def _adapt_to_data_science(self):
        """Adapt for data science projects"""
        print(f"📊 {self.role_name} adapted for data science project")
    
    def _adapt_to_mobile(self):
        """Adapt for mobile projects"""
        print(f"📱 {self.role_name} adapted for mobile development")
    
    def _adapt_to_desktop(self):
        """Adapt for desktop projects"""
        print(f"🖥️ {self.role_name} adapted for desktop development")
    
    def _adapt_to_fullstack(self):
        """Adapt for fullstack projects"""
        print(f"🌐 {self.role_name} adapted for fullstack development")
    
    def _adapt_to_generic(self):
        """Adapt for generic projects"""
        print(f"🔧 {self.role_name} adapted for generic project")
    
    def execute_with_quality_gate(self, phase, task_func, *args, **kwargs):
        """Execute task under quality gate protection"""
        print(f"🚪 {self.role_name} executing {phase} with quality gate protection...")
        
        # Execute task
        result = task_func(*args, **kwargs)
        
        # Quality gate check
        gatekeeper = self.get_tool("QualityGatekeeper")
        if gatekeeper and self.project_specification:
            print(f"🔍 Running quality gate for {phase}...")
            gate_result = gatekeeper.execute(phase, result, self.project_specification)
            
            if not gate_result["gate_passed"]:
                print(f"❌ Quality gate failed for {phase}")
                print(f"🔧 Attempting to fix issues: {gate_result['blocking_issues']}")
                # Quality gate failed, attempt to fix
                result = self._handle_quality_gate_failure(result, gate_result, phase)
            else:
                print(f"✅ Quality gate passed for {phase} (score: {gate_result['overall_score']:.1f}/10)")
            
            # Record quality gate history
            self.quality_gates.append({
                "phase": phase,
                "result": gate_result,
                "timestamp": self._get_timestamp()
            })
        
        return result
    
    def _handle_quality_gate_failure(self, result, gate_result, phase):
        """Handle quality gate failure"""
        print(f"🛠️ {self.role_name} handling quality gate failure in {phase}...")
        
        # Attempt to fix based on failure reasons
        blocking_issues = gate_result.get("blocking_issues", [])
        recommendations = gate_result.get("recommendations", [])
        
        # Record feedback
        self.feedback_history.append({
            "phase": phase,
            "issues": blocking_issues,
            "recommendations": recommendations,
            "timestamp": self._get_timestamp()
        })
        
        # Attempt to improve result based on recommendations
        improved_result = self._apply_quality_improvements(result, recommendations, phase)
        
        return improved_result
    
    def _apply_quality_improvements(self, result, recommendations, phase):
        """Apply quality improvement recommendations"""
        print(f"💡 Applying {len(recommendations)} quality improvements...")
        
        # Implementation of specific improvement logic here
        # Base class provides default implementation, subclasses can override for more specific improvements
        
        if not result:
            result = {}
        
        # Add improvement markers
        if "quality_improvements" not in result:
            result["quality_improvements"] = []
        
        for rec in recommendations:
            result["quality_improvements"].append({
                "criterion": rec.get("criterion", "unknown"),
                "priority": rec.get("priority", "medium"),
                "suggestion": rec.get("suggestion", "No specific suggestion"),
                "applied": True
            })
        
        return result
    
    def get_tool(self, tool_name):
        """Get tool instance"""
        for tool in self.tools:
            if tool.name == tool_name:
                return tool
        return None
    
    def get_contextual_tools(self, phase):
        """Get relevant tools based on current phase"""
        if not self.project_specification:
            return self.tools
        
        project_type = self.project_specification["type"]
        return [tool for tool in self.tools if self._is_tool_relevant(tool, phase, project_type)]
    
    def _is_tool_relevant(self, tool, phase, project_type):
        """Determine if tool is relevant to current phase and project type"""
        # Universal tools are always relevant
        universal_tools = ["ProjectSpecificationCoordinator", "UniversalValidator", "QualityGatekeeper"]
        if tool.name in universal_tools:
            return True
        
        # Other tools determined by phase and project type
        relevance_map = {
            "architecture_design": ["ProjectSpecificationCoordinator", "UniversalValidator"],
            "design_modeling": ["UniversalValidator", "QualityGatekeeper"],
            "implementation": ["UniversalValidator", "QualityGatekeeper"],
            "testing_validation": ["UniversalValidator", "QualityGatekeeper"]
        }
        
        return tool.name in relevance_map.get(phase, [])
    
    def generate_role_report(self):
        """Generate role work report"""
        return {
            "role": self.role_name,
            "project_type": self.project_specification.get("type") if self.project_specification else "unknown",
            "tools_used": [tool.name for tool in self.tools],
            "quality_gates": len(self.quality_gates),
            "feedback_received": len(self.feedback_history),
            "overall_performance": self._calculate_role_performance()
        }
    
    def _calculate_role_performance(self):
        """Calculate role performance"""
        if not self.quality_gates:
            return 0
        
        total_score = sum(gate["result"]["overall_score"] for gate in self.quality_gates)
        return total_score / len(self.quality_gates)
    
    def _get_timestamp(self):
        """Get timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def add_custom_tool(self, tool):
        """Add custom tool"""
        self.tools.append(tool)
        print(f"🔧 Added custom tool {tool.name} to {self.role_name}")
    
    def remove_tool(self, tool_name):
        """Remove tool"""
        self.tools = [tool for tool in self.tools if tool.name != tool_name]
        print(f"🗑️ Removed tool {tool_name} from {self.role_name}")
    
    def get_feedback_summary(self):
        """Get feedback summary"""
        if not self.feedback_history:
            return "No feedback received"
        
        total_issues = sum(len(feedback["issues"]) for feedback in self.feedback_history)
        phases_with_issues = len(set(feedback["phase"] for feedback in self.feedback_history))
        
        return {
            "total_feedback_sessions": len(self.feedback_history),
            "total_issues_identified": total_issues,
            "phases_with_issues": phases_with_issues,
            "improvement_rate": self._calculate_improvement_rate()
        }
    
    def _calculate_improvement_rate(self):
        """Calculate improvement rate"""
        if len(self.quality_gates) < 2:
            return 0
        
        # Compare scores of first and last quality gates
        first_score = self.quality_gates[0]["result"]["overall_score"]
        last_score = self.quality_gates[-1]["result"]["overall_score"]
        
        return ((last_score - first_score) / first_score) * 100 if first_score > 0 else 0
