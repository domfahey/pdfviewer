"""
Integration tests for error handling and edge cases.
"""
import io
from pathlib import Path

import pytest
from fastapi import status
from httpx import AsyncClient


class TestErrorHandling:
    """Test error handling and edge cases in PDF processing."""
    
    @pytest.mark.asyncio
    async def test_upload_invalid_file_type(self, async_client: AsyncClient):
        """Test uploading non-PDF file."""
        # Create a text file
        text_content = b"This is not a PDF file"
        files = {"file": ("test.txt", io.BytesIO(text_content), "text/plain")}
        
        response = await async_client.post("/api/upload", files=files)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid file type" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_upload_empty_file(self, async_client: AsyncClient):
        """Test uploading empty file."""
        files = {"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")}
        
        response = await async_client.post("/api/upload", files=files)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "empty" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_upload_oversized_file(self, async_client: AsyncClient):
        """Test uploading file exceeding size limit."""
        # Create a large dummy PDF (51MB - over the 50MB limit)
        large_content = b"%PDF-1.4\n" + b"0" * (51 * 1024 * 1024)
        files = {"file": ("large.pdf", io.BytesIO(large_content), "application/pdf")}
        
        response = await async_client.post("/api/upload", files=files)
        assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    
    @pytest.mark.asyncio
    async def test_analyze_nonexistent_pdf(self, async_client: AsyncClient):
        """Test analyzing PDF that doesn't exist."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        response = await async_client.post(f"/api/pdf/analyze/{fake_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_get_page_invalid_number(
        self, async_client: AsyncClient, sample_pdf_path: Path
    ):
        """Test requesting invalid page number."""
        # First upload a PDF
        with open(sample_pdf_path, "rb") as f:
            files = {"file": ("test.pdf", f, "application/pdf")}
            upload_response = await async_client.post("/api/upload", files=files)
        
        document_id = upload_response.json()["document_id"]
        
        # Request page 0 (invalid)
        response = await async_client.get(f"/api/pdf/page/{document_id}/0")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Request page 999 (out of range)
        response = await async_client.get(f"/api/pdf/page/{document_id}/999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Page not found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_corrupt_pdf_handling(
        self, async_client: AsyncClient, corrupt_pdf_path: Path
    ):
        """Test handling of corrupt PDF files."""
        # Skip if corrupt PDF doesn't exist
        if not corrupt_pdf_path.exists():
            pytest.skip("Corrupt PDF fixture not available")
        
        # Upload corrupt PDF
        with open(corrupt_pdf_path, "rb") as f:
            files = {"file": ("corrupt.pdf", f, "application/pdf")}
            upload_response = await async_client.post("/api/upload", files=files)
        
        if upload_response.status_code == status.HTTP_200_OK:
            document_id = upload_response.json()["document_id"]
            
            # Try to analyze corrupt PDF
            analysis_response = await async_client.post(
                f"/api/pdf/analyze/{document_id}"
            )
            
            # Should either fail gracefully or return partial results
            if analysis_response.status_code != status.HTTP_200_OK:
                assert analysis_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
                assert "corrupt" in analysis_response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_malformed_uuid(self, async_client: AsyncClient):
        """Test endpoints with malformed UUID."""
        malformed_ids = [
            "not-a-uuid",
            "12345",
            "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
            "g0000000-0000-0000-0000-000000000000",  # Invalid hex
        ]
        
        for bad_id in malformed_ids:
            # Test various endpoints
            response = await async_client.get(f"/api/pdf/metadata/{bad_id}")
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            
            response = await async_client.post(f"/api/pdf/analyze/{bad_id}")
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.asyncio
    async def test_concurrent_delete_handling(
        self, async_client: AsyncClient, sample_pdf_path: Path
    ):
        """Test handling concurrent delete requests."""
        import asyncio
        
        # Upload PDF
        with open(sample_pdf_path, "rb") as f:
            files = {"file": ("test.pdf", f, "application/pdf")}
            upload_response = await async_client.post("/api/upload", files=files)
        
        document_id = upload_response.json()["document_id"]
        
        # Try to delete the same PDF concurrently
        async def delete_pdf():
            return await async_client.delete(f"/api/pdf/{document_id}")
        
        # Execute multiple delete requests concurrently
        delete_tasks = [delete_pdf() for _ in range(3)]
        responses = await asyncio.gather(*delete_tasks, return_exceptions=True)
        
        # Only one should succeed, others should get 404
        success_count = sum(
            1 for r in responses 
            if not isinstance(r, Exception) and r.status_code == status.HTTP_200_OK
        )
        not_found_count = sum(
            1 for r in responses 
            if not isinstance(r, Exception) and r.status_code == status.HTTP_404_NOT_FOUND
        )
        
        assert success_count == 1
        assert not_found_count == 2
    
    @pytest.mark.asyncio
    async def test_special_characters_in_filename(self, async_client: AsyncClient):
        """Test handling filenames with special characters."""
        # Create a simple PDF content
        pdf_content = b"%PDF-1.4\n%EOF"
        
        special_filenames = [
            "test with spaces.pdf",
            "test_@#$%.pdf",
            "test(1).pdf",
            "тест.pdf",  # Cyrillic
            "测试.pdf",   # Chinese
            "test&file.pdf",
            "test;file.pdf",
        ]
        
        for filename in special_filenames:
            files = {"file": (filename, io.BytesIO(pdf_content), "application/pdf")}
            response = await async_client.post("/api/upload", files=files)
            
            # Should handle special characters gracefully
            assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]
            
            if response.status_code == status.HTTP_200_OK:
                # Verify the filename is properly stored
                document_id = response.json()["document_id"]
                metadata_response = await async_client.get(
                    f"/api/pdf/metadata/{document_id}"
                )
                assert metadata_response.status_code == status.HTTP_200_OK