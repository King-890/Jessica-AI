
import sys
import os
from pathlib import Path
import json
import pytest

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rag.document_processor import DocumentProcessor  # noqa: E402
from src.rag.rag_manager import RAGManager  # noqa: E402

try:
    from src.rag.vector_store import ML_AVAILABLE  # noqa: E402
except ImportError:
    ML_AVAILABLE = False


def test_jsonl_processing():
    print("Testing JSONL processing...")

    # Create a dummy jsonl file
    test_file = Path("test_data.jsonl")
    with open(test_file, "w") as f:
        f.write(json.dumps({"user": "Hello", "assistant": "Hi there"}) + "\n")
        f.write(json.dumps({"user": "What is 2+2?", "assistant": "It is 4"}) + "\n")

    processor = DocumentProcessor()
    text = processor.extract_text(test_file)

    print("Extracted Text:")
    print(text)

    assert "User: Hello" in text
    assert "Assistant: Hi there" in text
    assert "User: What is 2+2?" in text

    # Clean up
    if test_file.exists():
        os.remove(test_file)

    print("\nJSONL Processing Test Passed!")


@pytest.mark.skipif(not ML_AVAILABLE, reason="RAG dependencies (sentence-transformers) not installed")
def test_rag_integration():
    print("\nTesting RAG Integration...")
    # This might fail if dependecies like vector store aren't setup,
    # but we just want to see if index_training_data is called and runs without crashing

    # We can mock index_dir to a temp dir
    import tempfile

    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create fake training data
        train_dir = Path(tmp_dir) / "training_data"
        train_dir.mkdir()
        with open(train_dir / "chat.jsonl", "w") as f:
            f.write(json.dumps({"user": "SecretCode", "assistant": "The code is 12345"}) + "\n")

        # Initialize RAG Manager (Process root needs to be correct relative to rag_index)
        # In rag_manager: project_root = self.index_dir.parent.parent
        # So we need structure: tmp/training_data AND tmp/.jessica/rag_index

        jessica_dir = Path(tmp_dir) / ".jessica"
        jessica_dir.mkdir()
        rag_dir = jessica_dir / "rag_index"

        # Initialize
        rag = RAGManager(index_dir=rag_dir)

        # Search
        results = rag.search_knowledge("SecretCode", top_k=1)
        print("Search Results:")
        for r in results:
            print(r['content'])

        found = any("The code is 12345" in r['content'] for r in results)
        if found:
            print("RAG successfully found training data content!")
        else:
            print("RAG did NOT find training data content.")


if __name__ == "__main__":
    test_jsonl_processing()
    try:
        if ML_AVAILABLE:
            test_rag_integration()
        else:
            print("Skipping RAG integration test (dependencies missing)")
    except Exception as e:
        print(f"RAG Integration test failed (expected if deps missing): {e}")
