import os
import copy
import json
import argparse
import tqdm
import time

from core import interface
from utils import code_truncate, construct_system_message


class Analyst(object):
    def __init__(self, TEAM, ANALYST, requirement, model='gpt-3.5-turbo', majority=1, max_tokens=512,
                                temperature=0.0, top_p=0.95):
        self.model = model
        self.majority = majority
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.history_message = []

        self.itf = interface.ProgramInterface(
            stop='',
            verbose=False,
            model = self.model,
        )

        system_message = construct_system_message(requirement, ANALYST, TEAM)
        self.history_message_append(system_message)


    def analyze(self):
        try:
            responses = self.itf.run(prompt=self.history_message, majority_at = self.majority, max_tokens=self.max_tokens, temperature=self.temperature, top_p=self.top_p)
        except Exception as e:
            print(e)
            print("analyze fail")
            time.sleep(5)
            return "error"

        plan = responses[0]

        self.history_message_append(plan, "assistant")
    
        return plan
    
    def history_message_append(self, system_message, role="user"):
        self.history_message.append({
            "role": role,
            "content": system_message
        })


