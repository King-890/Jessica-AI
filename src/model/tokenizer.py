import torch
from typing import List, Union

class SimpleTokenizer:
    """
    A simple character-level tokenizer for 'from scratch' implementation.
    Maps characters to integers and vice versa.
    """
    def __init__(self):
        # Default vocabulary (printable ASCII)
        chars = sorted(list(set("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~ \t\n\r")))
        self.vocab_size = len(chars) + 1  # +1 for unknown/padding
        
        self.stoi = {ch: i+1 for i, ch in enumerate(chars)}
        self.itos = {i+1: ch for i, ch in enumerate(chars)}
        self.stoi['<pad>'] = 0
        self.itos[0] = '<pad>'
        
        # Special tokens
        self.pad_token_id = 0
        
    def encode(self, text: str) -> List[int]:
        """Convert string to list of integers"""
        return [self.stoi.get(c, 0) for c in text]
        
    def decode(self, indices: Union[List[int], torch.Tensor]) -> str:
        """Convert list of integers or tensor to string"""
        if isinstance(indices, torch.Tensor):
            indices = indices.tolist()
        return "".join([self.itos.get(i, "") for i in indices if i != 0])

    def save(self, path: str):
        # For a simple tokenizer, we just assume standard ascii
        pass
    
    def load(self, path: str):
        pass
