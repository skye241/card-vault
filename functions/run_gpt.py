"""Send one slab photo to GPT-4o mini through OpenRouter."""

import base64
import os
from pathlib import Path
import streamlit as st
from openai import OpenAI

import requests

MODEL_ID = "openai/gpt-4o-mini"
_URL = "https://openrouter.ai/api/v1/chat/completions"

def _api_key() -> str:
    api_key = st.secrets["OPENROUTER_API_KEY"]

    if api_key is None:
        raise RuntimeError("No API key")

    return api_key



def _mime(image_bytes: bytes) -> str:
    if image_bytes.startswith(b"\x89PNG"):
        return "image/png"
    if image_bytes.startswith(b"RIFF") and image_bytes[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


def run_gpt(image_bytes: bytes, prompt: str) -> str:
    """Ask GPT-4o mini to read an encoded image file. Returns the reply text."""
    mime = _mime(image_bytes)
    encoded = base64.b64encode(image_bytes).decode("ascii")
    client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=_api_key(),
)
    response = client.chat.completions.create(
        model=MODEL_ID,
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

