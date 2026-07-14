from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    """
    Schema for a chat request.
    """
    question: str = Field(..., description="The user query or question to be answered by the RAG model")
    document_id: str | None = Field(default=None, description="Optional document ID to restrict query context")

class ChatResponse(BaseModel):
    """
    Schema for a chat response.
    """
    question: str = Field(..., description="The original user query or question")
    answer: str = Field(..., description="The generated answer from the RAG pipeline")
    sources: list = Field(..., description="A list of unique document sources metadata that contributed to the answer")
