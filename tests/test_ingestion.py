"""Test ingestion pipeline."""

import pytest
from pathlib import Path
from langchain.schema import Document

from src.ingestion import DocumentLoader, TextSplitter, Embedder


class TestDocumentLoader:
    """Test document loader functionality."""
    
    def test_load_markdown_file(self, tmp_path):
        """Test loading a markdown file."""
        # Create test file
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test Document\n\nThis is a test.")
        
        loader = DocumentLoader()
        documents = loader.load_document(test_file)
        
        assert len(documents) > 0
        assert documents[0].metadata["source_file"] == "test.md"
        assert documents[0].metadata["file_type"] == ".md"
    
    def test_load_text_file(self, tmp_path):
        """Test loading a text file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("This is a test document.")
        
        loader = DocumentLoader()
        documents = loader.load_document(test_file)
        
        assert len(documents) > 0
        assert "test" in documents[0].page_content.lower()
    
    def test_unsupported_format(self, tmp_path):
        """Test handling of unsupported file format."""
        test_file = tmp_path / "test.xyz"
        test_file.write_text("test")
        
        loader = DocumentLoader()
        
        with pytest.raises(ValueError):
            loader.load_document(test_file)
    
    def test_clean_text(self):
        """Test text cleaning."""
        loader = DocumentLoader()
        
        dirty_text = "This   is    a\n\n\ntest   document."
        clean_text = loader.clean_text(dirty_text)
        
        assert "  " not in clean_text
        assert "\n\n\n" not in clean_text


class TestTextSplitter:
    """Test text splitting functionality."""
    
    def test_split_documents(self):
        """Test document splitting."""
        documents = [
            Document(
                page_content="This is a test document. " * 100,
                metadata={"source": "test.txt"}
            )
        ]
        
        splitter = TextSplitter(strategy="recursive", chunk_size=500, chunk_overlap=50)
        chunks = splitter.split_documents(documents)
        
        assert len(chunks) > 1
        assert all(len(chunk.page_content) <= 550 for chunk in chunks)  # Allow some overflow
    
    def test_chunk_metadata(self):
        """Test chunk metadata assignment."""
        documents = [
            Document(
                page_content="Test " * 200,
                metadata={"source": "test.txt"}
            )
        ]
        
        splitter = TextSplitter(chunk_size=100, chunk_overlap=20)
        chunks = splitter.split_documents(documents)
        
        for i, chunk in enumerate(chunks):
            assert "chunk_id" in chunk.metadata
            assert "chunk_size" in chunk.metadata
    
    def test_get_chunk_stats(self):
        """Test chunk statistics."""
        documents = [
            Document(page_content="Test " * 100, metadata={})
        ]
        
        splitter = TextSplitter(chunk_size=100)
        chunks = splitter.split_documents(documents)
        stats = splitter.get_chunk_stats(chunks)
        
        assert "total_chunks" in stats
        assert "avg_chunk_size" in stats
        assert stats["total_chunks"] == len(chunks)


class TestEmbedder:
    """Test embedding generation."""
    
    @pytest.mark.integration
    def test_embed_text(self):
        """Test single text embedding (requires Azure connection)."""
        embedder = Embedder()
        
        text = "This is a test document."
        embedding = embedder.embed_text(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == embedder.dimension
        assert all(isinstance(x, float) for x in embedding)
    
    @pytest.mark.integration
    def test_embed_documents(self):
        """Test batch document embedding (requires Azure connection)."""
        embedder = Embedder()
        
        documents = [
            Document(page_content=f"Test document {i}", metadata={})
            for i in range(5)
        ]
        
        result = embedder.embed_documents(documents, show_progress=False)
        
        assert len(result) == 5
        for doc in result:
            assert "embedding" in doc.metadata
            assert len(doc.metadata["embedding"]) == embedder.dimension


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
