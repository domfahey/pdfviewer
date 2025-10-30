"""
Integration tests for various sample PDF documents.

This module consolidates sample PDF testing by using pytest parametrization
to test multiple PDF documents against common validation and processing workflows.

The sample PDFs test different characteristics:
- EPA: Government document with standard formatting
- Weblite: Scanned document with OCR content
- PrinceXML: Large document with complex formatting
- Anyline: Document with barcodes and images
- NHTSA: Form document with form fields
"""

import pytest


# Define sample PDF configurations
SAMPLE_PDFS = [
    pytest.param(
        "epa_sample_pdf_file",
        {
            "name": "EPA Sample Letter",
            "min_pages": 1,
            "max_pages": 5,
            "has_text": True,
            "min_size_bytes": 10000,
        },
        id="epa",
    ),
    pytest.param(
        "weblite_sample_pdf_file",
        {
            "name": "Weblite OCR Sample",
            "min_pages": 1,
            "max_pages": 10,
            "has_text": True,
            "min_size_bytes": 50000,
        },
        id="weblite",
    ),
    pytest.param(
        "princexml_sample_pdf_file",
        {
            "name": "PrinceXML Essay",
            "min_pages": 10,
            "max_pages": 100,
            "has_text": True,
            "min_size_bytes": 100000,
        },
        id="princexml",
    ),
    pytest.param(
        "anyline_sample_pdf_file",
        {
            "name": "Anyline Scan Book",
            "min_pages": 5,
            "max_pages": 50,
            "has_text": True,
            "min_size_bytes": 500000,
        },
        id="anyline",
    ),
    pytest.param(
        "nhtsa_form_pdf_file",
        {
            "name": "NHTSA Form",
            "min_pages": 1,
            "max_pages": 20,
            "has_text": True,
            "min_size_bytes": 50000,
        },
        id="nhtsa",
    ),
]


class TestSamplePDFValidation:
    """Test that sample PDFs meet basic validation requirements."""

    @pytest.mark.parametrize("fixture_name,expected", SAMPLE_PDFS)
    def test_sample_pdf_exists(self, fixture_name, expected, request):
        """Test that sample PDF file exists and is readable."""
        pdf_file = request.getfixturevalue(fixture_name)
        
        assert pdf_file.exists(), f"{expected['name']} file should exist"
        assert pdf_file.is_file(), f"{expected['name']} should be a file"
        assert pdf_file.stat().st_size > 0, f"{expected['name']} should not be empty"

    @pytest.mark.parametrize("fixture_name,expected", SAMPLE_PDFS)
    def test_sample_pdf_size(self, fixture_name, expected, request):
        """Test that sample PDF meets size requirements."""
        pdf_file = request.getfixturevalue(fixture_name)
        file_size = pdf_file.stat().st_size
        
        assert (
            file_size >= expected["min_size_bytes"]
        ), f"{expected['name']} should be at least {expected['min_size_bytes']} bytes"

    @pytest.mark.parametrize("fixture_name,expected", SAMPLE_PDFS)
    def test_sample_pdf_is_valid_pdf(self, fixture_name, expected, request):
        """Test that sample PDF is a valid PDF file."""
        pdf_file = request.getfixturevalue(fixture_name)
        
        # Check PDF header
        with open(pdf_file, "rb") as f:
            header = f.read(5)
            assert header == b"%PDF-", f"{expected['name']} should have valid PDF header"


class TestSamplePDFUpload:
    """Test uploading sample PDFs through the API."""

    @pytest.mark.parametrize("fixture_name,expected", SAMPLE_PDFS)
    @pytest.mark.asyncio
    async def test_upload_sample_pdf(self, client, fixture_name, expected, request):
        """Test successful upload of sample PDF."""
        pdf_file = request.getfixturevalue(fixture_name)
        
        with open(pdf_file, "rb") as f:
            files = {"file": (pdf_file.name, f, "application/pdf")}
            response = client.post("/api/upload", files=files)
        
        assert response.status_code == 200, f"Upload {expected['name']} should succeed"
        data = response.json()
        
        assert "file_id" in data
        assert "filename" in data
        assert "metadata" in data
        
        # Cleanup
        file_id = data["file_id"]
        client.delete(f"/api/pdf/{file_id}")

    @pytest.mark.parametrize("fixture_name,expected", SAMPLE_PDFS)
    @pytest.mark.asyncio
    async def test_sample_pdf_metadata(self, client, fixture_name, expected, request):
        """Test metadata extraction from sample PDFs."""
        pdf_file = request.getfixturevalue(fixture_name)
        
        with open(pdf_file, "rb") as f:
            files = {"file": (pdf_file.name, f, "application/pdf")}
            response = client.post("/api/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        metadata = data["metadata"]
        
        # Verify page count is within expected range
        page_count = metadata["page_count"]
        assert (
            expected["min_pages"] <= page_count <= expected["max_pages"]
        ), f"{expected['name']} page count should be between {expected['min_pages']} and {expected['max_pages']}"
        
        # Cleanup
        file_id = data["file_id"]
        client.delete(f"/api/pdf/{file_id}")


class TestSamplePDFWorkflow:
    """Test complete workflow with sample PDFs."""

    @pytest.mark.parametrize("fixture_name,expected", SAMPLE_PDFS)
    @pytest.mark.asyncio
    async def test_complete_workflow(self, client, fixture_name, expected, request):
        """Test upload -> retrieve -> delete workflow with sample PDFs."""
        pdf_file = request.getfixturevalue(fixture_name)
        
        # 1. Upload
        with open(pdf_file, "rb") as f:
            files = {"file": (pdf_file.name, f, "application/pdf")}
            upload_response = client.post("/api/upload", files=files)
        
        assert upload_response.status_code == 200
        file_id = upload_response.json()["file_id"]
        
        # 2. Get metadata
        metadata_response = client.get(f"/api/pdf/{file_id}/metadata")
        assert metadata_response.status_code == 200
        
        # 3. Get file
        file_response = client.get(f"/api/pdf/{file_id}/file")
        assert file_response.status_code == 200
        assert file_response.headers["content-type"] == "application/pdf"
        
        # 4. Delete
        delete_response = client.delete(f"/api/pdf/{file_id}")
        assert delete_response.status_code == 200
        
        # 5. Verify deletion
        verify_response = client.get(f"/api/pdf/{file_id}/metadata")
        assert verify_response.status_code == 404
