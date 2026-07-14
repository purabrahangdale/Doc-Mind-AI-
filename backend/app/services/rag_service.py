from fastapi import HTTPException, status
from app.services.retriever_service import retrieve_relevant_chunks
from app.services.llm_service import generate_answer

def ask_question(question: str, document_id: str = None) -> dict:
    """
    Coordinates the complete RAG (Retrieval-Augmented Generation) pipeline:
    1. Validates the question.
    2. Retrieves relevant document chunks (filtering by document_id if provided).
    3. Merges chunks to build context.
    4. Generates an answer using the LLM.
    5. Returns a structured dictionary containing the question, answer, and sources.

    Args:
        question (str): The question asked by the user.
        document_id (str, optional): The unique ID of the document to scope results.

    Returns:
        dict: A dictionary of the form:
            {
                "question": str,
                "answer": str,
                "sources": list[dict]
            }

    Raises:
        HTTPException: If validation fails or any step in the pipeline fails.
    """
    # 1. Validate that the question is not empty or whitespace
    if not question or not question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The question cannot be empty or contain only whitespace."
        )

    try:
        # 2. Retrieve relevant chunks from the vector store
        # We retrieve the top 3 relevant chunks
        retrieved_chunks = retrieve_relevant_chunks(question, top_k=3, document_id=document_id)

        # 3. Handle case where no relevant chunks are found
        if not retrieved_chunks:
            return {
                "question": question,
                "answer": "I couldn't find that information in the uploaded documents.",
                "sources": []
            }

        # 4. Extract text from chunks and merge them into a single context string
        context_parts = [chunk["text"] for chunk in retrieved_chunks]
        combined_context = "\n\n".join(context_parts)

        # 5. Extract unique sources/metadata for attribution
        sources = []
        for chunk in retrieved_chunks:
            meta = chunk.get("metadata", {})
            if meta and meta not in sources:
                sources.append(meta)

        # 6. Pass the combined context and question to the LLM service to generate answer
        answer = generate_answer(question, combined_context)

        # 7. Return the final structured response
        return {
            "question": question,
            "answer": answer,
            "sources": sources
        }

    except HTTPException as he:
        # Re-raise HTTPExceptions as-is
        raise he
    except Exception as e:
        # 8. Handle any unexpected errors in the pipeline and raise HTTPException
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred in the RAG pipeline: {str(e)}"
        )
