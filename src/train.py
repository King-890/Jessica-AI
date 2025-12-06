import sys
import os
import yaml
import torch
from pathlib import Path

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.brain import Brain
from src.core.mcp_host import MCPHost
from src.training.dataset import DatasetBuilder
from src.training.lightning_wrapper import JessicaLightningModule
import pytorch_lightning as pl

def load_config():
    config_path = Path("config.yaml")
    if config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return {}

def main():
    print("⚡ Starting Jessica AI Cloud Training ⚡")
    
    # 1. Setup
    config = load_config()
    # Minimal Mock for Brain deps (we only need the model)
    brain = Brain(config, mcp_host=None, rag_manager=None)
    
    # 2. Prepare Data
    print("📊 Preparing Dataset...")
    # In cloud, we might check for a specific data folder
    builder = DatasetBuilder(brain.tokenizer)
    # Force some dummy data if empty for testing, or load from file
    if len(builder.interactions) == 0:
        print("   Warning: No interaction history found. Utilizing dummy data for dry-run.")
        builder.add_interaction("Hello", "Hi there, I am Jessica.")
        builder.add_interaction("Build empire", "Initializing empire building protocols.")
        
    dataset = builder.build_dataset(brain.tokenizer)
    dataloader = torch.utils.data.DataLoader(dataset, batch_size=2, shuffle=True)
    
    # 3. Initialize Training Module
    print("🧠 Initializing Lightning Module...")
    model = JessicaLightningModule(brain.local_model, learning_rate=1e-4)
    
    # 4. Trainer
    # Detect GPU
    accelerator = "gpu" if torch.cuda.is_available() else "cpu"
    devices = 1
    print(f"⚙️  Accelerator: {accelerator}")
    
    trainer = pl.Trainer(
        max_epochs=5,
        accelerator=accelerator,
        devices=devices,
        enable_checkpointing=True,
        default_root_dir="checkpoints"
    )
    
    # 5. Train
    print("🚀 Starting Training Loop...")
    trainer.fit(model, dataloader)
    
    print("✅ Training Complete.")
    
    # 6. Save (Simple save)
    output_path = "jessica_model_cloud.pt"
    torch.save(brain.local_model.state_dict(), output_path)
    print(f"💾 Model saved to {output_path}")

if __name__ == "__main__":
    main()
