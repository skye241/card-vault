"""Local Moondream reads through Ollama. Used by the evaluation script."""

import base64

import ollama


def run_moondream(image_bytes: bytes, prompt: str) -> str:
    """Ask the local Moondream model to read a photo. Returns the reply text."""
    response = ollama.chat(
        model="moondream",
        messages=[{
            "role": "user",
            "content": prompt,
            "images": [base64.b64encode(image_bytes).decode("ascii")],
        }],
    )
    return response["message"]["content"]
