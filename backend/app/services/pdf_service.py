import fitz  # PyMuPDF
from fastapi import HTTPException, status

def extract_text_from_pdf(file_path: str) -> str:
    """
    Opens a PDF file, extracts text from all pages, combines them,
    strips leading/trailing whitespace, and closes the document safely.
    Raises HTTPException if the PDF cannot be opened or parsed.
    """
    try:
        # Open the PDF document
        doc = fitz.open(file_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to open the PDF file: {str(e)}"
        )

    try:
        text_parts = []
        # Iterate through every page in the document
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()
            if text:
                text_parts.append(text)
        
        # Combine all page text and strip unnecessary leading/trailing whitespace
        combined_text = "".join(text_parts).strip()
        return combined_text
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract text from the PDF file: {str(e)}"
        )
    finally:
        # Close the document properly
        doc.close()

def get_pdf_page_count(file_path: str) -> int:
    """
    Opens a PDF file to safely count the number of pages.
    Raises HTTPException if the PDF cannot be opened.
    """
    try:
        doc = fitz.open(file_path)
        page_count = len(doc)
        doc.close()
        return page_count
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read page count from PDF: {str(e)}"
        )

def extract_text_per_page(file_path: str) -> list[dict]:
    """
    Opens a PDF file and returns one entry per page with accurate page numbers.

    Returns:
        list[dict]: Each entry contains:
            - "page_number" (int, 1-indexed)
            - "text" (str, extracted text for that page, may be empty)

    Raises:
        HTTPException: If the PDF cannot be opened or parsed.
    """
    try:
        doc = fitz.open(file_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to open PDF for per-page extraction: {str(e)}"
        )

    try:
        pages = []
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text().strip()
            pages.append({
                "page_number": page_num + 1,   # 1-indexed
                "text": text
            })
        return pages
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract per-page text from PDF: {str(e)}"
        )
    finally:
        doc.close()
