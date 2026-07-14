import logging
from fastapi import HTTPException, status
from app.services.embedding_service import generate_query_embedding
from app.services.chroma_manager import get_collection

logger = logging.getLogger(__name__)

def retrieve_relevant_chunks(
    query: str,
    top_k: int = 3,
    document_id: str = None
) -> list[dict]:
    """
    Retrieves the top_k relevant text chunks from ChromaDB for a given query,
    optionally filtering by document_id.

    Args:
        query (str): The search query.
        top_k (int, optional): The number of top relevant documents to retrieve. Defaults to 3.
        document_id (str, optional): The unique ID of the document to scope results.

    Returns:
        list[dict]: A list of dictionaries containing the relevant chunks, metadata, and distance.

    Raises:
        HTTPException: If query validation fails, the document doesn't exist, or retrieval encounters an error.
    """
    # 1. Validate that the query is not empty or whitespace
    if not query or not query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The retrieval query cannot be empty or contain only whitespace."
        )

    # 2. Validate that top_k is greater than zero
    if top_k <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The top_k parameter must be greater than zero."
        )

    # 3. Retrieve the centralized shared Chroma collection
    collection = get_collection()

    # 4. Validate that document exists in our collection if document_id is supplied
    if document_id:
        try:
            existing = collection.get(where={"document_id": document_id}, limit=1)
            if not existing or not existing.get("ids"):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document with ID '{document_id}' was not found in the vector database."
                )
        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Failed to verify document existence: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to query database for document existence check: {str(e)}"
            )

    try:
        # 5. Generate embedding vector for the user query string using the centralized helper
        query_embedding = generate_query_embedding(query)

        # Build metadata filter if document_id is specified
        where_filter = None
        if document_id:
            where_filter = {"document_id": document_id}

        # 7. Perform similarity query in ChromaDB using the query embedding
        query_results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter
        )

        # 8. Extract results and map them to the specified response format
        formatted_results = []
        
        # ChromaDB query returns lists of lists (since we queried with query_embeddings=[...])
        # If there are results, let's unpack them safely
        if query_results and "documents" in query_results and query_results["documents"]:
            documents = query_results["documents"][0]
            metadatas = query_results.get("metadatas", [[]])[0]
            distances = query_results.get("distances", [[]])[0]

            for i in range(len(documents)):
                formatted_results.append({
                    "text": documents[i],
                    "metadata": metadatas[i] if i < len(metadatas) else {},
                    "distance": float(distances[i]) if i < len(distances) else 0.0
                })

        return formatted_results

    except HTTPException as he:
        raise he
    except Exception as e:
        # 9. Handle exceptions safely and raise HTTPException
        logger.error(f"Error during chunk retrieval: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during chunk retrieval: {str(e)}"
        )
