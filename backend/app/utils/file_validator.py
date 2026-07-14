import os
from fastapi import HTTPException, status

# Reusable utility function to validate that an uploaded file is a PDF
def validate_pdf_file(filename: str) -> None:
    """
    Validates that the file has a .pdf extension.
    If the file is not a PDF, raises an HTTPException with a 400 Bad Request status.
    """
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is missing or empty."
        )
    
    # Extract extension and convert to lowercase
    _, ext = os.path.splitext(filename)
    if ext.lower() != '.pdf':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type: {ext}. Only PDF files are allowed."
        )
