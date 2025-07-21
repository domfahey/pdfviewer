"""
Integration tests for complete PDF processing workflow.
"""
import io
import time
from pathlib import Path

import pytest
from fastapi import status
from httpx import AsyncClient
# from PIL import Image  # Optional: for image validation

from backend.app.models.pdf import PDFMetadata


class TestPDFWorkflow:
    """Test complete PDF processing workflows."""
    
    @pytest.mark.asyncio
    async def test_full_pdf_processing_workflow(
        self, async_client: AsyncClient, sample_pdf_path: Path, test_upload_dir: Path
    ):
        """Test complete workflow: upload → analyze → retrieve → delete."""
        # Step 1: Upload PDF
        with open(sample_pdf_path, "rb") as f:
            files = {"file": ("test.pdf", f, "application/pdf")}
            upload_response = await async_client.post("/api/upload", files=files)
        
        assert upload_response.status_code == status.HTTP_200_OK
        upload_data = upload_response.json()
        assert "document_id" in upload_data
        document_id = upload_data["document_id"]
        
        # Verify file was saved
        saved_file = test_upload_dir / f"{document_id}.pdf"
        assert saved_file.exists()
        
        # Step 2: Analyze PDF
        analysis_response = await async_client.post(
            f"/api/pdf/analyze/{document_id}"
        )
        assert analysis_response.status_code == status.HTTP_200_OK
        analysis_data = analysis_response.json()
        
        # Validate analysis response
        assert "total_pages" in analysis_data
        assert "extracted_fields" in analysis_data
        assert analysis_data["document_id"] == document_id
        
        # Step 3: Get PDF metadata
        metadata_response = await async_client.get(
            f"/api/pdf/metadata/{document_id}"
        )
        assert metadata_response.status_code == status.HTTP_200_OK
        metadata = metadata_response.json()
        
        # Validate metadata
        assert metadata["filename"] == "test.pdf"
        assert metadata["page_count"] > 0
        
        # Step 4: Get page preview
        page_response = await async_client.get(
            f"/api/pdf/page/{document_id}/1"
        )
        assert page_response.status_code == status.HTTP_200_OK
        assert page_response.headers["content-type"] == "image/png"
        
        # Verify it's a valid PNG by checking magic bytes
        assert page_response.content[:8] == b'\x89PNG\r\n\x1a\n'
        
        # Step 5: Download original PDF
        download_response = await async_client.get(
            f"/api/pdf/download/{document_id}"
        )
        assert download_response.status_code == status.HTTP_200_OK
        assert download_response.headers["content-type"] == "application/pdf"
        assert len(download_response.content) > 0
        
        # Step 6: Delete PDF
        delete_response = await async_client.delete(
            f"/api/pdf/{document_id}"
        )
        assert delete_response.status_code == status.HTTP_200_OK
        
        # Verify file was deleted
        assert not saved_file.exists()
        
        # Verify we can't access deleted PDF
        get_deleted_response = await async_client.get(
            f"/api/pdf/metadata/{document_id}"
        )
        assert get_deleted_response.status_code == status.HTTP_404_NOT_FOUND
    
    @pytest.mark.asyncio
    async def test_concurrent_pdf_processing(
        self, async_client: AsyncClient, sample_pdf_path: Path
    ):
        """Test handling multiple concurrent PDF uploads and processing."""
        import asyncio
        
        async def upload_and_analyze(file_num: int):
            """Upload and analyze a single PDF."""
            with open(sample_pdf_path, "rb") as f:
                files = {"file": (f"test_{file_num}.pdf", f, "application/pdf")}
                upload_response = await async_client.post("/api/upload", files=files)
            
            assert upload_response.status_code == status.HTTP_200_OK
            document_id = upload_response.json()["document_id"]
            
            # Analyze PDF
            analysis_response = await async_client.post(
                f"/api/pdf/analyze/{document_id}"
            )
            assert analysis_response.status_code == status.HTTP_200_OK
            
            return document_id, analysis_response.json()
        
        # Upload and analyze 5 PDFs concurrently
        tasks = [upload_and_analyze(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        # Verify all uploads succeeded and have unique IDs
        document_ids = [doc_id for doc_id, _ in results]
        assert len(set(document_ids)) == 5  # All IDs should be unique
        
        # Verify all analyses completed
        for _, analysis in results:
            assert "total_pages" in analysis
            assert "extracted_fields" in analysis
    
    @pytest.mark.asyncio
    async def test_pdf_processing_with_retry(
        self, async_client: AsyncClient, sample_pdf_path: Path
    ):
        """Test PDF processing with retry logic for transient failures."""
        # Upload PDF
        with open(sample_pdf_path, "rb") as f:
            files = {"file": ("test.pdf", f, "application/pdf")}
            upload_response = await async_client.post("/api/upload", files=files)
        
        document_id = upload_response.json()["document_id"]
        
        # Simulate retry logic for analysis
        max_retries = 3
        retry_delay = 0.5
        
        for attempt in range(max_retries):
            analysis_response = await async_client.post(
                f"/api/pdf/analyze/{document_id}"
            )
            
            if analysis_response.status_code == status.HTTP_200_OK:
                break
            
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))
        
        assert analysis_response.status_code == status.HTTP_200_OK
        analysis_data = analysis_response.json()
        assert "processing_time_ms" in analysis_data
    
    @pytest.mark.asyncio
    async def test_pdf_workflow_with_correlation_id(
        self, async_client: AsyncClient, sample_pdf_path: Path
    ):
        """Test that correlation IDs are properly propagated through workflow."""
        correlation_id = "test-correlation-123"
        headers = {"X-Correlation-ID": correlation_id}
        
        # Upload with correlation ID
        with open(sample_pdf_path, "rb") as f:
            files = {"file": ("test.pdf", f, "application/pdf")}
            upload_response = await async_client.post(
                "/api/upload", files=files, headers=headers
            )
        
        assert upload_response.headers.get("X-Correlation-ID") == correlation_id
        document_id = upload_response.json()["document_id"]
        
        # Analyze with same correlation ID
        analysis_response = await async_client.post(
            f"/api/pdf/analyze/{document_id}", headers=headers
        )
        assert analysis_response.headers.get("X-Correlation-ID") == correlation_id
        
        # Get metadata with same correlation ID
        metadata_response = await async_client.get(
            f"/api/pdf/metadata/{document_id}", headers=headers
        )
        assert metadata_response.headers.get("X-Correlation-ID") == correlation_id