import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from fastapi import HTTPException, status
from google import genai
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI

logger = logging.getLogger(__name__)

# 1. Resolve path and load environment variables using pathlib
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BACKEND_DIR / ".env"

if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)

# Centralized constant configurations
EMBEDDING_MODEL_NAME = "models/gemini-embedding-001"
CHAT_MODEL_NAME = "gemini-2.5-flash"

# Singleton instances cache
_gemini_client = None
_embedding_model = None
_chat_model = None

def get_api_key() -> str:
    """
    Retrieves and validates the Gemini API key from environment variables.
    Raises HTTPException if not configured.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key or "your_gemini_api_key" in api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gemini API Key is missing. Please configure GEMINI_API_KEY or GOOGLE_API_KEY in your .env file."
        )
    return api_key

def get_gemini_client() -> genai.Client:
    """
    Returns the singleton Google GenAI client instance.
    """
    global _gemini_client
    if _gemini_client is None:
        api_key = get_api_key()
        try:
            # Set environment variable so the client can automatically fetch it
            os.environ["GOOGLE_API_KEY"] = api_key
            _gemini_client = genai.Client()
            logger.info("✓ Gemini initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Google GenAI Client: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Google GenAI Client initialization failed: {str(e)}"
            )
    return _gemini_client

def get_embedding_model() -> GoogleGenerativeAIEmbeddings:
    """
    Returns the singleton GoogleGenerativeAIEmbeddings instance.
    """
    global _embedding_model
    if _embedding_model is None:
        api_key = get_api_key()
        try:
            _embedding_model = GoogleGenerativeAIEmbeddings(
                model=EMBEDDING_MODEL_NAME,
                google_api_key=api_key
            )
            logger.info("✓ Embedding model loaded")
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Embedding model initialization failed: {str(e)}"
            )
    return _embedding_model

def get_chat_model() -> ChatGoogleGenerativeAI:
    """
    Returns the singleton ChatGoogleGenerativeAI instance.
    """
    global _chat_model
    if _chat_model is None:
        api_key = get_api_key()
        try:
            _chat_model = ChatGoogleGenerativeAI(
                model=CHAT_MODEL_NAME,
                temperature=0,
                google_api_key=api_key
            )
            logger.info("✓ Chat model loaded")
        except Exception as e:
            logger.error(f"Failed to initialize chat model: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Chat model initialization failed: {str(e)}"
            )
    return _chat_model
