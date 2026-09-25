# core/llm.py
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("NEBIUS_API_KEY"),
    base_url="https://api.tokenfactory.nebius.com/v1/"
)

# Exact model IDs from your Nebius account
MODELS = {
    "nano":  "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B",   # Fast, cheap — parallel scanning
    "super": "nvidia/nemotron-3-super-120b-a12b",        # Smart — blast radius analysis
    "ultra": "nvidia/Nemotron-3-Ultra-550b-a55b",        # Deepest reasoning — strategy
}

def call_llm(
    prompt: str,
    model: str = "super",
    system: str = "You are DriftWatch, an expert infrastructure intelligence agent.",
    max_tokens: int = 2048,
    temperature: float = 0.2,
) -> str:
    model_id = MODELS.get(model, MODELS["super"])
    
    response = client.chat.completions.create(
        model=model_id,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": prompt},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    
    # Defensive extraction — handles models that return
    # content in different structures
    choice = response.choices[0]
    
    # Standard content
    if choice.message.content:
        return choice.message.content.strip()
    
    # Some reasoning models return in reasoning_content instead
    if hasattr(choice.message, "reasoning_content") and choice.message.reasoning_content:
        return choice.message.reasoning_content.strip()
    
    # Fallback: print raw response for debugging
    print(f"DEBUG raw response: {response}")
    return ""


def call_llm_with_history(
    messages: list[dict],
    model: str = "super",
    max_tokens: int = 2048,
    temperature: float = 0.2,
) -> str:
    model_id = MODELS.get(model, MODELS["super"])
    
    response = client.chat.completions.create(
        model=model_id,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    
    return response.choices[0].message.content.strip()

import re

def strip_thinking(text: str) -> str:
    """Remove <think>...</think> blocks from reasoning model outputs."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    return text.strip()