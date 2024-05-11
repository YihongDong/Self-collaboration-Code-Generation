import io
import signal
from contextlib import redirect_stdout
from typing import Any, Callable, List, Optional
from collections import Counter

from .backend import call_chatgpt


class timeout:
    def __init__(self, seconds=1, error_message='Timeout'):
        self.seconds = seconds
        self.error_message = error_message
    def timeout_handler(self, signum, frame):
        raise TimeoutError(self.error_message)
    def __enter__(self):
        signal.signal(signal.SIGALRM, self.timeout_handler)
        signal.alarm(self.seconds)
    def __exit__(self, type, value, traceback):
        signal.alarm(0)

class ProgramInterface:
    
    def __init__(
        self,
        model: str = 'code-davinci-002',
        stop: str = '\n\n',
        get_answer_symbol: Optional[str] = None,
        get_answer_expr: Optional[str] = None,
        get_answer_from_stdout: bool = False,
        verbose: bool = False
    ) -> None:

        self.model = model
        self.history = []
        self.stop = stop
        self.answer_symbol = get_answer_symbol
        self.answer_expr = get_answer_expr
        self.get_answer_from_stdout = get_answer_from_stdout
        self.verbose = verbose
        
    def clear_history(self):
        self.history = []
    
    def process_generation_to_code(self, gens: str):
        return [g.split('\n') for g in gens]
    
    def generate(self, prompt: str, temperature: float =0.0, top_p: float =1.0, 
            max_tokens: int =512, majority_at: int =None, echo: bool =False, return_logprobs: bool =False):

        if 'davinci' not in self.model:
            gens = call_chatgpt(prompt, model=self.model, stop=self.stop, 
                temperature=temperature, top_p=top_p, max_tokens=max_tokens, echo=echo, majority_at=majority_at)
            
        return gens
    
    def run(self, prompt: str, time_out: float =10, temperature: float =0.0, top_p: float =1.0, 
            max_tokens: int =512, majority_at: int =None, echo=False, return_logprobs: bool =False):
        code_snippets = self.generate(prompt, majority_at=majority_at, temperature=temperature, top_p=top_p, max_tokens=max_tokens, echo=echo, return_logprobs=return_logprobs)

        return code_snippets
    