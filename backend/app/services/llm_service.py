from fastapi import HTTPException, status
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.core.config import get_chat_model

# 1. Define a professional prompt template instructing the model to answer strictly based on context
PROMPT_TEMPLATE = (
    "You are a helpful assistant called DocMind-AI. You are tasked with answering questions based ONLY "
    "on the provided context from the uploaded documents. Do not assume, extrapolate, or use any outside knowledge.\n\n"
    "If the answer is not available or cannot be derived from the context, you MUST respond exactly with:\n"
    "\"I couldn't find that information in the uploaded documents.\"\n\n"
    "Context:\n"
    "--- \n"
    "{context}\n"
    "--- \n\n"
    "Question: {question}\n"
    "Answer:"
)

# 2. Create the prompt template
prompt = PromptTemplate(
    template=PROMPT_TEMPLATE,
    input_variables=["context", "question"]
)

def generate_answer(question: str, context: str) -> str:
    """
    Generates an answer for a user question based strictly on the provided document context
    using the configured LLM.

    Args:
        question (str): The user query/question.
        context (str): The retrieved text context from documents.

    Returns:
        str: The generated answer from the LLM, or the fallback message if not found.

    Raises:
        HTTPException: If query/context validation fails, or if answer generation encounters an error.
    """
    # 3. Input validation: Ensure question is not empty or whitespace
    if not question or not question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The question cannot be empty or contain only whitespace."
        )
    
    # 4. Input validation: Ensure context is not empty or whitespace
    if not context or not context.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The context cannot be empty or contain only whitespace."
        )

    try:
        # 5. Initialize the chat model dynamically
        llm = get_chat_model()
        
        # 6. Construct LCEL chain incorporating prompt, model, and string output parser
        chain = prompt | llm | StrOutputParser()

        # 7. Invoke the LCEL chain and return the parsed final answer string
        answer = chain.invoke({
            "context": context,
            "question": question
        })
        
        return answer.strip()

    except HTTPException as he:
        raise he
    except Exception as e:
        # 8. Handle LLM invocation errors gracefully and raise HTTPException
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while generating the answer with Gemini: {str(e)}"
        )
