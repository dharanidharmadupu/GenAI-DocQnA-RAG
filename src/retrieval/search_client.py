"""Azure AI Search client wrapper."""

from typing import List, Dict, Any, Optional
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
    SemanticConfiguration,
    SemanticPrioritizedFields,
    SemanticField,
    SemanticSearch
)
from azure.core.credentials import AzureKeyCredential

from ..config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)


class SearchIndexManager:
    """Manage Azure AI Search indexes."""
    
    def __init__(self):
        """Initialize search index manager."""
        config = get_config()
        
        self.endpoint = config.search.endpoint
        self.credential = AzureKeyCredential(config.search.key)
        
        self.index_client = SearchIndexClient(
            endpoint=self.endpoint,
            credential=self.credential
        )
        
        self.logger = logger
    
    def create_index(self, index_name: str) -> SearchIndex:
        """
        Create a new search index with vector search capabilities.
        
        Args:
            index_name: Name of the index to create
        
        Returns:
            Created SearchIndex
        """
        config = get_config()
        
        # Define fields
        fields = [
            SimpleField(
                name="id",
                type=SearchFieldDataType.String,
                key=True,
                filterable=True
            ),
            SearchableField(
                name="content",
                type=SearchFieldDataType.String,
                searchable=True,
                analyzer_name="en.microsoft"
            ),
            SearchField(
                name="content_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=config.document_processing.embedding_dimension,
                vector_search_profile_name="vector-profile"
            ),
            SearchableField(
                name="title",
                type=SearchFieldDataType.String,
                searchable=True,
                filterable=True
            ),
            SimpleField(
                name="source_file",
                type=SearchFieldDataType.String,
                filterable=True,
                facetable=True
            ),
            SimpleField(
                name="page_number",
                type=SearchFieldDataType.Int32,
                filterable=True
            ),
            SimpleField(
                name="chunk_id",
                type=SearchFieldDataType.Int32,
                filterable=True
            ),
            SimpleField(
                name="created_at",
                type=SearchFieldDataType.DateTimeOffset,
                filterable=True,
                sortable=True
            ),
            SimpleField(
                name="metadata",
                type=SearchFieldDataType.String,
                filterable=False
            )
        ]
        
        # Configure vector search
        vector_search = VectorSearch(
            algorithms=[
                HnswAlgorithmConfiguration(
                    name="hnsw-algorithm",
                    parameters={
                        "m": 4,
                        "efConstruction": 400,
                        "efSearch": 500,
                        "metric": "cosine"
                    }
                )
            ],
            profiles=[
                VectorSearchProfile(
                    name="vector-profile",
                    algorithm_configuration_name="hnsw-algorithm"
                )
            ]
        )
        
        # Configure semantic search
        semantic_config = SemanticConfiguration(
            name="semantic-config",
            prioritized_fields=SemanticPrioritizedFields(
                title_field=SemanticField(field_name="title"),
                content_fields=[SemanticField(field_name="content")]
            )
        )
        
        semantic_search = SemanticSearch(
            configurations=[semantic_config]
        )
        
        # Create index
        index = SearchIndex(
            name=index_name,
            fields=fields,
            vector_search=vector_search,
            semantic_search=semantic_search
        )
        
        try:
            result = self.index_client.create_index(index)
            self.logger.info(f"Created index: {index_name}")
            return result
        except Exception as e:
            self.logger.error(f"Error creating index: {e}")
            raise
    
    def delete_index(self, index_name: str) -> None:
        """
        Delete a search index.
        
        Args:
            index_name: Name of the index to delete
        """
        try:
            self.index_client.delete_index(index_name)
            self.logger.info(f"Deleted index: {index_name}")
        except Exception as e:
            self.logger.warning(f"Error deleting index: {e}")
    
    def index_exists(self, index_name: str) -> bool:
        """
        Check if an index exists.
        
        Args:
            index_name: Name of the index
        
        Returns:
            True if index exists, False otherwise
        """
        try:
            self.index_client.get_index(index_name)
            return True
        except:
            return False
    
    def get_search_client(self, index_name: str) -> SearchClient:
        """
        Get a search client for querying an index.
        
        Args:
            index_name: Name of the index
        
        Returns:
            SearchClient instance
        """
        return SearchClient(
            endpoint=self.endpoint,
            index_name=index_name,
            credential=self.credential
        )
    
    def upload_documents(self, index_name: str, documents: List[Dict[str, Any]]) -> None:
        """
        Upload documents to a search index.
        
        Args:
            index_name: Name of the index
            documents: List of documents to upload
        """
        search_client = self.get_search_client(index_name)
        
        try:
            result = search_client.upload_documents(documents=documents)
            self.logger.debug(f"Uploaded {len(documents)} documents to {index_name}")
        except Exception as e:
            self.logger.error(f"Error uploading documents: {e}")
            raise


class AzureSearchRetriever:
    """Retriever for Azure AI Search with vector and hybrid search."""
    
    def __init__(self, index_name: Optional[str] = None):
        """
        Initialize Azure Search retriever.
        
        Args:
            index_name: Name of the search index (optional, uses config default)
        """
        config = get_config()
        
        self.index_name = index_name or config.search.index_name
        self.endpoint = config.search.endpoint
        self.credential = AzureKeyCredential(config.search.key)
        
        self.search_client = SearchClient(
            endpoint=self.endpoint,
            index_name=self.index_name,
            credential=self.credential
        )
        
        self.enable_hybrid = config.app.enable_hybrid_search
        self.enable_semantic = config.app.enable_semantic_ranking
        self.max_results = config.document_processing.max_retrieval_results
        
        self.logger = logger
    
    def vector_search(
        self,
        query_vector: List[float],
        top_k: Optional[int] = None,
        filters: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform vector search.
        
        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            filters: OData filter expression
        
        Returns:
            List of search results
        """
        top_k = top_k or self.max_results
        
        try:
            results = self.search_client.search(
                search_text=None,
                vector_queries=[{
                    "kind": "vector",
                    "vector": query_vector,
                    "fields": "content_vector",
                    "k": top_k
                }],
                filter=filters,
                select=["id", "content", "title", "source_file", "page_number", "chunk_id"]
            )
            
            return [
                {
                    "id": doc["id"],
                    "content": doc["content"],
                    "title": doc.get("title", ""),
                    "source_file": doc.get("source_file", ""),
                    "page_number": doc.get("page_number", 0),
                    "chunk_id": doc.get("chunk_id", 0),
                    "score": doc.get("@search.score", 0.0)
                }
                for doc in results
            ]
        
        except Exception as e:
            self.logger.error(f"Vector search error: {e}")
            return []
    
    def hybrid_search(
        self,
        query_text: str,
        query_vector: List[float],
        top_k: Optional[int] = None,
        filters: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search (keyword + vector).
        
        Args:
            query_text: Query text for keyword search
            query_vector: Query embedding vector
            top_k: Number of results to return
            filters: OData filter expression
        
        Returns:
            List of search results
        """
        top_k = top_k or self.max_results
        
        try:
            search_args = {
                "search_text": query_text,
                "vector_queries": [{
                    "kind": "vector",
                    "vector": query_vector,
                    "fields": "content_vector",
                    "k": top_k
                }],
                "top": top_k,
                "filter": filters,
                "select": ["id", "content", "title", "source_file", "page_number", "chunk_id"]
            }
            
            # Add semantic ranking if enabled
            if self.enable_semantic:
                search_args["query_type"] = "semantic"
                search_args["semantic_configuration_name"] = "semantic-config"
            
            results = self.search_client.search(**search_args)
            
            return [
                {
                    "id": doc["id"],
                    "content": doc["content"],
                    "title": doc.get("title", ""),
                    "source_file": doc.get("source_file", ""),
                    "page_number": doc.get("page_number", 0),
                    "chunk_id": doc.get("chunk_id", 0),
                    "score": doc.get("@search.score", 0.0),
                    "reranker_score": doc.get("@search.reranker_score")
                }
                for doc in results
            ]
        
        except Exception as e:
            self.logger.error(f"Hybrid search error: {e}")
            return []
    
    def search(
        self,
        query_text: str,
        query_vector: List[float],
        top_k: Optional[int] = None,
        filters: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform search using configured method (vector or hybrid).
        
        Args:
            query_text: Query text
            query_vector: Query embedding vector
            top_k: Number of results to return
            filters: OData filter expression
        
        Returns:
            List of search results
        """
        if self.enable_hybrid:
            return self.hybrid_search(query_text, query_vector, top_k, filters)
        else:
            return self.vector_search(query_vector, top_k, filters)


if __name__ == "__main__":
    # Test search index manager
    manager = SearchIndexManager()
    
    test_index = "test-index"
    
    # Create index
    if not manager.index_exists(test_index):
        manager.create_index(test_index)
        print(f"Created index: {test_index}")
    else:
        print(f"Index already exists: {test_index}")
