import pytorch_lightning as pl
import torch
from torch.utils.data import DataLoader
from src.model.transformer import JessicaGPT
from src.training.dataset import DatasetBuilder, TextDataset
from src.model.tokenizer import SimpleTokenizer

class JessicaLightningModule(pl.LightningModule):
    """
    Wrapper to handle the training loop configuration.
    """
    def __init__(self, model: JessicaGPT, dataset=None, batch_size=2, learning_rate: float = 1e-4):
        super().__init__()
        self.model = model
        self.learning_rate = learning_rate
        self.train_dataset = dataset
        self.batch_size = batch_size

    def train_dataloader(self):
        return DataLoader(self.train_dataset, batch_size=self.batch_size, shuffle=True, num_workers=0) # 0 workers for Win compatibility

    def training_step(self, batch, batch_idx):
        loss = self.model.training_step(batch, batch_idx)
        self.log('train_loss', loss, prog_bar=True)
        return loss

    def configure_optimizers(self):
        return torch.optim.AdamW(self.model.parameters(), lr=self.learning_rate)
