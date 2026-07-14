import os
import logging
import chromadb
import threading
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

# Define persistent directory for ChromaDB
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "chroma_db"))

# Thread-safe lock and references
_lock = threading.Lock()
_client = None

def get_client() -> chromadb.PersistentClient:
    """
    Initializes and returns the thread-safe persistent ChromaDB client.
    Automatically recreates DB folder if deleted.
    """
    global _client
    with _lock:
        if _client is None:
            try:
                # Handle deleted/missing database directory automatically
                if not os.path.exists(DB_PATH):
                    os.makedirs(DB_PATH, exist_ok=True)
                    logger.info(f"Recreated ChromaDB folder at: {DB_PATH}")
                    
                _client = chromadb.PersistentClient(path=DB_PATH)
                logger.info("ChromaDB PersistentClient successfully initialized.")
            except Exception as e:
                logger.error(f"Failed to initialize ChromaDB PersistentClient: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"ChromaDB initialization error: {str(e)}"
                )
        return _client

def get_collection() -> chromadb.Collection:
    """
    Dynamically loads and returns the current 'docmind_collection' from the client.
    Ensures that stale globally-cached Collection references are never returned.
    """
    client = get_client()
    with _lock:
        try:
            # Query client dynamically to ensure we fetch the latest valid reference
            collection = client.get_collection(name="docmind_collection")
        except Exception:
            # Create the collection if it does not exist
            collection = client.get_or_create_collection(name="docmind_collection")
            logger.info("Created new ChromaDB collection: docmind_collection")
        
        uuid_str = getattr(collection, "id", "Unknown-UUID")
        count = collection.count()
        logger.info(f"Loaded collection 'docmind_collection' (UUID: {uuid_str}) containing {count} document(s).")
        return collection

def recreate_collection() -> chromadb.Collection:
    """
    Safely deletes the old collection, creates a new one immediately, and returns the new instance.
    """
    client = get_client()
    with _lock:
        logger.warning("Recreating collection 'docmind_collection' due to dimension changes or reset request...")
        try:
            client.delete_collection(name="docmind_collection")
            logger.info("Deleted old ChromaDB collection 'docmind_collection' successfully.")
        except Exception as del_err:
            logger.error(f"Failed to delete old collection: {str(del_err)}")
        
        # Recreate immediately
        new_collection = client.get_or_create_collection(name="docmind_collection")
        uuid_str = getattr(new_collection, "id", "Unknown-UUID")
        logger.info(f"Successfully recreated ChromaDB collection 'docmind_collection' (New UUID: {uuid_str}).")
        return new_collection

def collection_exists() -> bool:
    """
    Checks if the collection 'docmind_collection' exists in ChromaDB.
    """
    client = get_client()
    with _lock:
        try:
            client.get_collection(name="docmind_collection")
            return True
        except Exception:
            return False

def validate_collection_dimension(expected_dim: int) -> bool:
    """
    Compares the existing collection dimension with the active embedding model dimension.
    Returns True if they match or if the collection is empty, and False if there is a mismatch.
    """
    collection = get_collection()
    try:
        # Retrieve the first embedding vector to verify its dimension length
        data = collection.get(include=["embeddings"], limit=1)
    except Exception as e:
        logger.error(f"Failed to retrieve collection metadata: {str(e)}")
        return False

    if data is not None and data.get("embeddings") is not None and len(data["embeddings"]) > 0:
        existing_dim = len(data["embeddings"][0])
        logger.info(f"Collection dimension: {existing_dim}, Model expected dimension: {expected_dim}")
        return existing_dim == expected_dim
    
    # If the collection is empty, the dimension is compatible (no lock established yet)
    logger.info("ChromaDB collection is empty. Dimension validation bypassed.")
    return True
