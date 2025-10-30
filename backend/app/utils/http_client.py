"""HTTP client utilities for making requests with retry logic."""

import asyncio
from typing import Any

import httpx
from fastapi import HTTPException


async def fetch_with_retry(
    url: str,
    max_retries: int = 3,
    timeout: float = 60.0,
    connect_timeout: float = 10.0,
    **kwargs: Any,
) -> httpx.Response:
    """Fetch a URL with automatic retry on transient failures.
    
    Implements exponential backoff for retries on network errors and timeouts.
    
    Args:
        url: URL to fetch
        max_retries: Maximum number of retry attempts (default: 3)
        timeout: Request timeout in seconds (default: 60.0)
        connect_timeout: Connection timeout in seconds (default: 10.0)
        **kwargs: Additional arguments to pass to httpx.AsyncClient.get()
        
    Returns:
        httpx.Response: The successful response
        
    Raises:
        HTTPException: If request fails after all retries
        
    Example:
        >>> response = await fetch_with_retry("https://example.com/file.pdf")
        >>> content = response.content
    """
    timeout_config = httpx.Timeout(timeout, connect=connect_timeout)
    limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
    
    async with httpx.AsyncClient(
        timeout=timeout_config, limits=limits, follow_redirects=True
    ) as client:
        response = None
        
        for attempt in range(max_retries):
            try:
                response = await client.get(url, **kwargs)
                response.raise_for_status()
                return response
                
            except (httpx.TimeoutException, httpx.NetworkError) as network_error:
                if attempt < max_retries - 1:
                    # Exponential backoff: 1s, 2s, 4s, ...
                    await asyncio.sleep(2**attempt)
                    continue
                raise HTTPException(
                    status_code=504,
                    detail=f"Timeout downloading from URL after {max_retries} attempts: {str(network_error)}",
                )
            except httpx.HTTPStatusError as http_status_error:
                raise HTTPException(
                    status_code=502,
                    detail=f"Failed to download from URL: {http_status_error.response.status_code}",
                )
        
        # Should not reach here, but handle edge case
        raise HTTPException(
            status_code=502,
            detail="Failed to download from URL after all retries",
        )
