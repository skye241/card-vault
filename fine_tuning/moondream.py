import os
import time
from itertools import cycle

from datasets import load_dataset
import moondream as md


QUESTION = """Examine this trading card photo. Return only a JSON object with keys "
    "is_graded, company, grade, cert_number, card_name, year, collection_name, "
    "and variant. is_graded is true only when the card is in a professional "
    "grading slab. year is the four-digit year. collection_name is the set name. "
    "variant is the printed finish, such as Holo, Gold Star, Reverse Holo, "
    "Full Art, SIR, or SAR. Use an empty string when a field is not visible."
)"""

# eval_data = load_dataset("/moondream_finetune.jsonl", split="valid")
train_data = load_dataset("json", data_files="fine_tuning/moondream_finetune.jsonl", split="train")




def fine_tune():
    ft = md.ft(
        api_key=os.environ["MOONDREAM_API_KEY"],
        name=f"rps-query-{int(time.time())}",
        rank=8,
    )
    print(f"Created finetune: {ft.finetune_id}")
    train_iter = cycle(train_data)

    for i in range(20):
        
        example = next(train_iter)

        # Generate 4 rollouts
        response = ft.rollouts(
            "query",
            image=example["image"],
            question=QUESTION,
            num_rollouts=4,
            settings={"temperature": 0.0, "max_tokens": 4},
        )

        # Score: 1.0 if correct, 0.0 if not
        rewards = [
            float(r["output"]["answer"].strip().lower() == example["class"])
            for r in response["rollouts"]
        ]

        # Train
        step = ft.train_step([{
            "mode": "rl",
            "request": response["request"],
            "rollouts": response["rollouts"],
            "rewards": rewards,
        }], lr=2e-4)

        print(f"step={step['step']} reward={sum(rewards)/len(rewards):.2f}")


if __name__ == "__main__":
    fine_tune()
