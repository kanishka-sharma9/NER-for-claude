"""
MCP Server for PDF Text Extraction and NER API Integration
This server connects to Claude Desktop and processes PDF files
by extracting text and calling the NER FastAPI endpoint.
"""

from fastmcp import FastMCP
import httpx
import PyPDF2
from typing import Annotated
import io
import base64
import os

# Initialize MCP server
mcp = FastMCP("PDF NER Extractor")

# Configuration for your FastAPI app
FASTAPI_URL = "http://localhost:8000"
NER_ENDPOINT = f"{FASTAPI_URL}/ner"


def extract_text_from_pdf(pdf_content: bytes) -> str:
    """
    Extract text from PDF file content.

    Args:
        pdf_content: PDF file content as bytes

    Returns:
        Extracted text from the PDF
    """
    try:
        pdf_file = io.BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)

        text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text() + "\n"

        return text.strip()
    except Exception as e:
        raise Exception(f"Failed to extract text from PDF: {str(e)}")


async def call_ner_api(text: str) -> list:
    """
    Call the NER FastAPI endpoint with the extracted text.

    Args:
        text: Text to analyze

    Returns:
        NER results from the API
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                NER_ENDPOINT,
                json={"query": text}
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        raise Exception(f"Failed to call NER API: {str(e)}")


@mcp.tool()
async def analyze_pdf_ner(
    pdf_base64: Annotated[str, "Base64 encoded PDF file content"]
) -> Annotated[dict, "NER analysis results with extracted entities"]:
    """
    Extract text from a PDF file and perform Named Entity Recognition (NER) analysis.

    This tool:
    1. Decodes the base64-encoded PDF content
    2. Extracts text from all pages of the PDF
    3. Calls the NER API to identify entities in the text
    4. Returns the entities found with their scores and positions

    Args:
        pdf_base64: Base64 encoded PDF file content

    Returns:
        Dictionary containing extracted text and NER results
    """
    try:
        # Decode base64 PDF content
        pdf_content = base64.b64decode(pdf_base64)

        # Extract text from PDF
        extracted_text = extract_text_from_pdf(pdf_content)

        if not extracted_text:
            return {
                "success": False,
                "error": "No text could be extracted from the PDF"
            }

        # Call NER API
        ner_results = await call_ner_api(extracted_text)

        return {
            "success": True,
            "extracted_text": extracted_text,
            "text_length": len(extracted_text),
            "ner_results": ner_results,
            "entity_count": len(ner_results)
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def analyze_text_ner(
    text: Annotated[str, "Text content to analyze"]
) -> Annotated[dict, "NER analysis results"]:
    """
    Perform Named Entity Recognition (NER) analysis on provided text.

    This tool calls the NER API to identify entities in the given text.

    Args:
        text: Text content to analyze

    Returns:
        Dictionary containing NER results
    """
    try:
        # Call NER API
        ner_results = await call_ner_api(text)

        return {
            "success": True,
            "text_length": len(text),
            "ner_results": ner_results,
            "entity_count": len(ner_results)
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def check_api_status() -> Annotated[dict, "API health status"]:
    """
    Check if the NER FastAPI server is running and accessible.

    Returns:
        Status of the API connection
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{FASTAPI_URL}/docs")
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "NER API is running and accessible",
                    "url": FASTAPI_URL
                }
            else:
                return {
                    "success": False,
                    "message": f"API returned status code: {response.status_code}",
                    "url": FASTAPI_URL
                }
    except Exception as e:
        return {
            "success": False,
            "message": f"Cannot connect to API: {str(e)}",
            "url": FASTAPI_URL
        }


if __name__ == "__main__":
    # Run the MCP server using stdio transport for Claude Desktop
    mcp.run(transport="stdio")
