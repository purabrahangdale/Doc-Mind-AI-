from fastapi import APIRouter, HTTPException, status
from app.schemas.chat_schema import ChatRequest, ChatResponse
from app.services.rag_service import ask_question

# Initialize APIRouter for chat endpoints
router = APIRouter(prefix="/chat", tags=["chat"])

@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate answer from document context",
    description="Submit a question to query the uploaded document context and generate a RAG response."
)
async def chat_endpoint(payload: ChatRequest) -> ChatResponse:
    """
    POST endpoint to interact with the RAG assistant.
    """
    try:
        # Call the RAG pipeline service using the user's question and document_id
        result = ask_question(payload.question, payload.document_id)
        
        # Return the response mapped to the ChatResponse schema
        return ChatResponse(
            question=result["question"],
            answer=result["answer"],
            sources=result["sources"]
        )
    except HTTPException as he:
        # Re-raise FastAPIs HTTPExceptions
        raise he
    except Exception as e:
        # Catch-all for unexpected pipeline errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred on the server: {str(e)}"
        )
