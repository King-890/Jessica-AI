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
            
    print(f"💾 Saved {count} training samples to {output_file}")
    print("👉 Now update src/train.py to load this file!")

if __name__ == "__main__":
    fetch_coding_data()
