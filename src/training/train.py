
import os
import time
import math
import torch
import torch.nn as nn
from torch.nn import functional as F
from src.model.transformer import JessicaModel, JessicaConfig
from src.backend.cloud.supabase_client import get_client, upload_file

# --- Hyperparameters ---
batch_size = 32
block_size = 128 # Reduced for faster initial convergence
max_iters = 5000
eval_interval = 100
learning_rate = 3e-4
device = 'cuda' if torch.cuda.is_available() else 'cpu'
eval_iters = 200
n_embd = 256 # Reduced for "Nano" version speed
n_head = 4
n_layer = 4
# -----------------------

print(f"Using device: {device}")

def train_job():
    print("Initializing Sovereign AI Training Job...")
    
    # 1. Load Data
    data_path = 'training_data/corpus.txt'
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found. Run data_miner.py first!")
        return

    print("Loading corpus...")
    with open(data_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # 2. Tokenizer (Character Level)
    chars = sorted(list(set(text)))
    vocab_size = len(chars)
    print(f"Corpus Length: {len(text)} chars | Vocab Size: {vocab_size} unique chars")
    
    stoi = { ch:i for i,ch in enumerate(chars) }
    itos = { i:ch for i,ch in enumerate(chars) }
    encode = lambda s: [stoi[c] for c in s]
    decode = lambda l: ''.join([itos[i] for i in l])

    # Train/Test Split
    data = torch.tensor(encode(text), dtype=torch.long)
    n = int(0.9 * len(data))
    train_data = data[:n]
    val_data = data[n:]

    def get_batch(split):
        data = train_data if split == 'train' else val_data
        ix = torch.randint(len(data) - block_size, (batch_size,))
        x = torch.stack([data[i:i+block_size] for i in ix])
        y = torch.stack([data[i+1:i+block_size+1] for i in ix])
        x, y = x.to(device), y.to(device)
        return x, y

    @torch.no_grad()
    def estimate_loss(model):
        out = {}
        model.eval()
        losses = torch.zeros(eval_iters)
        for k in range(eval_iters):
            X, Y = get_batch('train')
            logits, loss = model(X, Y)
            losses[k] = loss.item()
        out['train'] = losses.mean()
        model.train()
        return out

    # 3. Model Init
    print("Building Neural Network...")
    config = JessicaConfig(vocab_size=vocab_size, n_embd=n_embd, n_head=n_head, n_layer=n_layer, block_size=block_size)
    model = JessicaModel(config)
    m = model.to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)

    print(f"Starting Training Loop ({max_iters} steps)...")
    start_time = time.time()
    for iter in range(max_iters):

        if iter % eval_interval == 0:
            losses = estimate_loss(model)
            print(f"step {iter}: train loss {losses['train']:.4f}")

        xb, yb = get_batch('train')
        logits, loss = model(xb, yb)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()
        
    print(f"Training complete! Time: {time.time() - start_time:.2f}s")
    
    # 4. Save
    timestamp = str(int(time.time()))
    filename = f"jessica_nano_v1_{timestamp}.pth"
    torch.save(model.state_dict(), filename)
    print(f"Model saved: {filename}")
    
    # 5. Generate Proof of Intelligence
    print("\n--- Generating Sample Text ---")
    context = torch.zeros((1, 1), dtype=torch.long, device=device)
    generated_indices = m.generate(context, max_new_tokens=200)[0].tolist()
    print(decode(generated_indices))
    print("------------------------------")

if __name__ == "__main__":
    train_job()
