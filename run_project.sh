#!/bin/bash

# Project-level code generation script

echo "Self-Collaboration Project-Level Code Generation"
echo "=============================================="

# Example 1: Portfolio Website  
echo "Generating personal portfolio website..."
python3 main.py --mode project \
    --project_type web_visualization \
    --requirement "Create a modern personal portfolio website with sections for about me, skills, projects showcase, and contact form. Include smooth scrolling, animations, and responsive design. Use a professional color scheme and modern typography." \
    --output_dir "generated_portfolio" \
    --model "gpt-3.5-turbo" \
    --max_round 2 \
    --max_tokens 4096 \
    --temperature 0

echo ""
echo "Portfolio generation complete! Check the 'generated_portfolio' folder."
echo "Open generated_portfolio/index.html in your browser to view the result."
echo ""

# Example 2: Web Visualization Dashboard
echo "Generating interactive data visualization dashboard..."
python3 main.py --mode project \
    --project_type web_visualization \
    --requirement "Create an interactive data visualization dashboard that displays sales data with multiple chart types (bar charts, line charts, pie charts). Include filters for date range and product categories. Make it responsive and visually appealing with modern UI design." \
    --output_dir "generated_dashboard" \
    --model "gpt-3.5-turbo" \
    --max_round 2 \
    --max_tokens 4096 \
    --temperature 0

echo ""
echo "Dashboard generation complete! Check the 'generated_dashboard' folder."
echo "Open generated_dashboard/index.html in your browser to view the result."
echo ""


# Example 3: Real-time Analytics Dashboard
echo "Generating real-time analytics dashboard..."
python3 main.py --mode project \
    --project_type web_visualization \
    --requirement "Create a real-time analytics dashboard for monitoring website traffic and user behavior. Include live charts for page views, user sessions, bounce rate, and geographic distribution. Add real-time notifications and customizable widgets." \
    --output_dir "generated_analytics" \
    --model "gpt-3.5-turbo" \
    --max_round 2 \
    --max_tokens 4096 \
    --temperature 0

echo ""
echo "Analytics dashboard generation complete! Check the 'generated_analytics' folder."
echo "Open generated_analytics/index.html in your browser to view the result."
echo ""

echo "=============================================="
echo "All project generations completed!"
echo "You can also run custom projects with:"
echo "python main.py --mode universal --requirement 'Your custom requirement' --output_dir 'your_output_folder'"
