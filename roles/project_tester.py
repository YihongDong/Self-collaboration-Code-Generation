import os
import copy
import json
import time

from core import interface
from utils import construct_system_message
from tools import global_tool_orchestrator


class ProjectTester(object):
    def __init__(self, team_description, tester_description, requirement, project_type,
                 model='gpt-3.5-turbo', majority=1, max_tokens=1024, temperature=0.2, top_p=0.95):
        self.model = model
        self.majority = majority
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.history_message = []
        self.requirement = requirement
        self.project_type = project_type
        
        # Add tool orchestrator reference
        self.tool_orchestrator = global_tool_orchestrator

        self.itf = interface.ProgramInterface(
            stop='',
            verbose=False,
            model=self.model,
        )

        system_message = construct_system_message(requirement, tester_description, team_description)
        self.history_message_append(system_message)

    def test_project(self, project_files, architecture_plan):
        """Test the complete project implementation with tool assistance"""
        
        print("🧪 Enhanced testing with automated tools...")
        
        # Use automated tester for initial validation
        automated_tester = self.tool_orchestrator.get_tool("automated_tester")
        quality_checker = self.tool_orchestrator.get_tool("quality_checker")
        
        tool_results = {}
        if automated_tester:
            automated_results = automated_tester.execute("full_suite", 
                                                       files=project_files,
                                                       project_type=self.project_type)
            tool_results["automated_tests"] = automated_results
            print(f"🤖 Automated tests: {automated_results.get('status', 'completed')}")
        
        if quality_checker:
            quality_results = quality_checker.execute("check_quality",
                                                     files=project_files,
                                                     project_type=self.project_type)
            tool_results["quality_check"] = quality_results
            print(f"🔍 Quality check: {quality_results.get('overall_score', 'N/A')}/10")
        
        files_summary = self._create_files_summary(project_files)
        
        # Create enhanced testing prompt with tool results
        tool_summary = ""
        if tool_results:
            tool_summary = f"""
        
        Tool-based Testing Results:
        {json.dumps(tool_results, indent=2)}
        """
        
        testing_prompt = f"""
        Please test the following project implementation comprehensively, considering both manual review and automated tool results.
        
        Project Type: {self.project_type}
        Requirements: {self.requirement}
        Architecture Plan: {architecture_plan}
        
        Project Files:
        {files_summary}
        {tool_summary}
        
        Please perform the following types of testing:
        
        1. **Code Quality Analysis** (Enhanced with tools):
           - Check for syntax errors
           - Verify proper HTML structure and semantic markup
           - Validate CSS syntax and modern practices
           - Review JavaScript functionality and ES6+ usage
           - Consider automated tool findings
        
        2. **Functionality Testing**:
           - Verify all required features are implemented
           - Check if the project meets the stated requirements
           - Test user interactions and interface elements
           - Validate data flow and API integration
        
        3. **Design and UX Testing**:
           - Evaluate visual design and modern UI principles
           - Check responsive design implementation
           - Assess user experience and accessibility (WCAG compliance)
           - Review color schemes, typography, and spacing
        
        4. **Performance and Best Practices**:
           - Review code organization and structure
           - Check for performance optimizations
           - Verify modern web development practices
           - Assess browser compatibility
           - Review security considerations
        
        5. **Integration and Compatibility**:
           - Test cross-browser functionality
           - Check mobile responsiveness
           - Validate external dependencies
           - Assess loading performance
        
        Provide a detailed test report with:
        - Issues found (categorized by severity)
        - Suggestions for improvement (prioritized)
        - Overall assessment with scoring
        - Specific areas that need attention
        - Validation of tool-based findings
        
        If everything looks good, clearly state "All tests passed - no issues found."
        Include a final recommendation for deployment readiness.
        """
        
        self.history_message_append(testing_prompt)
        
        try:
            responses = self.itf.run(prompt=self.history_message, majority_at=self.majority,
                                   max_tokens=self.max_tokens, temperature=self.temperature, top_p=self.top_p)
        except Exception as e:
            print(f"Project testing failed: {e}")
            time.sleep(5)
            return "error"

        test_report = responses[0]
        self.history_message_append(test_report, "assistant")
        
        return test_report
    
    def _create_files_summary(self, project_files):
        """Create a summary of project files for testing"""
        summary = ""
        
        for file_path, content in project_files.items():
            summary += f"\n--- {file_path} ---\n"
            # Include first 20 lines or 1000 characters, whichever is shorter
            lines = content.split('\n')
            if len(lines) > 20:
                preview = '\n'.join(lines[:20]) + '\n... (truncated)'
            else:
                preview = content[:1000]
                if len(content) > 1000:
                    preview += "... (truncated)"
            summary += preview + "\n"
        
        return summary
    
    def history_message_append(self, message, role="user"):
        self.history_message.append({
            "role": role,
            "content": message
        })
