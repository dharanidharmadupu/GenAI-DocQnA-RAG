"""Text splitting strategies for document chunking."""

from typing import List, Optional
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter,
    TokenTextSplitter
)
from langchain.schema import Document

from ..utils.logger import get_logger
from ..config import get_config

logger = get_logger(__name__)


class TextSplitter:
    """Split documents into chunks for embedding."""
    
    def __init__(
        self,
        strategy: str = "recursive",
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ):
        """
        Initialize text splitter.
        
        Args:
            strategy: Splitting strategy ("recursive", "character", "token")
            chunk_size: Size of each chunk in characters
            chunk_overlap: Overlap between chunks
        """
        config = get_config()
        
        self.strategy = strategy
        self.chunk_size = chunk_size or config.document_processing.chunk_size
        self.chunk_overlap = chunk_overlap or config.document_processing.chunk_overlap
        
        self.logger = logger
        self.splitter = self._create_splitter()
    
    def _create_splitter(self):
        """Create the appropriate text splitter."""
        config = get_config()
        
        # Get separators from config
        separators = config.get("document_processing.chunking.separators", ["\n\n", "\n", " ", ""])
        
        if self.strategy == "recursive":
            return RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=separators,
                length_function=len,
            )
        elif self.strategy == "character":
            return CharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separator="\n\n",
                length_function=len,
            )
        elif self.strategy == "token":
            return TokenTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
            )
        else:
            raise ValueError(f"Unknown splitting strategy: {self.strategy}")
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into chunks.
        
        Args:
            documents: List of documents to split
        
        Returns:
            List of document chunks
        """
        self.logger.info(f"Splitting {len(documents)} documents with strategy: {self.strategy}")
        
        chunks = self.splitter.split_documents(documents)
        
        # Add chunk metadata
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_id"] = i
            chunk.metadata["chunk_size"] = len(chunk.page_content)
        
        self.logger.info(f"Created {len(chunks)} chunks from {len(documents)} documents")
        return chunks
    
    def split_text(self, text: str) -> List[str]:
        """
        Split a single text string into chunks.
        
        Args:
            text: Text to split
        
        Returns:
            List of text chunks
        """
        return self.splitter.split_text(text)
    
    def get_chunk_stats(self, chunks: List[Document]) -> dict:
        """
        Get statistics about chunks.
        
        Args:
            chunks: List of document chunks
        
        Returns:
            Dictionary with statistics
        """
        if not chunks:
            return {
                "total_chunks": 0,
                "avg_chunk_size": 0,
                "min_chunk_size": 0,
                "max_chunk_size": 0
            }
        
        chunk_sizes = [len(chunk.page_content) for chunk in chunks]
        
        return {
            "total_chunks": len(chunks),
            "avg_chunk_size": sum(chunk_sizes) / len(chunk_sizes),
            "min_chunk_size": min(chunk_sizes),
            "max_chunk_size": max(chunk_sizes)
        }


class SemanticChunker:
    """
    Advanced semantic chunking that preserves context.
    Uses sentence boundaries and semantic similarity.
    """
    
    def __init__(self, target_chunk_size: int = 1000):
        """
        Initialize semantic chunker.
        
        Args:
            target_chunk_size: Target size for chunks
        """
        self.target_chunk_size = target_chunk_size
        self.logger = logger
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents using semantic chunking.
        
        Args:
            documents: List of documents to split
        
        Returns:
            List of semantically coherent chunks
        """
        self.logger.info(f"Splitting {len(documents)} documents using semantic chunking")
        
        all_chunks = []
        
        for doc in documents:
            chunks = self._split_by_sentences(doc)
            all_chunks.extend(chunks)
        
        self.logger.info(f"Created {len(all_chunks)} semantic chunks")
        return all_chunks
    
    def _split_by_sentences(self, document: Document) -> List[Document]:
        """
        Split document by sentences while maintaining context.
        
        Args:
            document: Document to split
        
        Returns:
            List of chunks
        """
        import re
        
        text = document.page_content
        
        # Split by sentences (simple regex)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence)
            
            if current_size + sentence_size > self.target_chunk_size and current_chunk:
                # Create chunk
                chunk_text = ' '.join(current_chunk)
                chunk = Document(
                    page_content=chunk_text,
                    metadata={
                        **document.metadata,
                        "chunk_id": len(chunks),
                        "chunk_size": len(chunk_text)
                    }
                )
                chunks.append(chunk)
                
                # Start new chunk
                current_chunk = [sentence]
                current_size = sentence_size
            else:
                current_chunk.append(sentence)
                current_size += sentence_size
        
        # Add remaining chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunk = Document(
                page_content=chunk_text,
                metadata={
                    **document.metadata,
                    "chunk_id": len(chunks),
                    "chunk_size": len(chunk_text)
                }
            )
            chunks.append(chunk)
        
        return chunks


if __name__ == "__main__":
    # Test text splitter
    splitter = TextSplitter(strategy="recursive", chunk_size=500, chunk_overlap=50)
    
    # Sample document
    sample_doc = Document(
        page_content="This is a sample document. " * 100,
        metadata={"source": "test.txt"}
    )
    
    chunks = splitter.split_documents([sample_doc])
    stats = splitter.get_chunk_stats(chunks)
    
    print(f"Chunk statistics: {stats}")
