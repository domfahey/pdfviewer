"""Tests for HTTP client utilities."""

import pytest
from unittest.mock import AsyncMock, Mock, patch

import httpx
from fastapi import HTTPException

from backend.app.utils.http_client import fetch_with_retry


class TestFetchWithRetry:
    """Test fetch_with_retry function."""

    @pytest.mark.asyncio
    async def test_fetch_with_retry_success(self):
        """Test successful fetch on first attempt."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"test content"
        mock_response.raise_for_status = Mock()

        with patch("backend.app.utils.http_client.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            response = await fetch_with_retry("https://example.com/test.pdf")

            assert response.status_code == 200
            assert response.content == b"test content"

    @pytest.mark.asyncio
    async def test_fetch_with_retry_timeout_with_retry(self):
        """Test retry on timeout."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"test content"
        mock_response.raise_for_status = Mock()

        with patch("backend.app.utils.http_client.httpx.AsyncClient") as mock_client:
            mock_get = AsyncMock()
            # First call raises timeout, second succeeds
            mock_get.side_effect = [
                httpx.TimeoutException("Timeout"),
                mock_response,
            ]
            mock_client.return_value.__aenter__.return_value.get = mock_get

            with patch("backend.app.utils.http_client.asyncio.sleep", new_callable=AsyncMock):
                response = await fetch_with_retry("https://example.com/test.pdf")

            assert response.status_code == 200
            assert mock_get.call_count == 2  # First failed, second succeeded

    @pytest.mark.asyncio
    async def test_fetch_with_retry_max_retries_exceeded(self):
        """Test max retries exceeded."""
        with patch("backend.app.utils.http_client.httpx.AsyncClient") as mock_client:
            mock_get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            mock_client.return_value.__aenter__.return_value.get = mock_get

            with patch("backend.app.utils.http_client.asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(HTTPException) as exc_info:
                    await fetch_with_retry("https://example.com/test.pdf", max_retries=3)

            assert exc_info.value.status_code == 504
            assert "Timeout" in exc_info.value.detail
            assert mock_get.call_count == 3

    @pytest.mark.asyncio
    async def test_fetch_with_retry_http_status_error(self):
        """Test HTTP status error (404, 500, etc.)."""
        mock_response = Mock()
        mock_response.status_code = 404

        with patch("backend.app.utils.http_client.httpx.AsyncClient") as mock_client:
            mock_get = AsyncMock()
            mock_get.return_value.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Not found", request=Mock(), response=mock_response
            )
            mock_client.return_value.__aenter__.return_value.get = mock_get

            with pytest.raises(HTTPException) as exc_info:
                await fetch_with_retry("https://example.com/test.pdf")

            assert exc_info.value.status_code == 502
            assert "404" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_fetch_with_retry_network_error(self):
        """Test network error."""
        with patch("backend.app.utils.http_client.httpx.AsyncClient") as mock_client:
            mock_get = AsyncMock(side_effect=httpx.NetworkError("Connection failed"))
            mock_client.return_value.__aenter__.return_value.get = mock_get

            with patch("backend.app.utils.http_client.asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(HTTPException) as exc_info:
                    await fetch_with_retry("https://example.com/test.pdf", max_retries=2)

            assert exc_info.value.status_code == 504
            assert "Connection failed" in exc_info.value.detail
            assert mock_get.call_count == 2

    @pytest.mark.asyncio
    async def test_fetch_with_retry_custom_params(self):
        """Test with custom timeout and retry parameters."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"test content"
        mock_response.raise_for_status = Mock()

        with patch("backend.app.utils.http_client.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            response = await fetch_with_retry(
                "https://example.com/test.pdf",
                max_retries=5,
                timeout=120.0,
                connect_timeout=20.0,
            )

            assert response.status_code == 200
            # Verify AsyncClient was called with custom timeouts
            call_kwargs = mock_client.call_args[1]
            assert call_kwargs["timeout"].read == 120.0
            assert call_kwargs["timeout"].connect == 20.0
