import os
import uuid
import logging
from fastapi import HTTPException, status
from app.services.embedding_service import get_embedding_dimension, EMBEDDING_MODEL_NAME
from app.services.chroma_manager import (
    get_client,
    get_collection,
    recreate_collection,
    validate_collection_dimension,
    collection_exists
)

logger = logging.getLogger(__name__)

# Expose helper wrappers for backwards compatibility
def get_chroma_client():
    return get_client()

def reindex_all_documents() -> None:
    """
    Scans backend/app/uploads/ and re-indexes every stored PDF into ChromaDB.
    Uses per-page extraction so chunk metadata carries accurate page_number values.
    """
    try:
        from app.services.pdf_service import extract_text_per_page
        from app.services.chunk_service import chunk_text
        from app.services.embedding_service import generate_embeddings
        from datetime import datetime

        upload_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads"
        )
        if not os.path.exists(upload_dir):
            logger.info(f"Upload directory '{upload_dir}' does not exist. Skipping re-index.")
            return

        files = [f for f in os.listdir(upload_dir) if f.lower().endswith(".pdf")]
        if not files:
            logger.info("No PDF files found in uploads/. Skipping re-index.")
            return

        logger.info(f"Re-indexing {len(files)} document(s)...")

        for filename in files:
            file_path = os.path.join(upload_dir, filename)
            logger.info(f"  Re-indexing: {filename}")

            try:
                pages = extract_text_per_page(file_path)
                pages_with_text = [p for p in pages if p["text"]]

                if not pages_with_text:
                    logger.warning(f"  Skipping '{filename}' — no extractable text.")
                    continue

                # Build per-page chunks tagged with page_number
                page_chunks: list[dict] = []
                for page in pages_with_text:
                    try:
                        raw_chunks = chunk_text(page["text"])
                    except Exception:
                        continue
                    for raw_chunk in raw_chunks:
                        page_chunks.append({
                            "text": raw_chunk,
                            "page_number": page["page_number"]
                        })

                if not page_chunks:
                    logger.warning(f"  Skipping '{filename}' — no usable chunks.")
                    continue

                chunk_texts = [pc["text"] for pc in page_chunks]
                embedded_items = generate_embeddings(chunk_texts)

                doc_id = str(uuid.uuid4())
                upload_timestamp = datetime.utcnow().isoformat()

                for global_idx, (item, pc) in enumerate(zip(embedded_items, page_chunks)):
                    item["metadata"] = {
                        "document_id":      doc_id,
                        "filename":         filename,
                        "chunk_index":      global_idx,
                        "page_number":      pc["page_number"],
                        "upload_timestamp": upload_timestamp,
                        "source":           "uploaded_pdf"
                    }

                store_embeddings(embedded_items)
                logger.info(f"  ✓ Re-indexed '{filename}' ({len(embedded_items)} chunk(s)).")

            except Exception as file_err:
                logger.error(f"  Failed to re-index '{filename}': {file_err}")
                # Continue with next file rather than aborting the whole reindex

    except Exception as re_err:
        logger.error(f"reindex_all_documents failed: {re_err}")
        logger.warning("Auto re-indexing failed. Please upload your documents again.")


def validate_and_repair_db() -> None:
    """
    Verifies that the collection's embedding dimension matches the configured model.
    Deletes and recreates the collection, then auto re-indexes if a mismatch is found.
    """
    logger.info("Running vector database dimension validation check...")
    expected_dim = get_embedding_dimension()
    
    # Run the validation from chroma_manager
    if not validate_collection_dimension(expected_dim):
        logger.warning("Embedding dimension mismatch detected! Recreating collection...")
        recreate_collection()
        reindex_all_documents()
    else:
        logger.info("Database verification successful. Embedding dimensions match.")

def store_embeddings(items: list[dict]) -> None:
    """
    Stores text chunks and their corresponding embedding vectors in the ChromaDB collection.
    """
    if not items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The items list to store cannot be empty."
        )

    ids = []
    documents = []
    embeddings = []
    metadatas = []

    for item in items:
        text = item.get("text")
        embedding = item.get("embedding")
        
        if not text or not embedding:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Each item must contain non-empty 'text' and 'embedding' fields."
            )
        
        unique_id = str(uuid.uuid4())
        
        ids.append(unique_id)
        documents.append(text)
        embeddings.append(embedding)
        
        item_metadata = item.get("metadata", {})
        if not isinstance(item_metadata, dict):
            item_metadata = {}
        if "source" not in item_metadata:
            item_metadata["source"] = "uploaded_pdf"
            
        metadatas.append(item_metadata)

    col = get_collection()
    try:
        col.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
    except Exception as e:
        error_msg = str(e).lower()
        if "dimension" in error_msg or "dimensionality" in error_msg or "does not match" in error_msg:
            try:
                logger.warning("Dimension mismatch caught during store_embeddings. Resetting collection.")
                col = recreate_collection()
                col.upsert(
                    ids=ids,
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas
                )
                return
            except Exception as inner_e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Dimension mismatch detected, and failed to reset collection: {str(inner_e)}"
                )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while storing embeddings in the vector database: {str(e)}"
        )
