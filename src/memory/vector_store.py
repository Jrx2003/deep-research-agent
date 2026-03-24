"""Vector store implementation using ChromaDB."""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import hashlib

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

from src.core.config import settings


@dataclass
class Document:
    """Document in vector store."""

    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None


class VectorStore:
    """Vector store for research findings."""

    def __init__(self, collection_name: str = "research"):
        """Initialize vector store.

        Args:
            collection_name: Name of the collection
        """
        self.collection_name = collection_name
        self._client: Optional[Any] = None
        self._collection: Optional[Any] = None
        self._embedder: Optional[Any] = None

        if CHROMA_AVAILABLE:
            self._init_chroma()

        if SENTENCE_TRANSFORMERS_AVAILABLE:
            self._init_embedder()

    def _init_chroma(self):
        """Initialize ChromaDB client."""
        try:
            self._client = chromadb.PersistentClient(
                path=settings.chroma_persist_dir,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                ),
            )
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        except Exception as e:
            print(f"Failed to initialize ChromaDB: {e}")
            self._client = None
            self._collection = None

    def _init_embedder(self):
        """Initialize sentence transformer embedder."""
        try:
            self._embedder = SentenceTransformer(settings.embedding_model)
        except Exception as e:
            print(f"Failed to initialize embedder: {e}")
            self._embedder = None

    def _generate_id(self, content: str) -> str:
        """Generate ID from content."""
        return hashlib.md5(content.encode()).hexdigest()

    def _embed(self, texts: List[str]) -> List[List[float]]:
        """Embed texts into vectors."""
        if self._embedder is None:
            # Return zero vectors if embedder not available
            return [[0.0] * 384] * len(texts)

        try:
            embeddings = self._embedder.encode(texts, convert_to_list=True)
            return embeddings if isinstance(embeddings, list) else embeddings.tolist()
        except Exception as e:
            print(f"Embedding failed: {e}")
            return [[0.0] * 384] * len(texts)

    def add(self, documents: List[Document]) -> bool:
        """Add documents to vector store.

        Args:
            documents: List of documents to add

        Returns:
            True if successful
        """
        if not self._collection or not documents:
            return False

        try:
            # Generate embeddings
            texts = [doc.content for doc in documents]
            embeddings = self._embed(texts)

            # Prepare data for ChromaDB
            ids = [doc.id or self._generate_id(doc.content) for doc in documents]
            metadatas = [doc.metadata for doc in documents]

            # Add to collection
            self._collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
            )

            return True

        except Exception as e:
            print(f"Failed to add documents: {e}")
            return False

    def search(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """Search for similar documents.

        Args:
            query: Search query
            n_results: Number of results to return
            filter_metadata: Optional metadata filter

        Returns:
            List of matching documents
        """
        if not self._collection:
            return []

        try:
            # Embed query
            query_embedding = self._embed([query])[0]

            # Search
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=filter_metadata,
            )

            # Convert to Documents
            documents = []
            for i in range(len(results["ids"][0])):
                doc = Document(
                    id=results["ids"][0][i],
                    content=results["documents"][0][i],
                    metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                )
                documents.append(doc)

            return documents

        except Exception as e:
            print(f"Search failed: {e}")
            return []

    def get(self, doc_id: str) -> Optional[Document]:
        """Get document by ID.

        Args:
            doc_id: Document ID

        Returns:
            Document or None
        """
        if not self._collection:
            return None

        try:
            result = self._collection.get(ids=[doc_id])

            if result["ids"]:
                return Document(
                    id=result["ids"][0],
                    content=result["documents"][0],
                    metadata=result["metadatas"][0] if result["metadatas"] else {},
                )

            return None

        except Exception as e:
            print(f"Failed to get document: {e}")
            return None

    def delete(self, doc_id: str) -> bool:
        """Delete document by ID.

        Args:
            doc_id: Document ID

        Returns:
            True if successful
        """
        if not self._collection:
            return False

        try:
            self._collection.delete(ids=[doc_id])
            return True
        except Exception as e:
            print(f"Failed to delete document: {e}")
            return False

    def count(self) -> int:
        """Get number of documents in collection."""
        if not self._collection:
            return 0

        try:
            return self._collection.count()
        except Exception:
            return 0


# Global vector store instance
_vector_store: Optional[VectorStore] = None


def get_vector_store(collection_name: str = "research") -> VectorStore:
    """Get or create global vector store instance.

    Args:
        collection_name: Name of the collection

    Returns:
        VectorStore instance
    """
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore(collection_name)
    return _vector_store
