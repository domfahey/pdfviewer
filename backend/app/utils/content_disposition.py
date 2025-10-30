"""RFC 6266 compliant Content-Disposition header parsing with RFC 5987 support.

This module provides secure parsing of Content-Disposition headers with:
- RFC 6266 compliance for Content-Disposition parsing
- RFC 5987/2231 support for internationalized filenames (filename*)
- Filename sanitization to prevent path traversal attacks
- Control character and illegal filesystem character filtering
"""

import os
import re
import unicodedata
from email.message import Message
from typing import Literal
from urllib.parse import unquote


def sanitize_filename(
    filename: str, fallback: str = "downloaded.pdf", max_length: int = 255
) -> str:
    """Sanitize a filename to prevent security vulnerabilities.

    This function performs comprehensive sanitization:
    1. Removes path components (os.path.basename)
    2. Rejects path traversal sequences (..)
    3. Filters control characters (0x00-0x1F, 0x7F)
    4. Removes illegal filesystem characters (<>:"/\\|?*)
    5. Normalizes Unicode (NFC normalization)
    6. Enforces maximum filename length
    7. Ensures .pdf extension

    Args:
        filename: The filename to sanitize
        fallback: Fallback filename if sanitization fails
        max_length: Maximum allowed filename length (default: 255)

    Returns:
        str: Sanitized filename, or fallback if input is invalid

    Examples:
        >>> sanitize_filename("document.pdf")
        'document.pdf'
        >>> sanitize_filename("../../etc/passwd")
        'downloaded.pdf'
        >>> sanitize_filename("file<>name.pdf")
        'filename.pdf'
        >>> sanitize_filename("file\\x00name.pdf")
        'filename.pdf'
    """
    if not filename or not isinstance(filename, str):
        return fallback

    # Step 1: Check for path traversal sequences BEFORE stripping path
    # This ensures we reject any input containing ".." or absolute paths
    if ".." in filename or filename.startswith(("/", "\\")):
        return fallback

    # Step 2: Remove any path components (security: prevent directory traversal)
    # Note: We check for ".." first, then use basename as defense-in-depth
    filename = os.path.basename(filename)

    # Step 3: Normalize Unicode to NFC form for consistency
    filename = unicodedata.normalize("NFC", filename)

    # Step 4: Remove control characters (0x00-0x1F and 0x7F)
    filename = "".join(char for char in filename if ord(char) > 31 and ord(char) != 127)

    # Step 5: Remove illegal filesystem characters
    # Windows: < > : " / \ | ? *
    # Unix: primarily /
    # We use a comprehensive set for cross-platform compatibility
    illegal_chars = r'<>:"/\\|?*'
    for char in illegal_chars:
        filename = filename.replace(char, "")

    # Step 6: Strip whitespace and dots from start/end (Windows compatibility)
    filename = filename.strip(" .")

    # Step 7: Validate result is not empty after sanitization
    if not filename:
        return fallback

    # Step 8: Ensure .pdf extension
    if not filename.lower().endswith(".pdf"):
        # If there's an existing extension, replace it; otherwise add .pdf
        name_without_ext = os.path.splitext(filename)[0]
        if name_without_ext:
            filename = f"{name_without_ext}.pdf"
        else:
            return fallback

    # Step 9: Enforce maximum length (leave room for UUID prefix if needed)
    if len(filename) > max_length:
        # Try to preserve extension while truncating
        name, ext = os.path.splitext(filename)
        if ext.lower() == ".pdf":
            max_name_length = max_length - len(ext)
            filename = f"{name[:max_name_length]}{ext}"
        else:
            filename = filename[:max_length]

    # Step 10: Final validation - ensure we still have a valid filename
    if len(filename) < 5:  # Minimum: "a.pdf"
        return fallback

    return filename


def parse_content_disposition(
    header_value: str, fallback: str = "downloaded.pdf"
) -> str:
    """Parse Content-Disposition header with RFC 6266 and RFC 5987 support.

    This function properly handles:
    - RFC 2231/5987 encoded filenames (filename*=UTF-8''...)
    - Regular filenames (filename="..." or filename=...)
    - Both quoted and unquoted values
    - Priority: filename* (extended) > filename (regular)

    The parsed filename is automatically sanitized using sanitize_filename().

    Args:
        header_value: The Content-Disposition header value
        fallback: Fallback filename if parsing fails

    Returns:
        str: Sanitized filename from the header, or fallback if parsing fails

    Examples:
        >>> parse_content_disposition('attachment; filename="document.pdf"')
        'document.pdf'
        >>> parse_content_disposition("attachment; filename*=UTF-8''document%20name.pdf")
        'document name.pdf'
        >>> parse_content_disposition('inline; filename="../../etc/passwd"')
        'downloaded.pdf'
    """
    if not header_value:
        return sanitize_filename(fallback)

    # Use email.message.Message for RFC 2231/5987 compliant parsing
    # This handles both filename and filename* parameters correctly
    msg = Message()
    msg["content-disposition"] = header_value

    # Try to get the filename from the parsed header
    # get_filename() handles RFC 2231 decoding automatically
    filename = msg.get_filename()

    if filename:
        # Sanitize the parsed filename
        return sanitize_filename(filename, fallback=fallback)

    # Fallback: Try manual parsing for edge cases
    # This handles some non-compliant servers
    filename = _parse_filename_fallback(header_value)
    if filename:
        return sanitize_filename(filename, fallback=fallback)

    return sanitize_filename(fallback)


def _parse_filename_fallback(header_value: str) -> str | None:
    """Fallback parser for non-compliant Content-Disposition headers.

    This is used when email.message.Message fails to parse the header.
    It handles common non-compliant formats seen in the wild.

    Args:
        header_value: The Content-Disposition header value

    Returns:
        str | None: Extracted filename or None if not found
    """
    # Try to find filename* (RFC 5987) first
    # Format: filename*=charset'language'encoded-value
    # Example: filename*=UTF-8''document%20name.pdf
    match = re.search(
        r"filename\*=(?:UTF-8|utf-8)?''([^;\s]+)", header_value, re.IGNORECASE
    )
    if match:
        encoded_filename = match.group(1)
        try:
            # Decode URL encoding
            return unquote(encoded_filename)
        except Exception:
            pass

    # Try to find regular filename parameter
    # Format: filename="value" or filename=value
    match = re.search(r'filename="?([^";\s]+)"?', header_value, re.IGNORECASE)
    if match:
        return match.group(1)

    return None


def extract_filename_from_url(url: str, fallback: str = "downloaded.pdf") -> str:
    """Extract and sanitize filename from URL path.

    Args:
        url: The URL to extract filename from
        fallback: Fallback filename if extraction fails

    Returns:
        str: Sanitized filename from URL, or fallback if extraction fails

    Examples:
        >>> extract_filename_from_url("https://example.com/path/document.pdf")
        'document.pdf'
        >>> extract_filename_from_url("https://example.com/path/")
        'downloaded.pdf'
    """
    if not url:
        return sanitize_filename(fallback)

    # Extract the last path component
    url_parts = url.rstrip("/").split("/")
    if url_parts:
        potential_filename = url_parts[-1]
        # Only use it if it looks like a PDF filename
        if potential_filename and potential_filename.lower().endswith(".pdf"):
            return sanitize_filename(potential_filename, fallback=fallback)

    return sanitize_filename(fallback)
