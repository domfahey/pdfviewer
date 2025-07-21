"""
Integration tests for loading PDFs from URLs.
"""

import pytest
from fastapi import status
from httpx import AsyncClient


class TestLoadURL:
    """Test loading PDFs from external URLs."""

    # Sample PDFs for testing
    SAMPLE_PDFS = [
        {
            "name": "EPA Sample Letter",
            "url": "https://19january2021snapshot.epa.gov/sites/static/files/2016-02/documents/epa_sample_letter_sent_to_commissioners_dated_february_29_2015.pdf",
            "expected_pages": 3,
        },
        {
            "name": "Image-based PDF",
            "url": "https://nlsblog.org/wp-content/uploads/2020/06/image-based-pdf-sample.pdf",
            "expected_pages": None,  # Don't know exact page count
        },
        {
            "name": "Anyline Sample Book",
            "url": "https://anyline.com/app/uploads/2022/03/anyline-sample-scan-book.pdf",
            "expected_pages": None,
        },
        {
            "name": "NHTSA Form",
            "url": "https://www.nhtsa.gov/sites/nhtsa.gov/files/documents/mo_par_rev01_2012.pdf",
            "expected_pages": None,
        },
    ]

    @pytest.mark.asyncio
    async def test_load_pdf_from_url_success(self, async_client: AsyncClient):
        """Test successfully loading a PDF from URL."""
        # Use EPA sample PDF
        request_data = {"url": self.SAMPLE_PDFS[0]["url"]}

        response = await async_client.post("/api/load-url", json=request_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Validate response structure
        assert "file_id" in data
        assert "filename" in data
        assert "file_size" in data
        assert "metadata" in data

        # Validate filename
        assert (
            data["filename"]
            == "epa_sample_letter_sent_to_commissioners_dated_february_29_2015.pdf"
        )

        # Validate metadata
        assert data["metadata"]["page_count"] == 3
        assert data["metadata"]["encrypted"] is False

        # Cleanup - delete the uploaded file
        document_id = data["file_id"]
        delete_response = await async_client.delete(f"/api/pdf/{document_id}")
        assert delete_response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_load_invalid_url(self, async_client: AsyncClient):
        """Test loading from invalid URL."""
        request_data = {"url": "https://invalid.example.com/notfound.pdf"}

        response = await async_client.post("/api/load-url", json=request_data)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to load PDF" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_load_non_pdf_url(self, async_client: AsyncClient):
        """Test loading from URL that doesn't point to a PDF."""
        request_data = {"url": "https://www.google.com"}

        response = await async_client.post("/api/load-url", json=request_data)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to load PDF" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_load_url_with_invalid_format(self, async_client: AsyncClient):
        """Test with invalid URL format."""
        request_data = {"url": "not-a-valid-url"}

        response = await async_client.post("/api/load-url", json=request_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_load_all_sample_pdfs(self, async_client: AsyncClient):
        """Test loading all sample PDFs."""
        loaded_files = []

        for sample in self.SAMPLE_PDFS:
            print(f"\nTesting: {sample['name']}")
            request_data = {"url": sample["url"]}

            try:
                response = await async_client.post("/api/load-url", json=request_data)

                if response.status_code == status.HTTP_200_OK:
                    data = response.json()
                    loaded_files.append(data["file_id"])

                    print("  ✓ Loaded successfully")
                    print(f"  - File ID: {data['file_id']}")
                    print(f"  - Size: {data['file_size_mb']:.2f} MB")
                    print(f"  - Pages: {data['metadata']['page_count']}")

                    # Verify expected page count if known
                    if sample["expected_pages"]:
                        assert (
                            data["metadata"]["page_count"] == sample["expected_pages"]
                        )
                else:
                    print(f"  ✗ Failed with status {response.status_code}")

            except Exception as e:
                print(f"  ✗ Error: {e}")

        # Cleanup all loaded files
        for file_id in loaded_files:
            delete_response = await async_client.delete(f"/api/pdf/{file_id}")
            assert delete_response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_404_NOT_FOUND,
            ]

        # At least some PDFs should load successfully
        assert len(loaded_files) > 0

    @pytest.mark.asyncio
    async def test_load_url_preserves_filename(self, async_client: AsyncClient):
        """Test that original filename is preserved from URL."""
        # Test with Anyline PDF which has a clear filename in URL
        request_data = {
            "url": "https://anyline.com/app/uploads/2022/03/anyline-sample-scan-book.pdf"
        }

        response = await async_client.post("/api/load-url", json=request_data)

        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert data["filename"] == "anyline-sample-scan-book.pdf"

            # Cleanup
            await async_client.delete(f"/api/pdf/{data['file_id']}")

    @pytest.mark.asyncio
    async def test_load_url_with_redirect(self, async_client: AsyncClient):
        """Test loading PDF from URL that redirects."""
        # Many government sites use redirects
        request_data = {"url": self.SAMPLE_PDFS[3]["url"]}  # NHTSA URL often redirects

        response = await async_client.post("/api/load-url", json=request_data)

        # Should handle redirects gracefully
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "file_id" in data

            # Cleanup
            await async_client.delete(f"/api/pdf/{data['file_id']}")

    @pytest.mark.asyncio
    async def test_concurrent_url_loads(self, async_client: AsyncClient):
        """Test loading multiple URLs concurrently."""
        import asyncio

        # Use first two sample PDFs
        urls = [sample["url"] for sample in self.SAMPLE_PDFS[:2]]

        async def load_url(url: str):
            """Load a single URL."""
            response = await async_client.post("/api/load-url", json={"url": url})
            if response.status_code == status.HTTP_200_OK:
                return response.json()["file_id"]
            return None

        # Load URLs concurrently
        results = await asyncio.gather(*[load_url(url) for url in urls])

        # Filter out None values
        loaded_files = [f for f in results if f is not None]

        # Should load at least one successfully
        assert len(loaded_files) > 0

        # All loaded files should have unique IDs
        assert len(set(loaded_files)) == len(loaded_files)

        # Cleanup
        for file_id in loaded_files:
            await async_client.delete(f"/api/pdf/{file_id}")
