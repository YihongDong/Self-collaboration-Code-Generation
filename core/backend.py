import openai
from openai import OpenAI
import time
import os


def call_chatgpt(prompt, model='code-davinci-002', stop=None, temperature=0., top_p=1.0,
        max_tokens=128, echo=False, majority_at=None):

    client = OpenAI()
    num_completions = majority_at if majority_at is not None else 1
    num_completions_batch_size = 10

    completions = []
    for i in range(20 * (num_completions // num_completions_batch_size + 1)):
        try:
            requested_completions = min(num_completions_batch_size, num_completions - len(completions))

            response = client.chat.completions.create(
            model=model,
            messages=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            n=requested_completions
            )
            completions.extend([choice.message.content for choice in response.choices])
            if len(completions) >= num_completions:
                return completions[:num_completions]
        except openai.RateLimitError as e:
            time.sleep(min(i**2, 60))
    raise RuntimeError('Failed to call GPT API')


def _extract_code_from_reasoning(reasoning):
    """Try to extract a Python code block from a reasoning/thinking chain.
    Returns the code if found, otherwise returns empty string."""
    import re
    # Look for markdown code blocks in the reasoning
    for m in re.finditer(r"```(?:python)?\s*\n(.*?)```", reasoning, re.DOTALL):
        candidate = m.group(1).strip()
        if "def " in candidate:
            return candidate
    # Look for a def block without markdown fences
    idx = reasoning.rfind("\ndef ")
    if idx != -1:
        block = reasoning[idx + 1:]
        # Take lines until we hit a non-indented non-def line
        lines = []
        in_func = False
        for line in block.split("\n"):
            if line.startswith("def "):
                in_func = True
            elif in_func and line.strip() and not line[0].isspace():
                break
            if in_func:
                lines.append(line)
        if lines:
            return "\n".join(lines)
    return ""


def call_llm(prompt, config, majority_at=None):
    """Model-agnostic LLM call using ModelConfig. Supports OpenRouter and any OpenAI-compatible API."""
    from core.config import ModelConfig

    api_key = os.environ.get(config.api_key_env, "")
    client = OpenAI(base_url=config.base_url, api_key=api_key)

    num_completions = majority_at if majority_at is not None else 1
    num_completions_batch_size = 10

    completions = []
    for i in range(20 * (num_completions // num_completions_batch_size + 1)):
        try:
            requested_completions = min(num_completions_batch_size, num_completions - len(completions))

            response = client.chat.completions.create(
                model=config.model,
                messages=prompt,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                top_p=config.top_p,
                n=requested_completions,
            )
            for choice in response.choices:
                content = choice.message.content
                # For thinking/reasoning models: content may be None when
                # reasoning tokens consumed the entire max_tokens budget.
                # Try to extract code from reasoning as last resort.
                if not content:
                    reasoning = getattr(choice.message, 'reasoning', None) or ""
                    content = _extract_code_from_reasoning(reasoning)
                completions.append(content)
            if len(completions) >= num_completions:
                return completions[:num_completions]
        except openai.RateLimitError as e:
            time.sleep(min(i**2, 60))
    raise RuntimeError('Failed to call LLM API')


def call_llm_with_tools(messages, config, tools=None):
    """LLM call with native tool use support.

    Returns the full API response (not just completions) so callers can
    inspect tool_calls on the assistant message.
    """
    api_key = os.environ.get(config.api_key_env, "")
    client = OpenAI(base_url=config.base_url, api_key=api_key)

    for attempt in range(3):
        try:
            kwargs = dict(
                model=config.model,
                messages=messages,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
            )
            if tools:
                kwargs["tools"] = tools
            response = client.chat.completions.create(**kwargs)
            return response
        except openai.RateLimitError:
            time.sleep(min(2 ** attempt * 2, 60))
        except openai.APIError as e:
            if attempt == 2:
                raise
            time.sleep(2)
    raise RuntimeError("Failed to call LLM API with tools")