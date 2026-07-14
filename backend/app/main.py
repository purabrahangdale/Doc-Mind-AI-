import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.health import router as health_router
from app.api.routes.upload import router as upload_router
from app.api.routes.chat import router as chat_router
from app.services.startup_validator import run_startup_validation

# Configure logger
logger = logging.getLogger(__name__)

# Initialize the FastAPI application with metadata
app = FastAPI(
    title="DocMind AI API",
    description="Backend API for the DocMind AI application",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    """
    Runs the full startup validation gate before serving any requests.

    Verifies:
      - Gemini API key, client, embedding model, chat model
      - ChromaDB client and collection
      - Embedding dimension consistency (auto-repair + reindex on mismatch)
      - Uploaded PDF inventory

    Any unrecoverable failure raises an exception, which prevents uvicorn
    from marking the application as ready to serve traffic.
    """
    run_startup_validation()   # raises on any unrecoverable failure

# Define allowed origins for CORS.
# In development, the React frontend runs on http://localhost:5173.
# In production, these should be restricted to trusted domains.
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# Add CORS middleware to allow cross-origin requests from the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all request headers
)

# Register endpoints and routers
# Include the health check router containing the root endpoint
app.include_router(health_router)

# Include the upload router containing file-handling endpoints
app.include_router(upload_router)

# Include the chat router containing question-answering endpoints
app.include_router(chat_router)


