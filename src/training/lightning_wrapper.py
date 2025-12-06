import pytorch_lightning as pl
from torch.utils.data import DataLoader
from src.model.transformer import JessicaGPT
from src.training.dataset import DatasetBuilder, TextDataset
from src.model.tokenizer import SimpleTokenizer

class TrainingModule(pl.LightningModule):
    """
    Wrapper to handle the training loop configuration.
    """
    def __init__(self, model: JessicaGPT, train_dataset: TextDataset, batch_size: int = 4):
        super().__init__()
        self.model = model
        self.train_dataset = train_dataset
        self.batch_size = batch_size

    def train_dataloader(self):
        return DataLoader(self.train_dataset, batch_size=self.batch_size, shuffle=True, num_workers=0) # 0 workers for Win compatibility

    def training_step(self, batch, batch_idx):
        return self.model.training_step(batch, batch_idx)

    def configure_optimizers(self):
        return self.model.configure_optimizers()
