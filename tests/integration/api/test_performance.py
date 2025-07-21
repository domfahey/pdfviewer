"""
Performance and load tests for PDF processing.
"""

import asyncio
import time
from pathlib import Path
from statistics import mean, stdev

import pytest
from fastapi import status
from httpx import AsyncClient


class TestPerformance:
    """Test performance characteristics of PDF processing."""

    @pytest.mark.asyncio
    async def test_upload_response_time(
        self, async_client: AsyncClient, sample_pdf_path: Path
    ):
        """Test that PDF upload completes within acceptable time."""
        response_times = []

        for _ in range(5):
            start_time = time.time()

            with open(sample_pdf_path, "rb") as f:
                files = {"file": ("test.pdf", f, "application/pdf")}
                response = await async_client.post("/api/upload", files=files)

            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to ms

            assert response.status_code == status.HTTP_200_OK
            response_times.append(response_time)

        avg_response_time = mean(response_times)

        # Upload should complete within 500ms on average
        assert (
            avg_response_time < 500
        ), f"Average upload time {avg_response_time}ms exceeds 500ms"

        # Log performance metrics
        if len(response_times) > 1:
            std_dev = stdev(response_times)
            print("\nUpload Performance:")
            print(f"  Average: {avg_response_time:.2f}ms")
            print(f"  Std Dev: {std_dev:.2f}ms")
            print(f"  Min: {min(response_times):.2f}ms")
            print(f"  Max: {max(response_times):.2f}ms")

    @pytest.mark.asyncio
    async def test_concurrent_upload_performance(
        self, async_client: AsyncClient, sample_pdf_path: Path
    ):
        """Test system performance under concurrent uploads."""
        concurrent_uploads = 10

        async def timed_upload(index: int):
            """Upload with timing."""
            start_time = time.time()

            with open(sample_pdf_path, "rb") as f:
                files = {"file": (f"test_{index}.pdf", f, "application/pdf")}
                response = await async_client.post("/api/upload", files=files)

            end_time = time.time()
            return {
                "status": response.status_code,
                "time_ms": (end_time - start_time) * 1000,
                "document_id": (
                    response.json().get("document_id")
                    if response.status_code == 200
                    else None
                ),
            }

        # Execute concurrent uploads
        start_time = time.time()
        tasks = [timed_upload(i) for i in range(concurrent_uploads)]
        results = await asyncio.gather(*tasks)
        total_time = (time.time() - start_time) * 1000

        # Verify all uploads succeeded
        successful_uploads = [r for r in results if r["status"] == status.HTTP_200_OK]
        assert len(successful_uploads) == concurrent_uploads

        # Calculate performance metrics
        response_times = [r["time_ms"] for r in results]
        avg_response_time = mean(response_times)

        print(f"\nConcurrent Upload Performance ({concurrent_uploads} uploads):")
        print(f"  Total Time: {total_time:.2f}ms")
        print(f"  Average Response Time: {avg_response_time:.2f}ms")
        print(
            f"  Throughput: {concurrent_uploads / (total_time / 1000):.2f} uploads/sec"
        )

        # Concurrent uploads should not significantly degrade performance
        # Average response time should be less than 2x single upload time
        assert avg_response_time < 1000

    @pytest.mark.asyncio
    async def test_page_rendering_performance(
        self, async_client: AsyncClient, sample_pdf_path: Path
    ):
        """Test page rendering performance."""
        # Upload PDF
        with open(sample_pdf_path, "rb") as f:
            files = {"file": ("test.pdf", f, "application/pdf")}
            upload_response = await async_client.post("/api/upload", files=files)

        document_id = upload_response.json()["document_id"]

        # Get metadata to know page count
        metadata_response = await async_client.get(f"/api/pdf/metadata/{document_id}")
        page_count = metadata_response.json()["page_count"]

        # Test rendering first 5 pages (or all if less)
        pages_to_test = min(5, page_count)
        render_times = []

        for page_num in range(1, pages_to_test + 1):
            start_time = time.time()

            response = await async_client.get(f"/api/pdf/page/{document_id}/{page_num}")

            end_time = time.time()
            render_time = (end_time - start_time) * 1000

            assert response.status_code == status.HTTP_200_OK
            assert response.headers["content-type"] == "image/png"
            render_times.append(render_time)

        avg_render_time = mean(render_times)

        print("\nPage Rendering Performance:")
        print(f"  Average: {avg_render_time:.2f}ms")
        print(f"  First Page: {render_times[0]:.2f}ms")

        # Page rendering should complete within 1 second on average
        assert avg_render_time < 1000

        # First page might be slower due to PDF loading
        # Subsequent pages should be faster
        if len(render_times) > 1:
            subsequent_avg = mean(render_times[1:])
            print(f"  Subsequent Pages Avg: {subsequent_avg:.2f}ms")

    @pytest.mark.asyncio
    async def test_analysis_performance_scaling(
        self, async_client: AsyncClient, sample_pdf_path: Path
    ):
        """Test how analysis performance scales with document complexity."""
        # Upload same PDF multiple times to test analysis
        document_ids = []

        for i in range(3):
            with open(sample_pdf_path, "rb") as f:
                files = {"file": (f"test_{i}.pdf", f, "application/pdf")}
                upload_response = await async_client.post("/api/upload", files=files)
            document_ids.append(upload_response.json()["document_id"])

        # Analyze each PDF and measure time
        analysis_times = []

        for doc_id in document_ids:
            start_time = time.time()

            response = await async_client.post(f"/api/pdf/analyze/{doc_id}")

            end_time = time.time()
            analysis_time = (end_time - start_time) * 1000

            assert response.status_code == status.HTTP_200_OK
            analysis_times.append(analysis_time)

            # Check if processing time is reported
            if "processing_time_ms" in response.json():
                reported_time = response.json()["processing_time_ms"]
                print(f"\n  Reported processing time: {reported_time}ms")
                print(f"  Actual API response time: {analysis_time:.2f}ms")

        avg_analysis_time = mean(analysis_times)

        print("\nAnalysis Performance:")
        print(f"  Average: {avg_analysis_time:.2f}ms")

        # Analysis should complete within 5 seconds
        assert avg_analysis_time < 5000

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires large PDF fixture")
    async def test_large_pdf_handling(
        self, async_client: AsyncClient, large_pdf_path: Path
    ):
        """Test handling of large PDF files."""
        if not large_pdf_path.exists():
            pytest.skip("Large PDF fixture not available")

        # Upload large PDF
        start_time = time.time()

        with open(large_pdf_path, "rb") as f:
            files = {"file": ("large.pdf", f, "application/pdf")}
            response = await async_client.post("/api/upload", files=files)

        upload_time = (time.time() - start_time) * 1000

        assert response.status_code == status.HTTP_200_OK
        document_id = response.json()["document_id"]

        print("\nLarge PDF Upload Performance:")
        print(f"  File Size: {large_pdf_path.stat().st_size / (1024 * 1024):.2f}MB")
        print(f"  Upload Time: {upload_time:.2f}ms")

        # Test page rendering for large PDF
        page_response = await async_client.get(f"/api/pdf/page/{document_id}/1")
        assert page_response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_memory_efficiency(
        self, async_client: AsyncClient, sample_pdf_path: Path
    ):
        """Test that repeated operations don't cause memory leaks."""
        # This is a basic test - real memory profiling would require additional tools

        # Perform multiple upload/delete cycles
        for cycle in range(10):
            # Upload
            with open(sample_pdf_path, "rb") as f:
                files = {"file": (f"test_cycle_{cycle}.pdf", f, "application/pdf")}
                upload_response = await async_client.post("/api/upload", files=files)

            assert upload_response.status_code == status.HTTP_200_OK
            document_id = upload_response.json()["document_id"]

            # Get a page (forces PDF loading)
            page_response = await async_client.get(f"/api/pdf/page/{document_id}/1")
            assert page_response.status_code == status.HTTP_200_OK

            # Delete
            delete_response = await async_client.delete(f"/api/pdf/{document_id}")
            assert delete_response.status_code == status.HTTP_200_OK

        # If we get here without crashing, basic memory management is working
        print("\nMemory efficiency test completed 10 upload/render/delete cycles")
