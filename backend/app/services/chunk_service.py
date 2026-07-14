from fastapi import HTTPException, status
from langchain_text_splitters import RecursiveCharacterTextSplitter

def chunk_text(text: str) -> list[str]:
    """
    Splits the provided text into smaller, overlapping chunks using LangChain's
    RecursiveCharacterTextSplitter.

    Args:
        text (str): The raw extracted text content to be chunked.

    Returns:
        list[str]: A list of text chunks.

    Raises:
        HTTPException: If the input text is empty, contains only whitespace, or is None.
    """
    # 1. Validate input text: Handle empty, None, or whitespace-only inputs safely.
    if not text or not text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Input text cannot be empty or contain only whitespace."
        )

    # 2. Configure the RecursiveCharacterTextSplitter with the specified parameters.
    # We use chunk_size = 500 and chunk_overlap = 50.
    # RecursiveCharacterTextSplitter attempts to split by paragraphs, sentences,
    # words, and characters recursively to maintain semantic coherence.
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        length_function=len,
        is_separator_regex=False
    )

    try:
        # 3. Perform the text splitting and return the list of chunks.
        chunks = splitter.split_text(text)
        return chunks
    except Exception as e:
        # 4. Handle any unexpected errors during splitting gracefully.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while chunking the text: {str(e)}"
        )
