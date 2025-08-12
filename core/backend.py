import openai
from openai import OpenAI
import time
import os
import httpx
import json
import tiktoken


def count_tokens(messages, model="gpt-3.5-turbo"):
    """Calculate the number of tokens in messages"""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    
    num_tokens = 0
    for message in messages:
        if isinstance(message, dict):
            # ChatGPT format
            num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
            for key, value in message.items():
                if isinstance(value, str):
                    num_tokens += len(encoding.encode(value))
                if key == "name":  # if there's a name, the role is omitted
                    num_tokens += -1  # role is always required and always 1 token
        elif isinstance(message, str):
            num_tokens += len(encoding.encode(message))
    
    num_tokens += 2  # every reply is primed with <im_start>assistant
    return num_tokens


def adjust_max_tokens(messages, model='gpt-3.5-turbo', desired_max_tokens=4096):
    """Intelligently adjust max_tokens to avoid exceeding model limits"""
    
    # Context length limits for different models
    model_limits = {
        'gpt-3.5-turbo': 16385,
        'gpt-3.5-turbo-0301': 4096,
        'gpt-3.5-turbo-0613': 4096,
        'gpt-3.5-turbo-16k': 16385,
        'gpt-4': 8192,
        'gpt-4-0314': 8192,
        'gpt-4-0613': 8192,
        'gpt-4-32k': 32768,
        'gpt-4-1106-preview': 128000,
        'gpt-4-turbo': 128000,
    }
    
    # Get the maximum context length for the model
    max_context_length = model_limits.get(model, 16385)  # Default to gpt-3.5-turbo limit
    
    # Calculate input message token count
    input_tokens = count_tokens(messages, model)
    
    # Calculate available tokens, leaving some margin
    available_tokens = max_context_length - input_tokens - 100  # Leave 100 tokens margin
    
    # Adjust max_tokens
    if available_tokens <= 0:
        print(f"⚠️ Warning: Input too long ({input_tokens} tokens), truncating...")
        # If input is too long, truncate message history
        adjusted_max_tokens = min(512, max_context_length // 4)  # Use minimum output tokens
        truncated_messages = truncate_messages(messages, max_context_length - adjusted_max_tokens - 100)
        return truncated_messages, adjusted_max_tokens
    else:
        # Use smaller value: desired max_tokens or available token count
        adjusted_max_tokens = min(desired_max_tokens, available_tokens)
        print(f"📊 Token info: Input={input_tokens}, Available={available_tokens}, Using={adjusted_max_tokens}")
        return messages, max(adjusted_max_tokens, 256)  # Use at least 256 tokens


def truncate_messages(messages, max_tokens):
    """Truncate message history to fit token limit"""
    if not messages:
        return messages
    
    # Keep system messages and latest user messages
    truncated = []
    
    # If first message is system message, keep it
    if messages and isinstance(messages[0], dict) and messages[0].get('role') == 'system':
        truncated.append(messages[0])
        remaining_messages = messages[1:]
    else:
        remaining_messages = messages
    
    # Start from latest messages, add messages forward until token limit reached
    current_tokens = count_tokens(truncated)
    for message in reversed(remaining_messages):
        message_tokens = count_tokens([message])
        if current_tokens + message_tokens <= max_tokens:
            truncated.insert(-1 if truncated and truncated[0].get('role') == 'system' else 0, message)
            current_tokens += message_tokens
        else:
            break
    
    print(f"📝 Truncated messages: {len(messages)} -> {len(truncated)} messages")
    return truncated


def call_chatgpt(prompt, model='gpt-3.5-turbo', stop=None, temperature=0., top_p=0.95,
        max_tokens=128, echo=False, majority_at=None):
    
    client = OpenAI()
    
    # Intelligently adjust token count
    adjusted_prompt, adjusted_max_tokens = adjust_max_tokens(prompt, model, max_tokens)
    
    num_completions = majority_at if majority_at is not None else 1
    num_completions_batch_size = 10

    completions = []
    for i in range(20 * (num_completions // num_completions_batch_size + 1)):
        try:
            requested_completions = min(num_completions_batch_size, num_completions - len(completions))

            response = client.chat.completions.create(
                model=model,
                messages=adjusted_prompt,
                max_tokens=adjusted_max_tokens,
                temperature=temperature,
                top_p=top_p,
                n=requested_completions
            )
            completions.extend([choice.message.content for choice in response.choices])
            if len(completions) >= num_completions:
                return completions[:num_completions]
        
        except openai.BadRequestError as e:
            error_message = str(e)
            if "context_length_exceeded" in error_message or "maximum context length" in error_message:
                print(f"🔄 Context length exceeded, reducing max_tokens from {adjusted_max_tokens} to {adjusted_max_tokens // 2}")
                adjusted_max_tokens = max(adjusted_max_tokens // 2, 256)
                # Further truncate messages
                adjusted_prompt, adjusted_max_tokens = adjust_max_tokens(
                    adjusted_prompt, model, adjusted_max_tokens
                )
                continue
            else:
                print(f"❌ API Error: {error_message}")
                raise e
        
        except openai.RateLimitError as e:
            print(f"⏳ Rate limit hit, waiting {min(i**2, 60)} seconds...")
            time.sleep(min(i**2, 60))
        
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            if i < 3:  # First 3 attempts try reducing token count
                adjusted_max_tokens = max(adjusted_max_tokens // 2, 256)
                print(f"🔄 Retrying with reduced max_tokens: {adjusted_max_tokens}")
                continue
            else:
                raise e
    
    raise RuntimeError('Failed to call GPT API after multiple attempts')