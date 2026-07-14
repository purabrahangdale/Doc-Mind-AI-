import os
import logging

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────
#  STARTUP VALIDATOR
#  Runs every time uvicorn boots.  Any exception that is NOT
#  caught here will propagate and prevent startup.
# ─────────────────────────────────────────────────────────

def run_startup_validation() -> None:
    """
    Full startup validation gate.  Steps:

      1. Gemini API key
      2. Gemini client
      3. Embedding model
      4. Chat model
      5. ChromaDB client
      6. ChromaDB collection
      7. Embedding dimension check
         → On mismatch: delete collection, recreate, reindex PDFs
      8. Report uploaded PDF count
      9. Confirm everything is ready

    Raises on any unrecoverable failure so that uvicorn refuses to start.
    """

    logger.info("=" * 60)
    logger.info("  DocMind AI — Startup Validation")
    logger.info("=" * 60)

    # ── Step 1 · API Key ─────────────────────────────────────────
    logger.info("[1/9] Verifying Gemini API key...")
    from app.core.config import get_api_key
    api_key = get_api_key()          # raises HTTPException on failure
    logger.info(f"      ✓ Gemini API key present ({api_key[:6]}…)")

    # ── Step 2 · Gemini Client ───────────────────────────────────
    logger.info("[2/9] Initializing Gemini client...")
    from app.core.config import get_gemini_client
    get_gemini_client()              # raises on failure
    logger.info("      ✓ Gemini client ready")

    # ── Step 3 · Embedding Model ─────────────────────────────────
    logger.info("[3/9] Loading embedding model...")
    from app.core.config import get_embedding_model, EMBEDDING_MODEL_NAME
    get_embedding_model()            # raises on failure
    logger.info(f"      ✓ Embedding model ready  ({EMBEDDING_MODEL_NAME})")

    # ── Step 4 · Chat Model ──────────────────────────────────────
    logger.info("[4/9] Loading chat model...")
    from app.core.config import get_chat_model, CHAT_MODEL_NAME
    get_chat_model()                 # raises on failure
    logger.info(f"      ✓ Chat model ready  ({CHAT_MODEL_NAME})")

    # ── Step 5 · ChromaDB Client ─────────────────────────────────
    logger.info("[5/9] Connecting to ChromaDB...")
    from app.services.chroma_manager import get_client
    client = get_client()            # raises on failure
    logger.info("      ✓ ChromaDB client connected")

    # ── Step 6 · Collection ──────────────────────────────────────
    logger.info("[6/9] Loading ChromaDB collection...")
    from app.services.chroma_manager import get_collection
    collection = get_collection()    # creates if not exists; raises on real failure
    doc_count = collection.count()
    logger.info(f"      ✓ Collection 'docmind_collection' ready  ({doc_count} chunk(s) stored)")

    # ── Step 7 · Embedding Dimension ────────────────────────────
    logger.info("[7/9] Validating embedding dimension...")
    from app.services.embedding_service import get_embedding_dimension
    from app.services.chroma_manager import validate_collection_dimension, recreate_collection
    from app.services.vector_service import reindex_all_documents

    expected_dim = get_embedding_dimension()   # live API call → real dimension
    logger.info(f"      Active model dimension: {expected_dim}")

    if not validate_collection_dimension(expected_dim):
        logger.warning("      ✗ Dimension mismatch detected — beginning repair...")

        logger.info("        → Deleting stale collection...")
        recreate_collection()
        logger.info("        → Collection recreated successfully")

        logger.info("        → Reindexing uploaded PDFs...")
        reindex_all_documents()          # raises if reindex itself crashes fatally
        logger.info("        → Reindexing complete")

        # Final sanity check — validate dimension of freshly inserted data
        if not validate_collection_dimension(expected_dim):
            raise RuntimeError(
                f"Startup aborted: ChromaDB collection dimension still invalid after repair. "
                f"Expected {expected_dim}. Collection must be fixed before starting."
            )
        logger.info(f"      ✓ Dimension repaired and verified: {expected_dim}")
    else:
        logger.info(f"      ✓ Embedding dimension verified: {expected_dim}")

    # ── Step 8 · Uploaded PDFs ───────────────────────────────────
    logger.info("[8/9] Scanning uploaded PDFs...")
    upload_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "uploads"
    )
    if os.path.isdir(upload_dir):
        pdf_files = [f for f in os.listdir(upload_dir) if f.lower().endswith(".pdf")]
        logger.info(f"      ✓ Found {len(pdf_files)} PDF(s) in uploads/  {pdf_files if pdf_files else ''}")
    else:
        logger.info("      ✓ No uploads/ directory yet — will be created on first upload")

    # ── Step 9 · All clear ───────────────────────────────────────
    logger.info("[9/9] All checks passed.")
    logger.info("=" * 60)
    logger.info("  DocMind AI — Ready to serve requests ✓")
    logger.info("=" * 60)
