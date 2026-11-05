"""Local Qwen2-VL-2B-Instruct call for one slab photo."""

import io

import torch
from PIL import Image
from transformers import AutoProcessor, Qwen2VLForConditionalGeneration

MODEL_ID = "Qwen/Qwen2-VL-2B-Instruct"

if torch.cuda.is_available():
    device = "cuda"
elif torch.backends.mps.is_available():
    device = "mps"
else:
    device = "cpu"
torch_dtype = torch.float32 if device == "cpu" else torch.float16

_model = None
_processor = None


def _load():
    global _model, _processor
    if _model is not None:
        return
    print(f"Loading {MODEL_ID} on {device}...")
    _model = Qwen2VLForConditionalGeneration.from_pretrained(
        MODEL_ID,
        torch_dtype=torch_dtype,
    ).to(device)
    _processor = AutoProcessor.from_pretrained(MODEL_ID)


def run_qwen(image_bytes: bytes, prompt: str) -> str:
    """Ask Qwen2-VL about an encoded image file. Returns the reply text."""
    _load()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image"},
                {"type": "text", "text": prompt},
            ],
        }
    ]
    text = _processor.apply_chat_template(messages, add_generation_prompt=True)
    inputs = _processor(text=[text], images=[image], return_tensors="pt")
    inputs = inputs.to(device)
    inputs["pixel_values"] = inputs["pixel_values"].to(dtype=torch_dtype)

    generated = _model.generate(**inputs, max_new_tokens=256, do_sample=False)
    trimmed = [out[len(inp):] for inp, out in zip(inputs.input_ids, generated)]
    return _processor.batch_decode(trimmed, skip_special_tokens=True)[0]
