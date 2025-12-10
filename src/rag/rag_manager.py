"""
RAG Manager - High-level orchestration of RAG system
"""

import shutil
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any
from .document_processor import DocumentProcessor, Document
from .vector_store import VectorStore
from .web_crawler import WebCrawler

class RAGManager:
    """Manages RAG indexing and querying"""
    
    def __init__(self, index_dir: Path = None, enable_training: bool = True):
        """
        Initialize RAG manager
        
        Args:
            index_dir: Directory to store index files
            enable_training: Whether to scan and index local training data on startup
        """
        if index_dir is None:
            index_dir = Path.cwd() / ".jessica" / "rag_index"
        
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        self.processor = DocumentProcessor(max_chunk_size=512, overlap=50)
        self.vector_store = VectorStore(
            model_name="all-MiniLM-L6-v2",
            index_path=self.index_dir
        )
        self.crawler = WebCrawler()
        
        self.indexed_projects: Dict[str, Path] = {}
        
        # Try to load existing index
        try:
            self._load_index()
        except:
            print("No existing index found, starting fresh")
            
        # Ensure training data is indexed (or at least check)
        if enable_training:
            self.index_training_data()
        else:
            print("Local training/indexing disabled (Cloud/Lite Mode).")

    def index_training_data(self):
        """Index the training_data directory if it exists"""
        training_dir = self.index_dir.parent / "training_data"
        # If running from src/rag, we might need to adjust path logic or pass it in.
        # Assuming index_dir is at project_root/.jessica/rag_index
        # So project_root is index_dir.parent.parent
        project_root = self.index_dir.parent.parent
        training_dir = project_root / "training_data"
        
        if training_dir.exists() and training_dir.is_dir():
            print(f"Checking training data at {training_dir}")
            # We can force update or check if already indexed.
            # For now, let's just index it as a project named "training_memory"
            # It will process files and add them.
            self.index_project(training_dir, project_name="training_memory")
        else:
            print(f"Training data directory not found at {training_dir}")
    
    def index_project(self, project_path: Path, project_name: Optional[str] = None):
        """
        Index a project directory
        
        Args:
            project_path: Path to project directory
            project_name: Optional name for the project
        """
        project_path = Path(project_path).resolve()
        
        if not project_path.exists():
            raise FileNotFoundError(f"Project path does not exist: {project_path}")
        
        if not project_path.is_dir():
            raise NotADirectoryError(f"Project path is not a directory: {project_path}")
        
        project_name = project_name or project_path.name
        
        print(f"\n{'='*60}")
        print(f"Indexing project: {project_name}")
        print(f"Path: {project_path}")
        print(f"{'='*60}\n")
        
        # Process files in batches to avoid MemoryError
        batch_size = 10
        current_batch = []
        files = [f for f in project_path.rglob('*') if f.is_file()]
        
        print(f"Found {len(files)} files to process in {project_path}")
        
        for i, file_path in enumerate(files):
            try:
                # Process single file
                file_docs = self.processor.process_file(file_path, project_path)
                if file_docs:
                    current_batch.extend(file_docs)
                    print(f"  Processed: {file_path.name} ({len(file_docs)} chunks)")
            except Exception as e:
                print(f"  [ERROR] Failed to process {file_path.name}: {e}")
                # Continue to next file
                continue
            
            # Flush batch if full
            if len(current_batch) >= 50 or (i + 1) % batch_size == 0:
                print(f"  Flushing batch of {len(current_batch)} chunks...")
                self.vector_store.add_documents(current_batch)
                current_batch = [] # Clear memory
        
        # Flush remaining
        if current_batch:
            print(f"  Flushing final batch of {len(current_batch)} chunks...")
            self.vector_store.add_documents(current_batch)
        
        # Track indexed project
        self.indexed_projects[project_name] = project_path
        
        # Save index
        self._save_index()
        
        # Print summary
        file_summary = self.processor.get_file_summary(documents)
        print(f"\n{'='*60}")
        print(f"Indexing complete!")
        print(f"Files indexed: {len(file_summary)}")
        print(f"Total chunks: {len(documents)}")
        print(f"{'='*60}\n")
        print(f"Total chunks: {len(documents)}")
        print(f"{'='*60}\n")
    
    def ingest_git_repo(self, repo_url: str, repo_name: Optional[str] = None):
        """
        Clone and index a Git repository
        
        Args:
            repo_url: URL of the git repository
            repo_name: Optional name for the repository (defaults to repo name from URL)
        """
        if not repo_name:
            repo_name = repo_url.split("/")[-1].replace(".git", "")
            
        # Create a directory for learned repos
        repos_dir = self.index_dir.parent / "learned_repos"
        repos_dir.mkdir(parents=True, exist_ok=True)
        
        target_dir = repos_dir / repo_name
        
        print(f"\n{'='*60}")
        print(f"Ingesting Git Repository: {repo_name}")
        print(f"URL: {repo_url}")
        print(f"{'='*60}\n")
        
        # Clone or pull
        if target_dir.exists():
            print(f"Repository already exists at {target_dir}")
            print("Pulling latest changes...")
            try:
                subprocess.run(["git", "pull"], cwd=target_dir, check=True, capture_output=True)
            except Exception as e:
                print(f"Error pulling repo: {e}")
                # Continue anyway, maybe it's fine
        else:
            print(f"Cloning to {target_dir}...")
            try:
                subprocess.run(["git", "clone", repo_url, str(target_dir)], check=True, capture_output=True)
            except Exception as e:
                print(f"Error cloning repo: {e}")
                raise RuntimeError(f"Failed to clone repository: {e}")
        
        # Index the repo
        self.index_project(target_dir, f"git:{repo_name}")
        print(f"Successfully ingested {repo_name}")
        
    def ingest_web_page(self, url: str):
        """
        Fetch and index a web page
        
        Args:
            url: URL to fetch
        """
        print(f"\n{'='*60}")
        print(f"Ingesting Web Page: {url}")
        print(f"{'='*60}\n")
        
        page_data = self.crawler.fetch_page(url)
        
        if not page_data:
            raise RuntimeError(f"Failed to fetch page: {url}")
            
        # Create a document from the page content
        doc = Document(
            content=page_data['content'],
            metadata={
                'source': url,
                'title': page_data['title'],
                'type': 'web_page',
                'domain': page_data['domain']
            }
        )
        
        # Chunk the document
        chunks = self.processor.chunk_document(doc)
        
        if not chunks:
            print("No content found to index")
            return
            
        # Add to vector store
        self.vector_store.add_documents(chunks)
        
        # Track as a "project" (using domain as project name for grouping)
        domain = page_data['domain']
        if domain not in self.indexed_projects:
            # We don't have a local path for web pages, so we use a placeholder
            # This might need a better approach if we want to persist "known domains"
            # For now, we just add it to the vector store
            pass
            
        self._save_index()
        
        print(f"Successfully ingested {url}")
        print(f"Title: {page_data['title']}")
        print(f"Chunks: {len(chunks)}")

    def search_knowledge(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Query the RAG system for relevant context
        
        Args:
            query: Search query
            top_k: Number of results to return
        
        Returns:
            List of result dictionaries with content and metadata
        """
        results = self.vector_store.search(query, top_k=top_k)
        
        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                'content': doc.content,
                'metadata': doc.metadata,
                'similarity': score
            })
        
        return formatted_results
    
    def get_context_for_query(self, query: str, top_k: int = 3) -> str:
        """
        Get formatted context string for a query
        
        Args:
            query: Search query
            top_k: Number of results to include
        
        Returns:
            Formatted context string
        """
        results = self.search_knowledge(query, top_k=top_k)
        
        if not results:
            return ""
        
        context_parts = []
        context_parts.append("=== Relevant Project Context ===\n")
        
        for i, result in enumerate(results, 1):
            metadata = result['metadata']
            path = metadata.get('path', 'unknown')
            chunk_info = f"(chunk {metadata.get('chunk_index', 0) + 1}/{metadata.get('total_chunks', 1)})"
            
            context_parts.append(f"\n[{i}] {path} {chunk_info}")
            context_parts.append(f"Relevance: {result['similarity']:.2f}")
            context_parts.append("```")
            context_parts.append(result['content'][:500])  # Limit to 500 chars
            if len(result['content']) > 500:
                context_parts.append("... (truncated)")
            context_parts.append("```\n")
        
        return "\n".join(context_parts)
    
    def reindex_project(self, project_name: str):
        """Re-index a previously indexed project"""
        if project_name not in self.indexed_projects:
            raise ValueError(f"Project not found: {project_name}")
        project_path = self.indexed_projects[project_name]
        
        # Clear and re-index
        print(f"Re-indexing project: {project_name}")
        self.vector_store.clear()
        self.indexed_projects.clear()
        self.index_project(project_path, project_name)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the RAG system"""
        return {
            'indexed_projects': list(self.indexed_projects.keys()),
            'vector_store': self.vector_store.get_stats(),
            'index_directory': str(self.index_dir)
        }

    def unload_index(self):
        """Free up memory by unloading the vector store"""
        print("Wait! Unloading RAG Index to save memory...")
        # Assuming VectorStore has a clear method or we just re-init
        # If VectorStore uses a heavy model, we might want to delete it
        if hasattr(self.vector_store, 'clear'):
            # This clears data but might not free model weights if they are loaded in __init__
            pass
        
        # Force garbage collection if possible or just reset logic
        # For this MVP, we'll just print log as the VectorStore is lightweight-ish (MiniLM)
        # But let's add a flag to prevent searches
        print("RAG Index unloaded (Simulation).")
    
    def _save_index(self):
        """Save index to disk"""
        self.vector_store.save(self.index_dir)
        
        # Save project list
        import pickle
        projects_file = self.index_dir / "projects.pkl"
        with open(projects_file, 'wb') as f:
            pickle.dump(self.indexed_projects, f)
    
    def _load_index(self):
        """Load index from disk"""
        self.vector_store.load(self.index_dir)

        # Load project list
        import pickle
        projects_file = self.index_dir / "projects.pkl"
        if projects_file.exists():
            with open(projects_file, 'rb') as f:
                self.indexed_projects = pickle.load(f)

            print(f"Loaded index with {len(self.indexed_projects)} projects:")
            for name in self.indexed_projects.keys():
                print(f"  - {name}")
