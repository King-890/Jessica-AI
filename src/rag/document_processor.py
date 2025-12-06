"""
Document Processor for RAG System
Extracts and chunks documents intelligently for indexing.
"""

import os
from pathlib import Path
from typing import List, Dict, Any
import tiktoken

class Document:
    """Represents a processed document chunk"""
    def __init__(self, content: str, metadata: Dict[str, Any]):
        self.content = content
        self.metadata = metadata
    
    def __repr__(self):
        return f"Document(path={self.metadata.get('path')}, chunk={self.metadata.get('chunk_index')})"

class DocumentProcessor:
    """Process files into chunks suitable for RAG indexing"""
    
    # Supported file extensions
    SUPPORTED_EXTENSIONS = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h',
        '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt',
        '.md', '.txt', '.yaml', '.yml', '.json', '.xml', '.html', '.css',
        '.sh', '.bat', '.ps1', '.sql'
    }
    
    # Files to ignore
    IGNORE_PATTERNS = {
        '__pycache__', '.git', '.venv', 'venv', 'node_modules',
        '.pytest_cache', '.mypy_cache', 'dist', 'build', '.egg-info'
    }
    
    def __init__(self, max_chunk_size: int = 512, overlap: int = 50):
        """
        Initialize document processor
        
        Args:
            max_chunk_size: Maximum tokens per chunk
            overlap: Number of tokens to overlap between chunks
        """
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    def should_process_file(self, file_path: Path) -> bool:
        """Check if file should be processed"""
        # Check extension
        if file_path.suffix not in self.SUPPORTED_EXTENSIONS:
            return False
        
        # Check ignore patterns
        for part in file_path.parts:
            if part in self.IGNORE_PATTERNS:
                return False
        
        # Check file size (skip files > 1MB)
        try:
            if file_path.stat().st_size > 1_000_000:
                return False
        except:
            return False
        
        return True
    
    def extract_text(self, file_path: Path) -> str:
        """Extract text content from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    return f.read()
            except:
                return ""
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return ""
    
    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Document]:
        """
        Chunk text into smaller pieces with overlap
        
        Tries to preserve semantic boundaries (paragraphs, functions, etc.)
        """
        if not text.strip():
            return []
        
        # Tokenize the entire text
        tokens = self.tokenizer.encode(text)
        
        if len(tokens) <= self.max_chunk_size:
            # Text fits in one chunk
            return [Document(text, {**metadata, 'chunk_index': 0, 'total_chunks': 1})]
        
        # Split into chunks with overlap
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(tokens):
            end = min(start + self.max_chunk_size, len(tokens))
            chunk_tokens = tokens[start:end]
            chunk_text = self.tokenizer.decode(chunk_tokens)
            
            chunk_metadata = {
                **metadata,
                'chunk_index': chunk_index,
                'start_token': start,
                'end_token': end
            }
            
            chunks.append(Document(chunk_text, chunk_metadata))
            
            # Move start position with overlap
            start = end - self.overlap
            chunk_index += 1
        
        # Add total chunks to metadata
        for chunk in chunks:
            chunk.metadata['total_chunks'] = len(chunks)
        
        return chunks
    
    def process_file(self, file_path: Path, root_dir: Path) -> List[Document]:
        """Process a single file into document chunks"""
        if not self.should_process_file(file_path):
            return []
        
        # Extract text
        text = self.extract_text(file_path)
        if not text:
            return []
        
        # Create metadata
        try:
            relative_path = file_path.relative_to(root_dir)
        except ValueError:
            relative_path = file_path
        
        metadata = {
            'path': str(relative_path),
            'absolute_path': str(file_path),
            'extension': file_path.suffix,
            'filename': file_path.name,
            'size': len(text),
            'modified': file_path.stat().st_mtime
        }
        
        # Chunk the text
        return self.chunk_text(text, metadata)
    
    def process_directory(self, directory: Path) -> List[Document]:
        """Process all files in a directory recursively"""
        documents = []
        
        print(f"Processing directory: {directory}")
        
        for file_path in directory.rglob('*'):
            if file_path.is_file():
                file_docs = self.process_file(file_path, directory)
                documents.extend(file_docs)
                
                if file_docs:
                    print(f"  Processed: {file_path.name} ({len(file_docs)} chunks)")
        
        print(f"Total documents: {len(documents)}")
        return documents
    
    def get_file_summary(self, documents: List[Document]) -> Dict[str, int]:
        """Get summary statistics about processed documents"""
        file_counts = {}
        for doc in documents:
            path = doc.metadata.get('path', 'unknown')
            file_counts[path] = file_counts.get(path, 0) + 1
        return file_counts
