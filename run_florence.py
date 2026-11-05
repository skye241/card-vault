import io

import torch
from PIL import Image
from transformers import AutoProcessor, AutoModelForCausalLM

# 1. Setup compute device and precision
device = "cuda" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

# Choose model: "microsoft/Florence-2-base" or "microsoft/Florence-2-large"
model_id = "microsoft/Florence-2-base"

print(f"Loading Florence-2 on {device}...")
model = AutoModelForCausalLM.from_pretrained(
    model_id, 
    torch_dtype=torch_dtype, 
    trust_remote_code=True  # Required for Florence-2 custom architecture
).to(device)

processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)


def run_florence_task(image_bytes: bytes, task_prompt: str, text_input: str = ""):
    """Run a Florence-2 task. image_bytes is an encoded image file (JPEG, PNG, WebP)."""
    try:
        # frombytes() expects raw pixels plus a size, not a compressed file.
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        # <OCR> takes no extra text. text_input is only for tasks such as phrase grounding.
        prompt = task_prompt + text_input

    # Prepare inputs
        inputs = processor(text=prompt, images=image, return_tensors="pt").to(device, torch_dtype)

    # Generate output token IDs
        generated_ids = model.generate(
            input_ids=inputs["input_ids"],
            pixel_values=inputs["pixel_values"],
            max_new_tokens=1024,
            num_beams=3,
            do_sample=False
        )

        # Decode text output
        generated_text = processor.batch_decode(generated_ids, skip_special_tokens=False)[0]

        # Post-process raw text output into structured Python dicts
        parsed_result = processor.post_process_generation(
            generated_text, 
            task=task_prompt, 
            image_size=(image.width, image.height)
        )
        print(parsed_result)
        return parsed_result
    except (OSError, ValueError) as e:
        print(f"Error! {e}")


# # --- Quick Test ---
# if __name__ == "__main__":
#     # Test with OCR task on a local image
#     image_file = "data/images/graded-pokemon.jpg"  # Replace with your test image path
    
#     # Extract plain text (OCR)
#     ocr_result = run_florence_task(image_file, "<OCR>")
#     print("OCR Output:\n", ocr_result)

#     # Extract text with bounding box coordinates (useful for slab headers)
#     ocr_region_result = run_florence_task(image_file, "<OCR_WITH_REGION>")
#     print("\nOCR with BBoxes Output:\n", ocr_region_result)