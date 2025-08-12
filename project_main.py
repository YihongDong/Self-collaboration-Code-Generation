import os
import copy
import json
import argparse
import tqdm

from project_session import ProjectSession
from utils import construct_system_message

parser = argparse.ArgumentParser()
parser.add_argument('--project_type', type=str, default='web_visualization', 
                   choices=['web_visualization', 'data_analysis', 'api_service', 'desktop_app'])
parser.add_argument('--requirement', type=str, required=True, help='Project requirement description')
parser.add_argument('--output_dir', type=str, default='generated_project')
parser.add_argument('--model', type=str, default='gpt-3.5-turbo')
parser.add_argument('--max_round', type=int, default=3)
parser.add_argument('--max_tokens', type=int, default=1024) 
parser.add_argument('--majority', type=int, default=1)
parser.add_argument('--temperature', type=float, default=0.2)
parser.add_argument('--top_p', type=float, default=0.95)
parser.add_argument('--verbose', action='store_true')
args = parser.parse_args()


if __name__ == '__main__':
    from roles.project_roles import PROJECT_TEAM, PROJECT_ARCHITECT, PROJECT_DEVELOPER, PROJECT_TESTER, UI_DESIGNER

    OUTPUT_DIR = args.output_dir
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    try:
        # Initialize project session with enhanced roles
        session = ProjectSession(
            team_description=PROJECT_TEAM,
            architect_description=PROJECT_ARCHITECT, 
            developer_description=PROJECT_DEVELOPER,
            tester_description=PROJECT_TESTER,
            ui_designer_description=UI_DESIGNER,
            requirement=args.requirement,
            project_type=args.project_type,
            model=args.model, 
            majority=args.majority,
            max_tokens=args.max_tokens, 
            temperature=args.temperature,
            top_p=args.top_p, 
            max_round=args.max_round,
            output_dir=OUTPUT_DIR
        )
        
        # Run project generation session
        project_files, session_history = session.run_project_session()
        
        # Save session history
        with open(os.path.join(OUTPUT_DIR, 'session_history.json'), 'w', encoding='utf-8') as f:
            json.dump(session_history, f, indent=2, ensure_ascii=False)
            
        print(f"Project generated successfully in: {OUTPUT_DIR}")
        print(f"Generated files: {list(project_files.keys())}")
        
        # If web project, provide instructions for running
        if args.project_type == 'web_visualization' and 'index.html' in project_files:
            print("\nTo view the web application:")
            print(f"Open {os.path.join(OUTPUT_DIR, 'index.html')} in your browser")
            
    except Exception as e:
        print(f"Project generation failed: {str(e)}")
