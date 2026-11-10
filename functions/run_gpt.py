"""Send one slab photo to Gemini 2.5 Flash through OpenRouter."""

import base64
import os
from pathlib import Path
import streamlit as st
from openai import OpenAI

import requests

MODEL_ID = "google/gemini-2.5-flash"
_URL = "https://openrouter.ai/api/v1/chat/completions"

def _api_key() -> str:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        api_key = st.secrets["OPENROUTER_API_KEY"]
    if not api_key:
        raise RuntimeError("No API key")
    return api_key



def _mime(image_bytes: bytes) -> str:
    if image_bytes.startswith(b"\x89PNG"):
        return "image/png"
    if image_bytes.startswith(b"RIFF") and image_bytes[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


def run_gpt(image_bytes: bytes, prompt: str, model: str = MODEL_ID) -> str:
    """Ask the vision model to read an encoded image file. Returns the reply text."""
    mime = _mime(image_bytes)
    encoded = base64.b64encode(image_bytes).decode("ascii")
    client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=_api_key(),
)
    response = client.chat.completions.create(
        model=model,
        max_tokens=400,
        messages= [
            {
                "role": "user",
                "content": [{
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime};base64,{encoded}"}
                }
                ]
            },
           
        ],
    )
    return response.choices[0].message.content


def run_gpt_logprobs(image_bytes: bytes, prompt: str, model: str = MODEL_ID) -> tuple[str, list[dict]]:
    """Same call as run_gpt, plus the probability of each generated token."""
    mime = _mime(image_bytes)
    encoded = base64.b64encode(image_bytes).decode("ascii")
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=_api_key())
    response = client.chat.completions.create(
        model=model,
        max_tokens=400,
        logprobs=True,
        top_logprobs=1,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{encoded}"}},
            ],
        }],
    )
    choice = response.choices[0]
    tokens = []
    content_logprobs = choice.logprobs.content if choice.logprobs else []
    for item in content_logprobs or []:
        tokens.append({"token": item.token, "logprob": item.logprob})
    return choice.message.content or "", tokens

