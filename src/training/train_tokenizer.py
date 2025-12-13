
"""
Train a Byte-Pair Encoding (BPE) Tokenizer on the corpus.
Based on minBPE (Andrej Karpathy).
"""
import os
import json
import regex as re
from collections import Counter

# --- Configuration ---
CORPUS_FILE = "training_data/corpus.txt"
VOCAB_SIZE = 4096 # Target vocabulary size (Small for testing, can go to 32k+)
MODEL_NAME = "jessica_tokenizer"

# GPT-4 split pattern
PAT = re.compile(r"""'(?i:[sdmt]|ll|ve|re)|[^\r\n\p{L}\p{N}]?+\p{L}+|\p{N}{1,3}| ?[^\s\p{L}\p{N}]++[\r\n]*|\s*[\r\n]|\s+(?!\S)|\s+""")

def get_stats(ids):
    counts = {}
    for pair in zip(ids, ids[1:]):
        counts[pair] = counts.get(pair, 0) + 1
    return counts

def merge(ids, pair, idx):
    newids = []
    i = 0
    while i < len(ids):
        if i < len(ids) - 1 and ids[i] == pair[0] and ids[i+1] == pair[1]:
            newids.append(idx)
            i += 2
        else:
            newids.append(ids[i])
            i += 1
    return newids

def train_tokenizer():
    print(f"🚀 Starting Tokenizer Training (Target: {VOCAB_SIZE} tokens)...")
    
    # 1. Load Corpus
    if not os.path.exists(CORPUS_FILE):
        print(f"Error: {CORPUS_FILE} not found.")
        return

    print("Loading text...")
    with open(CORPUS_FILE, 'r', encoding='utf-8') as f:
        text = f.read()
    
    print(f"Corpus size: {len(text)} chars / {len(text.encode('utf-8'))} bytes")

    # 2. Initial encoding (UTF-8 bytes)
    tokens = [list(map(int, t.encode('utf-8'))) for t in re.findall(PAT, text)]
    # Flatten for stats (approximate, usually we preserve word boundaries but for simple BPE global stats work ok)
    # Actually, proper BPE respects regex boundaries. Let's do a simple global stream for "Sovereign AI v1"
    # To keep it simple and robust:
    ids = list(text.encode("utf-8")) # Raw byte stream BPE
    print(f"Initial tokens (bytes): {len(ids)}")

    # 3. Training Loop
    merges = {} # (int, int) -> int
    vocab = {idx: bytes([idx]) for idx in range(256)} # int -> bytes
    
    num_merges = VOCAB_SIZE - 256
    for i in range(num_merges):
        stats = get_stats(ids)
        if not stats:
            break
            
        pair = max(stats, key=stats.get)
        idx = 256 + i
        
        # print(f"Merging {pair} -> {idx} ({stats[pair]} occurrences)")
        ids = merge(ids, pair, idx)
        
        merges[pair] = idx
        vocab[idx] = vocab[pair[0]] + vocab[pair[1]]
        
        if (i+1) % 100 == 0:
            print(f"Merge {i+1}/{num_merges}: {vocab[idx]} (freq: {stats[pair]})")

    print(f"Training complete! Final vocab size: {len(vocab)}")
    
    # 4. Save
    os.makedirs("models", exist_ok=True)
    vocab_str = {idx: b.decode('utf-8', errors='replace') for idx, b in vocab.items()}
    
    # Save vocab.json
    with open(f"models/{MODEL_NAME}_vocab.json", "w", encoding="utf-8") as f:
        json.dump(vocab_str, f, indent=2, ensure_ascii=False)
        
    print(f"Saved models/{MODEL_NAME}_vocab.json")

    # Save merges (for reconstruction)
    # (Not strictly implementing save_merges here for brevity, but vocab is enough for simple inference decoding)

if __name__ == "__main__":
    train_tokenizer()
