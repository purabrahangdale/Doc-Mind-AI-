import logging
from fastapi import HTTPException, status
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from app.core.config import get_embedding_model, get_chat_model, EMBEDDING_MODEL_NAME

logger = logging.getLogger(__name__)

def get_embeddings_model() -> GoogleGenerativeAIEmbeddings:
    """
    Returns the centralized GoogleGenerativeAIEmbeddings instance from config.
    """
    return get_embedding_model()

def get_embedding_dimension() -> int:
    """
    Dynamically detects the embedding dimension of the Google Gemini model.
    Raises HTTPException if dimension retrieval fails.
    """
    try:
        model = get_embeddings_model()
        test_vector = model.embed_query("dimension_test")
        return len(test_vector)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve Gemini embedding dimension: {str(e)}"
        )

def generate_embeddings(chunks: list[str]) -> list[dict]:
    """
    Generates embedding vectors for a list of text chunks using the centralized Google Gemini embeddings.

    Args:
        chunks (list[str]): A list of text chunks to embed.

    Returns:
        list[dict]: A list of dictionaries, each containing:
            - "text": The original chunk text.
            - "embedding": The generated embedding vector (list of floats).

    Raises:
        HTTPException: If the input list is empty or if any internal error occurs.
    """
    # 1. Validate that the input list is not empty
    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The chunks list cannot be empty."
        )

    try:
        embeddings_model = get_embeddings_model()

        # 2. Batch generate embeddings for all chunks to optimize performance
        embedding_vectors = embeddings_model.embed_documents(chunks)

        # 3. Map each chunk to its corresponding embedding vector
        result = [
            {
                "text": chunk,
                "embedding": vector
            }
            for chunk, vector in zip(chunks, embedding_vectors)
        ]

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate Gemini embeddings: {str(e)}"
        )

def generate_query_embedding(query: str) -> list[float]:
    """
    Generates a single query embedding vector using the centralized embeddings model.
    """
    if not query or not query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query string cannot be empty or whitespace."
        )
    try:
        model = get_embeddings_model()
        return model.embed_query(query)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate query embedding: {str(e)}"
        )
