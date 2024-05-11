import os
import copy
import json
import argparse
import tqdm

from session import Session
from datasets import load_dataset, load_from_disk
from utils import prompt_split_humaneval, find_method_name, code_split, build_test_method

parser = argparse.ArgumentParser()
parser.add_argument('--dataset', type=str, default='humaneval')
parser.add_argument('--lang', type=str, default='python')
parser.add_argument('--output_path', type=str, default='output.jsonl')

parser.add_argument('--signature', action='store_true')
parser.add_argument('--model', type=str, default='gpt-3.5-turbo-0301')
parser.add_argument('--max_round', type=int, default=2)

parser.add_argument('--max_tokens', type=int, default=512) 
parser.add_argument('--majority', type=int, default=1)
parser.add_argument('--temperature', type=float, default=0.0)
parser.add_argument('--top_p', type=float, default=0.95)

parser.add_argument('--fail_list', type=list, default=[])
parser.add_argument('--append', action='store_true')
parser.add_argument('--verbose', action='store_true')
parser.add_argument("--timeout", type=float, default=10, help="how many seconds to wait during execution for each test case")
args = parser.parse_args()


if __name__ == '__main__':
    from roles.rule_descriptions_actc import TEAM, ANALYST, PYTHON_DEVELOPER, TESTER

    OUTPUT_PATH = args.output_path

    # load dataset
    if args.dataset == 'humaneval':
        if args.lang == 'python':
            dataset = load_dataset("openai_humaneval")
            dataset_key = ["test"]

    with open(OUTPUT_PATH, 'w+') as f:
        for key in dataset_key:
            pbar = tqdm.tqdm(dataset[key], total=len(dataset[key]))
            for idx, task in enumerate(pbar):
                
                if args.dataset == 'humaneval':
                    method_name = task['entry_point']
                    before_func, signature, intent, public_test_case = prompt_split_humaneval(task['prompt'],method_name)
                    args.signature = True
                    if args.signature:
                        intent = task['prompt']
                    
                    test = task['test']

                try:
                    session = Session(TEAM, ANALYST, PYTHON_DEVELOPER, TESTER,requirement=intent, model=args.model, majority=args.majority, 
                                    max_tokens=args.max_tokens, temperature=args.temperature, 
                                    top_p=args.top_p, max_round=args.max_round, before_func=before_func)
                    
                    code, session_history = session.run_session()

                except RuntimeError as e:
                    print(str(e))
                    print("task-%d fail"%(task['task_id']))
                    fail_list.append(task['task_id'])
                    continue

                if  code == "error":
                    continue

                entry_point = find_method_name(code)
                solution = {
                    'task_id': task['task_id'],
                    'prompt': before_func+"\n",
                    'test': test,
                    'entry_point': entry_point,
                    'completion': code,
                    'session_history': session_history,
                }
                f.write(json.dumps(solution) + '\n')
                f.flush()
