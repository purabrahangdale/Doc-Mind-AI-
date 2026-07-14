import os
import shutil
import uuid
import logging
from datetime import datetime

from fastapi import HTTPException, UploadFile, status

from app.services.pdf_service import extract_text_per_page, get_pdf_page_count
from app.services.chunk_service import chunk_text
from app.services.embedding_service import generate_embeddings
from app.services.vector_service import store_embeddings
from app.services.chroma_manager import get_collection

logger = logging.getLogger(__name__)

# Absolute path to the uploads directory (backend/app/uploads/)
UPLOAD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads"
)


def _check_duplicate(filename: str) -> bool:
    """
    Returns True if at least one chunk for this filename already exists in ChromaDB.
    Uses a metadata filter query to avoid iterating all documents.
    """
    try:
        collection = get_collection()
        results = collection.get(where={"filename": filename}, limit=1)
        return bool(results and results.get("ids"))
    except Exception:
        # If the query itself fails (e.g. empty collection), assume no duplicate
        return False


def save_uploaded_file(file: UploadFile) -> dict:
    """
    Full upload pipeline:

      1. Validate the filename is not empty and is a PDF
      2. Reject duplicate uploads (409 Conflict)
      3. Save the file to disk
      4. Extract text per-page (422 if entirely empty)
      5. Chunk each page's text, tagging every chunk with its real page_number
      6. Batch-generate Gemini embeddings for all chunks
      7. Attach rich metadata to every embedded item
      8. Store in ChromaDB
      9. On any processing failure after file save: delete the file and re-raise

    Returns:
        dict with filename, message, characters, pages, chunks, document_id
    """

    # ── 1. Basic filename validation ──────────────────────────────────────────
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided."
        )
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only PDF files are accepted. Got: '{file.filename}'"
        )

    # ── 2. Duplicate detection ────────────────────────────────────────────────
    if _check_duplicate(file.filename):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"'{file.filename}' has already been uploaded and indexed. "
                "Delete it first if you want to re-index it."
            )
        )

    # ── 3. Save to disk ───────────────────────────────────────────────────────
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    try:
        with open(file_path, "wb") as buf:
            shutil.copyfileobj(file.file, buf)
        logger.info(f"Saved uploaded file to: {file_path}")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file to disk: {str(e)}"
        )

    # All subsequent steps run inside a try block so we can clean up on failure
    try:
        # ── 4. Extract text per-page ──────────────────────────────────────────
        pages = extract_text_per_page(file_path)           # list[{page_number, text}]
        page_count = len(pages)

        pages_with_text = [p for p in pages if p["text"]]
        if not pages_with_text:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"'{file.filename}' contains no extractable text. "
                    "It may be a scanned image-only PDF. Please use a text-based PDF."
                )
            )

        total_characters = sum(len(p["text"]) for p in pages_with_text)
        logger.info(
            f"Extracted text from {len(pages_with_text)}/{page_count} page(s) "
            f"({total_characters} chars)."
        )

        # ── 5. Chunk each page, preserve page_number per chunk ────────────────
        # chunk_text() returns list[str]; we track which page each chunk came from
        page_chunks: list[dict] = []   # [{"text": str, "page_number": int}]

        for page in pages_with_text:
            try:
                raw_chunks = chunk_text(page["text"])
            except HTTPException:
                # Page text was empty/whitespace after strip — skip silently
                continue
            for raw_chunk in raw_chunks:
                page_chunks.append({
                    "text": raw_chunk,
                    "page_number": page["page_number"]
                })

        if not page_chunks:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"No usable text chunks could be created from '{file.filename}'. "
                    "The document content may be too short or malformed."
                )
            )

        logger.info(f"Created {len(page_chunks)} chunk(s) from {file.filename}.")

        # ── 6. Generate Gemini embeddings (single batch) ──────────────────────
        chunk_texts = [pc["text"] for pc in page_chunks]
        embedded_items = generate_embeddings(chunk_texts)
        # Returns list[{"text": str, "embedding": list[float]}]

        # ── 7. Attach rich metadata ───────────────────────────────────────────
        document_id = str(uuid.uuid4())
        upload_timestamp = datetime.utcnow().isoformat()

        for global_idx, (item, page_chunk) in enumerate(
            zip(embedded_items, page_chunks)
        ):
            item["metadata"] = {
                "document_id":      document_id,
                "filename":         file.filename,
                "chunk_index":      global_idx,
                "page_number":      page_chunk["page_number"],
                "upload_timestamp": upload_timestamp,
                "source":           "uploaded_pdf"
            }

        # ── 8. Store in ChromaDB ──────────────────────────────────────────────
        store_embeddings(embedded_items)
        logger.info(
            f"Successfully indexed '{file.filename}' "
            f"({len(embedded_items)} chunk(s), document_id={document_id})."
        )

        return {
            "filename":    file.filename,
            "message":     "File uploaded and indexed successfully.",
            "characters":  total_characters,
            "pages":       page_count,
            "chunks":      len(embedded_items),
            "document_id": document_id
        }

    except HTTPException:
        # Clean up the saved file before propagating known HTTP errors
        _cleanup_file(file_path)
        raise

    except Exception as e:
        # Clean up the saved file for unexpected errors, then surface as 500
        _cleanup_file(file_path)
        logger.error(f"Upload pipeline failed for '{file.filename}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload pipeline failed: {str(e)}"
        )


def _cleanup_file(file_path: str) -> None:
    """Silently removes a file from disk if it exists."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up failed upload: {file_path}")
    except Exception as cleanup_err:
        logger.warning(f"Could not clean up file '{file_path}': {cleanup_err}")
