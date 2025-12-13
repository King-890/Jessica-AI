
import os
import time
import math
import torch
import torch.nn as nn
from torch.nn import functional as F
from src.model.transformer import JessicaModel, JessicaConfig
from src.model.tokenizer import SimpleTokenizer # We will expand this
from src.backend.cloud.supabase_client import get_client, upload_file

# --- Hyperparameters ---
batch_size = 32 # How many independent sequences will we process in parallel?
block_size = 256 # What is the maximum context length for predictions?
max_iters = 5000
eval_interval = 300
learning_rate = 3e-4
device = 'cuda' if torch.cuda.is_available() else 'cpu'
eval_iters = 200
n_embd = 384
n_head = 6
n_layer = 6
# -----------------------

print(f"Using device: {device}")

# NOTE: For now, we will grab a dummy text file to train on
# In reality, this will pull from 'training_data/' folder
def get_batch(split):
    # generate a small batch of data of inputs x and targets y
    data = torch.randint(0, 1000, (batch_size, block_size)) # Dummy data for skeleton
    x = torch.stack([d[:-1] for d in data])
    y = torch.stack([d[1:] for d in data])
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

def train_job():
    print("Initializing Sovereign AI Training Job...")
    
    # 1. Initialize Model
    config = JessicaConfig(vocab_size=1000, n_embd=n_embd, n_head=n_head, n_layer=n_layer, block_size=block_size)
    model = JessicaModel(config)
    m = model.to(device)
    
    # 2. Optimizer
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)

    print("Starting training loop...")
    for iter in range(max_iters):

        # every once in a while evaluate the loss on train and val sets
        if iter % eval_interval == 0:
            losses = estimate_loss(model)
            print(f"step {iter}: train loss {losses['train']:.4f}")

        # sample a batch of data
        xb, yb = get_batch('train')

        # evaluate the loss
        logits, loss = model(xb, yb)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()
        
    print("Training complete!")
    
    # 3. Save Model
    timestamp = str(int(time.time()))
    filename = f"jessica_zero_v1_{timestamp}.pth"
    torch.save(model.state_dict(), filename)
    print(f"Model saved locally: {filename}")
    
    # 4. Upload to Cloud (Supabase)
    try:
        bucket = "models"
        print(f"Uploading to Supabase bucket '{bucket}'...")
        # upload_file(bucket, filename, filename) # Need to implement large file upload logic later
        print("Upload logic check complete.")
    except Exception as e:
        print(f"Upload failed: {e}")

if __name__ == "__main__":
    train_job()
