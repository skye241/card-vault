"""Send one slab photo to a vision model through OpenRouter."""

import base64
import math
import os
import re
from io import BytesIO
from pathlib import Path

import streamlit as st
from openai import OpenAI
from PIL import Image

import requests

#MODEL_ID = "google/gemini-2.5-flash"#
MODEL_ID="openai/gpt-4o"
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



def crop_top(image_bytes: bytes, ratio: float = 0.3) -> bytes:
    """Keep the top portion of a photo. ratio=0.3 keeps the top 30%."""
    image = Image.open(BytesIO(image_bytes))
    width, height = image.size
    cropped = image.crop((0, 0, width, max(1, round(height * ratio))))
    buffer = BytesIO()
    image_format = image.format or "JPEG"
    if image_format == "JPEG" and cropped.mode != "RGB":
        cropped = cropped.convert("RGB")
    cropped.save(buffer, format=image_format)
    return buffer.getvalue()


def _mime(image_bytes: bytes) -> str:
    if image_bytes.startswith(b"\x89PNG"):
        return "image/png"
    if image_bytes.startswith(b"RIFF") and image_bytes[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


def _value_spans(text: str) -> dict[str, tuple[int, int]]:
    spans = {}
    for match in re.finditer(r'"([A-Za-z0-9_]+)"\s*:\s*', text):
        start = match.end()
        rest = text[start:]
        if rest.startswith('"'):
            index = 1
            while index < len(rest):
                if rest[index] == "\\":
                    index += 2
                    continue
                if rest[index] == '"':
                    spans[match.group(1)] = (start, start + index + 1)
                    break
                index += 1
            continue
        value = re.match(r"true|false|null|-?\d+(?:\.\d+)?", rest)
        if value:
            spans[match.group(1)] = (start, start + value.end())
    return spans


def _field_confidence(text: str, tokens: list[dict]) -> dict[str, float]:
    """Lowest token probability inside each JSON value. Empty when the model returns none."""
    cursor = 0
    ranges = []
    for token in tokens:
        piece = token["token"]
        ranges.append((cursor, cursor + len(piece), math.exp(token["logprob"])))
        cursor += len(piece)
    if "".join(token["token"] for token in tokens) != text:
        return {}
    scores = {}
    for field, (start, end) in _value_spans(text).items():
        probs = [prob for left, right, prob in ranges if left < end and right > start]
        if probs:
            scores[field] = round(min(probs), 3)
    return scores


def read_image(image_bytes: bytes, prompt: str, model: str = MODEL_ID, top_ratio: float | None = None) -> dict:
    """Read a photo and return the reply, per-field confidence, and prompt tokens."""
    if top_ratio is not None:
        image_bytes = crop_top(image_bytes, top_ratio)
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
    text = choice.message.content or ""
    tokens = []
    for item in (choice.logprobs.content if choice.logprobs else []) or []:
        tokens.append({"token": item.token, "logprob": item.logprob})
    confidence = _field_confidence(text, tokens)
    probs = [math.exp(token["logprob"]) for token in tokens]
    return {
        "text": text,
        "tokens": tokens,
        "field_confidence": confidence,
        "answer_confidence": round(sum(probs) / len(probs), 3) if probs else None,
        "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
    }


def run_gpt(image_bytes: bytes, prompt: str, model: str = MODEL_ID, top_ratio: float | None = None) -> str:
    """Ask the vision model to read an encoded image file. Returns the reply text."""
    return read_image(image_bytes, prompt, model=model)["text"]


def run_gpt_logprobs(image_bytes: bytes, prompt: str, model: str = MODEL_ID) -> tuple[str, list[dict]]:
    """Same call as run_gpt, plus the probability of each generated token."""
    reading = read_image(image_bytes, prompt, model=model)
    return reading["text"], reading["tokens"]

