"""Embedding generation using Azure OpenAI."""

from typing import List
import time

from openai import AzureOpenAI
from langchain.schema import Document

from ..config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)


class Embedder:
    """Generate embeddings for text chunks."""
    
    def __init__(self):
        """Initialize embedder with Azure OpenAI."""
        config = get_config()
        
        self.client = AzureOpenAI(
            api_key=config.ai_foundry.key,
            api_version=config.ai_foundry.api_version,
            azure_endpoint=config.ai_foundry.endpoint
        )
        
        self.deployment_name = config.ai_foundry.embedding_deployment_name
        self.dimension = config.document_processing.embedding_dimension
        self.batch_size = config.get("embedding.batch_size", 16)
        
        self.logger = logger
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding vector
        """
        try:
            response = self.client.embeddings.create(
                input=text,
                model=self.deployment_name
            )
            
            return response.data[0].embedding
        
        except Exception as e:
            self.logger.error(f"Error generating embedding: {e}")
            raise
    
    def embed_documents(
        self,
        documents: List[Document],
        show_progress: bool = True
    ) -> List[Document]:
        """
        Generate embeddings for a list of documents.
        
        Args:
            documents: List of documents to embed
            show_progress: Whether to show progress
        
        Returns:
            Documents with embeddings added to metadata
        """
        self.logger.info(f"Generating embeddings for {len(documents)} documents")
        
        start_time = time.time()
        
        # Process in batches
        for i in range(0, len(documents), self.batch_size):
            batch = documents[i:i + self.batch_size]
            
            try:
                # Extract texts
                texts = [doc.page_content for doc in batch]
                
                # Generate embeddings
                response = self.client.embeddings.create(
                    input=texts,
                    model=self.deployment_name
                )
                
                # Add embeddings to documents
                for j, doc in enumerate(batch):
                    doc.metadata["embedding"] = response.data[j].embedding
                
                if show_progress:
                    progress = min(i + self.batch_size, len(documents))
                    self.logger.info(f"Progress: {progress}/{len(documents)} documents")
            
            except Exception as e:
                self.logger.error(f"Error in batch {i//self.batch_size}: {e}")
                # Continue with next batch
                continue
        
        elapsed = time.time() - start_time
        self.logger.info(
            f"Generated embeddings in {elapsed:.2f}s "
            f"({len(documents)/elapsed:.2f} docs/sec)"
        )
        
        return documents
    
    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a search query.
        
        Args:
            query: Query text
        
        Returns:
            Query embedding vector
        """
        return self.embed_text(query)


if __name__ == "__main__":
    # Test embedder
    from dotenv import load_dotenv
    load_dotenv()
    
    embedder = Embedder()
    
    # Test single text
    text = "This is a test document about Azure AI."
    embedding = embedder.embed_text(text)
    
    print(f"Embedding dimension: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")
