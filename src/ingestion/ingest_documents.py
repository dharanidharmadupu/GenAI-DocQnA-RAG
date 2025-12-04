"""Main document ingestion script."""

import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import List

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.config import get_config
from src.ingestion import DocumentLoader, TextSplitter, Embedder
from src.retrieval.search_client import SearchIndexManager
from src.utils.logger import setup_logger, get_logger

logger = get_logger(__name__)


def ingest_documents(
    docs_folder: Path,
    index_name: str = None,
    chunk_size: int = None,
    chunk_overlap: int = None,
    recreate_index: bool = False
) -> None:
    """
    Ingest documents into Azure AI Search.
    
    Args:
        docs_folder: Path to folder containing documents
        index_name: Name of search index (optional, uses config default)
        chunk_size: Chunk size for splitting (optional, uses config default)
        chunk_overlap: Chunk overlap (optional, uses config default)
        recreate_index: Whether to recreate the index
    """
    logger.info("=" * 80)
    logger.info("Starting document ingestion pipeline")
    logger.info("=" * 80)
    
    # Load configuration
    config = get_config()
    index_name = index_name or config.search.index_name
    
    # Initialize components
    logger.info("Initializing components...")
    loader = DocumentLoader()
    splitter = TextSplitter(
        strategy="recursive",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    embedder = Embedder()
    search_manager = SearchIndexManager()
    
    # Step 1: Load documents
    logger.info(f"\n{'='*80}")
    logger.info(f"Step 1: Loading documents from {docs_folder}")
    logger.info(f"{'='*80}")
    
    if not docs_folder.exists():
        logger.error(f"Documents folder not found: {docs_folder}")
        sys.exit(1)
    
    documents = loader.load_directory(docs_folder, recursive=True)
    
    if not documents:
        logger.warning("No documents found to ingest!")
        return
    
    logger.info(f"✓ Loaded {len(documents)} document pages")
    
    # Step 2: Split documents into chunks
    logger.info(f"\n{'='*80}")
    logger.info(f"Step 2: Splitting documents into chunks")
    logger.info(f"{'='*80}")
    
    chunks = splitter.split_documents(documents)
    stats = splitter.get_chunk_stats(chunks)
    
    logger.info(f"✓ Created {stats['total_chunks']} chunks")
    logger.info(f"  - Average chunk size: {stats['avg_chunk_size']:.0f} characters")
    logger.info(f"  - Min chunk size: {stats['min_chunk_size']} characters")
    logger.info(f"  - Max chunk size: {stats['max_chunk_size']} characters")
    
    # Step 3: Generate embeddings
    logger.info(f"\n{'='*80}")
    logger.info(f"Step 3: Generating embeddings")
    logger.info(f"{'='*80}")
    
    chunks_with_embeddings = embedder.embed_documents(chunks, show_progress=True)
    logger.info(f"✓ Generated embeddings for {len(chunks_with_embeddings)} chunks")
    
    # Step 4: Create or update search index
    logger.info(f"\n{'='*80}")
    logger.info(f"Step 4: Setting up Azure AI Search index")
    logger.info(f"{'='*80}")
    
    if recreate_index:
        logger.info(f"Recreating index: {index_name}")
        search_manager.delete_index(index_name)
    
    if not search_manager.index_exists(index_name):
        logger.info(f"Creating new index: {index_name}")
        search_manager.create_index(index_name)
    else:
        logger.info(f"Using existing index: {index_name}")
    
    # Step 5: Upload documents to search index
    logger.info(f"\n{'='*80}")
    logger.info(f"Step 5: Uploading documents to search index")
    logger.info(f"{'='*80}")
    
    # Prepare documents for upload
    search_documents = []
    for i, chunk in enumerate(chunks_with_embeddings):
        doc = {
            "id": f"doc_{i}_{int(datetime.now().timestamp())}",
            "content": chunk.page_content,
            "content_vector": chunk.metadata.get("embedding", []),
            "title": chunk.metadata.get("title", chunk.metadata.get("source_file", "Untitled")),
            "source_file": chunk.metadata.get("source_file", "unknown"),
            "page_number": chunk.metadata.get("page", 0),
            "chunk_id": chunk.metadata.get("chunk_id", i),
            "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "metadata": str(chunk.metadata)
        }
        search_documents.append(doc)
    
    # Upload in batches
    batch_size = 100
    total_uploaded = 0
    
    for i in range(0, len(search_documents), batch_size):
        batch = search_documents[i:i + batch_size]
        try:
            search_manager.upload_documents(index_name, batch)
            total_uploaded += len(batch)
            logger.info(f"Uploaded batch {i//batch_size + 1}: {total_uploaded}/{len(search_documents)} documents")
        except Exception as e:
            logger.error(f"Error uploading batch: {e}")
            continue
    
    logger.info(f"✓ Successfully uploaded {total_uploaded} documents")
    
    # Summary
    logger.info(f"\n{'='*80}")
    logger.info("Ingestion Complete!")
    logger.info(f"{'='*80}")
    logger.info(f"Summary:")
    logger.info(f"  - Documents processed: {len(documents)}")
    logger.info(f"  - Chunks created: {len(chunks)}")
    logger.info(f"  - Documents uploaded: {total_uploaded}")
    logger.info(f"  - Index name: {index_name}")
    logger.info(f"{'='*80}\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Ingest documents into Azure AI Search with embeddings"
    )
    
    parser.add_argument(
        "--docs-folder",
        type=Path,
        default=Path("sample_docs"),
        help="Path to folder containing documents"
    )
    
    parser.add_argument(
        "--index-name",
        type=str,
        help="Name of the search index (optional, uses config default)"
    )
    
    parser.add_argument(
        "--chunk-size",
        type=int,
        help="Chunk size for text splitting (optional, uses config default)"
    )
    
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        help="Chunk overlap (optional, uses config default)"
    )
    
    parser.add_argument(
        "--recreate-index",
        action="store_true",
        help="Recreate the index if it exists"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logger(log_level=args.log_level, log_file="logs/ingestion.log")
    
    try:
        ingest_documents(
            docs_folder=args.docs_folder,
            index_name=args.index_name,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            recreate_index=args.recreate_index
        )
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
