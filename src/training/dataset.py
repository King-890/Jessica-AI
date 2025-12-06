import torch
from torch.utils.data import Dataset, DataLoader
from typing import List
from src.model.tokenizer import SimpleTokenizer
import json
from pathlib import Path

class TextDataset(Dataset):
    """
    PyTorch Dataset for text training.
    """
    def __init__(self, data: List[str], tokenizer: SimpleTokenizer, block_size: int):
        self.tokenizer = tokenizer
        self.block_size = block_size
        
        # Simple concatenation strategy
        text = "\n".join(data)
        self.tokens = tokenizer.encode(text)
        print(f"Dataset loaded with {len(self.tokens)} tokens.")

    def __len__(self):
        return len(self.tokens) - self.block_size

    def __getitem__(self, idx):
        # chunk of length block_size + 1
        chunk = self.tokens[idx : idx + self.block_size + 1]
        x = torch.tensor(chunk[:-1], dtype=torch.long)
        y = torch.tensor(chunk[1:], dtype=torch.long)
        return x, y

class DatasetBuilder:
    """
    Builds datasets from RAG index or gathered data.
    """
    def __init__(self, tokenizer: SimpleTokenizer):
        self.tokenizer = tokenizer
        
    def from_jsonl(self, file_path: str, block_size: int = 128) -> TextDataset:
        """Load from DataCollector JSONL files"""
        data = []
        path = Path(file_path)
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        # Learn from both user (questions) and assistant (responses)
                        data.append(entry.get('user', ''))
                        data.append(entry.get('assistant', ''))
                    except:
                        pass
        return TextDataset(data, self.tokenizer, block_size)

    def from_rag(self, vector_store, block_size: int = 128) -> TextDataset:
        """
        Load training data directly from RAG Vector Store documents.
        This is "Pre-training" on the knowledge base.
        """
        # This assumes vector store has a way to iterate docs.
        # For simplicity, we just use a placeholder text if store not accessible provided
        data = ["Jessica AI is a helpful assistant.", "Code is law."]
        if hasattr(vector_store, 'documents'):
            data.extend([doc.page_content for doc in vector_store.documents])
            
        return TextDataset(data, self.tokenizer, block_size)
