"""Document loader for various file formats."""

from pathlib import Path
from typing import List, Dict, Any
import re

from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
    UnstructuredHTMLLoader
)
from langchain.schema import Document

from ..utils.logger import get_logger

logger = get_logger(__name__)


class DocumentLoader:
    """Load documents from various file formats."""
    
    SUPPORTED_FORMATS = {
        ".pdf": PyPDFLoader,
        ".docx": Docx2txtLoader,
        ".txt": TextLoader,
        ".md": UnstructuredMarkdownLoader,
        ".html": UnstructuredHTMLLoader
    }
    
    def __init__(self):
        """Initialize document loader."""
        self.logger = logger
    
    def load_document(self, file_path: Path) -> List[Document]:
        """
        Load a single document.
        
        Args:
            file_path: Path to the document file
        
        Returns:
            List of Document objects
        
        Raises:
            ValueError: If file format is not supported
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_ext = file_path.suffix.lower()
        
        if file_ext not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported file format: {file_ext}. "
                f"Supported formats: {list(self.SUPPORTED_FORMATS.keys())}"
            )
        
        loader_class = self.SUPPORTED_FORMATS[file_ext]
        
        try:
            loader = loader_class(str(file_path))
            documents = loader.load()
            
            # Add metadata
            for doc in documents:
                doc.metadata["source_file"] = file_path.name
                doc.metadata["file_path"] = str(file_path)
                doc.metadata["file_type"] = file_ext
            
            self.logger.info(f"Loaded {len(documents)} pages from {file_path.name}")
            return documents
        
        except Exception as e:
            self.logger.error(f"Error loading {file_path.name}: {e}")
            raise
    
    def load_directory(
        self,
        directory: Path,
        recursive: bool = True,
        pattern: str = "*"
    ) -> List[Document]:
        """
        Load all supported documents from a directory.
        
        Args:
            directory: Path to directory
            recursive: Whether to search recursively
            pattern: File pattern to match
        
        Returns:
            List of all loaded documents
        """
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        all_documents = []
        
        # Find all files
        if recursive:
            files = list(directory.rglob(pattern))
        else:
            files = list(directory.glob(pattern))
        
        # Filter by supported formats
        supported_files = [
            f for f in files
            if f.suffix.lower() in self.SUPPORTED_FORMATS
        ]
        
        self.logger.info(
            f"Found {len(supported_files)} supported documents in {directory}"
        )
        
        # Load each file
        for file_path in supported_files:
            try:
                documents = self.load_document(file_path)
                all_documents.extend(documents)
            except Exception as e:
                self.logger.warning(f"Skipping {file_path.name}: {e}")
                continue
        
        self.logger.info(f"Loaded total of {len(all_documents)} pages")
        return all_documents
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean and normalize text.
        
        Args:
            text: Raw text
        
        Returns:
            Cleaned text
        """
        # Remove multiple whitespaces
        text = re.sub(r'\s+', ' ', text)
        
        # Remove multiple newlines
        text = re.sub(r'\n+', '\n', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def extract_metadata(self, document: Document) -> Dict[str, Any]:
        """
        Extract additional metadata from document.
        
        Args:
            document: Document object
        
        Returns:
            Dictionary of metadata
        """
        metadata = document.metadata.copy()
        
        # Extract title (first line or from filename)
        if document.page_content:
            first_line = document.page_content.split('\n')[0]
            if len(first_line) < 100:  # Likely a title
                metadata["title"] = first_line
        
        # Add word count
        metadata["word_count"] = len(document.page_content.split())
        
        # Add character count
        metadata["char_count"] = len(document.page_content)
        
        return metadata


if __name__ == "__main__":
    # Test document loader
    loader = DocumentLoader()
    
    # Example usage
    docs_dir = Path("sample_docs")
    if docs_dir.exists():
        documents = loader.load_directory(docs_dir)
        print(f"Loaded {len(documents)} documents")
        
        if documents:
            print(f"\nFirst document preview:")
            print(f"Source: {documents[0].metadata.get('source_file')}")
            print(f"Content: {documents[0].page_content[:200]}...")
