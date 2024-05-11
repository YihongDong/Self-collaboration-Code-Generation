import re
import json
import copy
import argparse
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils import build_test_method, find_method_name, code_split, prompt_split_humaneval
from execute.execution import evaluate_with_test_code, evaluate_with_test_code_T
from evaluation import pass_at_K, AvgPassRatio
from datasets import load_dataset, load_from_disk

parser = argparse.ArgumentParser()
parser.add_argument('--dataset', type=str, default='humaneval')
parser.add_argument('--lang', type=str, default='python')
parser.add_argument('--input_path', type=str, default='humaneval_output_240415.jsonl')
parser.add_argument('--output_path', type=str, default='outputs/test_eval.jsonl')
args = parser.parse_args()

INPUTPATH = args.input_path
OUTPUT_PATH = args.output_path

if args.dataset == 'humaneval':
    dataset = load_dataset("openai_humaneval")
    dataset_key = ["test"]


with open(INPUTPATH, 'r') as f:
    except_list = []
    handled_solutions = [json.loads(line) for line in f if json.loads(line)["task_id"] not in except_list]
    print(len(handled_solutions))
    
for solution in handled_solutions:
    solution["generation"] = solution['prompt'] + solution["completion"]  
    solution["prompt"] = ""
    solution["entry_point"] = find_method_name(solution["generation"]) if find_method_name(solution["generation"]) else "candidate"
    solution["completion"] = solution["generation"]

print(INPUTPATH)
data_dict = {}
for key in dataset_key:
    for idx, task in enumerate(dataset[key]):
        data_dict[task['task_id']] = task

exec_result = evaluate_with_test_code(handled_solutions, timeout=10)
print('pass@1:')
pass_at_K(exec_result, k=[1])

if args.dataset == "humaneval":
    test_case_path= 'data/HumanEval_test_case_ET.jsonl'
    with open(test_case_path, 'r') as f:
        test_cases = [json.loads(line) for line in f]
        
    test_cases_dict = {}
    for case in test_cases:
        test = build_test_method(case['test_case_list'], "", case['entry_point'])
        test_cases_dict[case['task_id']] = test


for solution in handled_solutions:
    solution['test'] =test_cases_dict[solution['task_id']]

exec_result_T = evaluate_with_test_code(handled_solutions, timeout=10)

print('pass@1 - ET:')
pass_at_K(exec_result_T, k=[1])