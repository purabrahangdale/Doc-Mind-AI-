from pydantic import BaseModel, Field

# Schema representing a successful upload response with document metadata
class UploadSuccessResponse(BaseModel):
    filename: str = Field(..., description="The name of the saved file")
    message: str = Field(..., description="Details about the status of the upload operation")
    characters: int = Field(..., description="Total character count of the extracted PDF text")
    pages: int = Field(..., description="Total page count of the uploaded PDF")
    chunks: int = Field(..., description="Total number of chunks created from the PDF")
    document_id: str = Field(..., description="The unique UUID generated for this document")
    already_indexed: bool = Field(
        default=False,
        description="True if the file was already indexed and this upload was a duplicate"
    )

