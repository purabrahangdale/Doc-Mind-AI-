from fastapi import APIRouter, File, UploadFile
from app.utils.file_validator import validate_pdf_file
from app.services.upload_service import save_uploaded_file
from app.schemas.upload_schema import UploadSuccessResponse

# Initialize the router for upload-related endpoints
router = APIRouter()

@router.post("/upload", response_model=UploadSuccessResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    Endpoint to receive and store a single PDF file.
    Validates that the file is a PDF before saving it.
    """
    # Validate that the file is a PDF
    validate_pdf_file(file.filename)
    
    # Save the file using the service layer
    result = save_uploaded_file(file)
    
    return result
