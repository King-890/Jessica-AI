import json
import asyncio
from pathlib import Path
from datasets import load_dataset
from tqdm import tqdm

def fetch_coding_data(output_file: str = "data_code.jsonl", max_samples: int = 5000):
    """
    Downloads coding instruction dataset (Alpaca-style) and converts to Jessica's training format.
    Target Dataset: iamtarun/python_code_instructions_18k_alpaca
    """
    print(f"⬇️  Downloading Coding Dataset (Target: {max_samples} samples)...")
    
    # 1. Load Dataset from HuggingFace
    # We use a known high-quality Python instruction set
    try:
        ds = load_dataset("iamtarun/python_code_instructions_18k_alpaca", split="train")
    except Exception as e:
        print(f"❌ Error downloading dataset: {e}")
        return

    print(f"✅ Download complete. Processing...")

    # 2. Format and Save
    count = 0
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in tqdm(ds):
            if count >= max_samples:
                break
                
            instruction = item.get('instruction', '')
            input_context = item.get('input', '')
            output_code = item.get('output', '')
            
            # Construct the prompt format Jessica expects
            # User asks for code -> Jessica provides code
            if input_context:
                user_text = f"{instruction}\nContext:\n{input_context}"
            else:
                user_text = instruction
                
            entry = {
                "user": user_text,
                "assistant": output_code,
                "source": "python_alpaca"
            }
            
            f.write(json.dumps(entry) + "\n")
            count += 1
            
    print(f"💾 Saved {count} coding samples to {output_file}")
    
    # --- 2. TinyStories (Creative Writing / English Basics) ---
    print(f"⬇️  Downloading General English Dataset (TinyStories)...")
    try:
        ds_stories = load_dataset("roneneldan/TinyStories", split="train", streaming=True)
        story_count = 0
        with open("data_stories.jsonl", 'w', encoding='utf-8') as f:
            for item in ds_stories:
                if story_count >= 1000: # Small sample
                    break
                text = item.get('text', '')
                entry = {"user": "Write a story.", "assistant": text, "source": "tinystories"}
                f.write(json.dumps(entry) + "\n")
                story_count += 1
        print(f"💾 Saved {story_count} stories to data_stories.jsonl")
    except Exception as e:
        print(f"❌ Failed to download stories: {e}")

    # --- 3. Advanced Coding (Evol-Instruct - Great for Complex Tasks) ---
    print(f"⬇️  Downloading Advanced Coding Dataset (Evol-Instruct)...")
    try:
        # Using nickrosh/Evol-Instruct-Code-80k-v1 which is safe and high quality
        ds_evol = load_dataset("nickrosh/Evol-Instruct-Code-80k-v1", split="train", streaming=True)
        evol_count = 0
        with open("data_evol.jsonl", 'w', encoding='utf-8') as f:
            for item in ds_evol:
                if evol_count >= 2000: 
                    break
                
                # item keys: instruction, output
                instruction = item.get('instruction', '')
                output = item.get('output', '')

                entry = {
                    "user": instruction, 
                    "assistant": output, 
                    "source": "evol_instruct_code"
                }
                f.write(json.dumps(entry) + "\n")
                evol_count += 1
        print(f"💾 Saved {evol_count} advanced coding samples to data_evol.jsonl")
    except Exception as e:
        print(f"❌ Failed to download Evol-Instruct data: {e}")

    print("👉 Now src/train.py will automatically find ALL these .jsonl files!")

if __name__ == "__main__":
    fetch_coding_data()
