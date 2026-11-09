import ollama
import base64



def _mime(image_bytes: bytes) -> str:
    if image_bytes.startswith(b"\x89PNG"):
        return "image/png"
    if image_bytes.startswith(b"RIFF") and image_bytes[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


def run_moondream(image_bytes: bytes, prompt: str) -> str:
    mime = _mime(image_bytes)
    encoded = base64.b64encode(image_bytes).decode("ascii")

    response = ollama.chat(
        model="moondream",
        messages=[{
            "role": "user",
            "content": prompt,
            "images": [encoded]
        }]
        
    )

    print(response['message']['content'])
    return response['message']['content']