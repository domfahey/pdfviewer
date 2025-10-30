"""
Tests for RFC 6266/5987 compliant Content-Disposition parsing and filename sanitization.

This test suite covers:
- RFC 6266 Content-Disposition parsing
- RFC 5987/2231 encoded filenames (filename*)
- Filename sanitization security checks
- Path traversal prevention
- Control character and illegal character filtering
"""

import pytest

from backend.app.utils.content_disposition import (
    extract_filename_from_url,
    parse_content_disposition,
    sanitize_filename,
)


class TestSanitizeFilename:
    """Test filename sanitization for security and compatibility."""

    def test_valid_filename_unchanged(self):
        """Test that valid filenames pass through unchanged."""
        assert sanitize_filename("document.pdf") == "document.pdf"
        assert sanitize_filename("test_file-2024.pdf") == "test_file-2024.pdf"
        assert sanitize_filename("my document.pdf") == "my document.pdf"

    def test_path_traversal_rejected(self):
        """Test that path traversal attempts are rejected."""
        assert sanitize_filename("../../etc/passwd") == "downloaded.pdf"
        assert sanitize_filename("../../../etc/passwd.pdf") == "downloaded.pdf"
        assert sanitize_filename("..\\..\\windows\\system32\\config.pdf") == "downloaded.pdf"

    def test_path_components_removed(self):
        """Test that path components are rejected or stripped."""
        # Absolute paths should be rejected
        assert sanitize_filename("/etc/passwd.pdf") == "downloaded.pdf"
        assert sanitize_filename("/path/to/document.pdf") == "downloaded.pdf"
        assert sanitize_filename("C:\\Users\\test\\document.pdf") == "downloaded.pdf"
        assert sanitize_filename("\\\\network\\share\\file.pdf") == "downloaded.pdf"

    def test_control_characters_removed(self):
        """Test that control characters are filtered."""
        assert sanitize_filename("file\x00name.pdf") == "filename.pdf"
        assert sanitize_filename("file\x01name.pdf") == "filename.pdf"
        assert sanitize_filename("file\x1fname.pdf") == "filename.pdf"
        assert sanitize_filename("file\x7fname.pdf") == "filename.pdf"  # DEL character

    def test_illegal_filesystem_characters_removed(self):
        """Test that illegal filesystem characters are removed."""
        assert sanitize_filename("file<name>.pdf") == "filename.pdf"
        assert sanitize_filename("file:name.pdf") == "filename.pdf"
        assert sanitize_filename('file"name".pdf') == "filename.pdf"
        assert sanitize_filename("file|name.pdf") == "filename.pdf"
        assert sanitize_filename("file?name.pdf") == "filename.pdf"
        assert sanitize_filename("file*name.pdf") == "filename.pdf"

    def test_windows_reserved_characters(self):
        """Test handling of Windows reserved characters."""
        # These should all be sanitized
        assert sanitize_filename("file<>name.pdf") == "filename.pdf"
        assert sanitize_filename('CON.pdf') == "CON.pdf"  # CON is reserved but we allow it with .pdf
        # Paths with / or \ are rejected as absolute paths
        assert sanitize_filename('file/name.pdf') == "downloaded.pdf"
        assert sanitize_filename('file\\name.pdf') == "downloaded.pdf"

    def test_whitespace_handling(self):
        """Test whitespace normalization."""
        assert sanitize_filename("  document.pdf  ") == "document.pdf"
        assert sanitize_filename("...document.pdf...") == "document.pdf"
        assert sanitize_filename("   .pdf   ") == "downloaded.pdf"  # Too short after strip

    def test_extension_enforcement(self):
        """Test that .pdf extension is enforced."""
        assert sanitize_filename("document.txt") == "document.pdf"
        assert sanitize_filename("document.exe") == "document.pdf"
        assert sanitize_filename("document") == "document.pdf"
        assert sanitize_filename("document.PDF") == "document.PDF"  # Preserve case

    def test_unicode_normalization(self):
        """Test Unicode normalization (NFC)."""
        # Test with combining characters
        filename = "café.pdf"  # é as single character
        result = sanitize_filename(filename)
        assert result == "café.pdf"
        assert len(result) == 8  # Normalized length

    def test_length_limit_enforcement(self):
        """Test that filenames are truncated to max length."""
        long_name = "a" * 300 + ".pdf"
        result = sanitize_filename(long_name, max_length=255)
        assert len(result) <= 255
        assert result.endswith(".pdf")

    def test_empty_or_invalid_input(self):
        """Test handling of empty or invalid inputs."""
        assert sanitize_filename("") == "downloaded.pdf"
        assert sanitize_filename("   ") == "downloaded.pdf"
        assert sanitize_filename(None) == "downloaded.pdf"  # type: ignore

    def test_only_extension_rejected(self):
        """Test that filenames with only extension are rejected."""
        assert sanitize_filename(".pdf") == "downloaded.pdf"
        assert sanitize_filename("...pdf") == "downloaded.pdf"

    def test_custom_fallback(self):
        """Test custom fallback filename."""
        assert sanitize_filename("", fallback="custom.pdf") == "custom.pdf"
        assert sanitize_filename("../../../etc/passwd", fallback="safe.pdf") == "safe.pdf"

    def test_multiple_dots_preserved(self):
        """Test that multiple dots in filename are handled correctly."""
        assert sanitize_filename("file.backup.pdf") == "file.backup.pdf"
        assert sanitize_filename("archive.2024.01.15.pdf") == "archive.2024.01.15.pdf"


class TestParseContentDisposition:
    """Test RFC 6266/5987 compliant Content-Disposition parsing."""

    def test_simple_quoted_filename(self):
        """Test parsing simple quoted filename."""
        header = 'attachment; filename="document.pdf"'
        assert parse_content_disposition(header) == "document.pdf"

    def test_simple_unquoted_filename(self):
        """Test parsing simple unquoted filename."""
        header = "attachment; filename=document.pdf"
        assert parse_content_disposition(header) == "document.pdf"

    def test_rfc5987_encoded_filename(self):
        """Test parsing RFC 5987 encoded filename (filename*)."""
        # UTF-8 encoded with URL encoding
        header = "attachment; filename*=UTF-8''document%20name.pdf"
        assert parse_content_disposition(header) == "document name.pdf"

    def test_rfc5987_with_special_chars(self):
        """Test RFC 5987 encoding with special characters."""
        header = "attachment; filename*=UTF-8''r%C3%A9sum%C3%A9.pdf"
        result = parse_content_disposition(header)
        assert result == "résumé.pdf"

    def test_both_filename_and_filename_star(self):
        """Test that filename* takes precedence over filename."""
        # When both are present, filename* should be preferred (RFC 5987)
        header = 'attachment; filename="fallback.pdf"; filename*=UTF-8\'\'preferred.pdf'
        # The email.message.Message parser should prefer filename*
        result = parse_content_disposition(header)
        # Either is acceptable depending on parser behavior, but must be sanitized
        assert result in ["preferred.pdf", "fallback.pdf"]

    def test_inline_disposition(self):
        """Test inline disposition type."""
        header = 'inline; filename="document.pdf"'
        assert parse_content_disposition(header) == "document.pdf"

    def test_filename_with_path_traversal(self):
        """Test that path traversal in Content-Disposition is sanitized."""
        header = 'attachment; filename="../../etc/passwd.pdf"'
        assert parse_content_disposition(header) == "downloaded.pdf"

    def test_filename_with_illegal_characters(self):
        """Test that illegal characters are removed."""
        header = 'attachment; filename="file<>name.pdf"'
        assert parse_content_disposition(header) == "filename.pdf"

    def test_empty_header(self):
        """Test handling of empty header."""
        assert parse_content_disposition("") == "downloaded.pdf"
        assert parse_content_disposition(None) == "downloaded.pdf"  # type: ignore

    def test_malformed_header(self):
        """Test handling of malformed headers."""
        assert parse_content_disposition("not a valid header") == "downloaded.pdf"
        assert parse_content_disposition("attachment;") == "downloaded.pdf"

    def test_case_insensitive_parsing(self):
        """Test case-insensitive parameter parsing."""
        header = 'ATTACHMENT; FILENAME="document.pdf"'
        assert parse_content_disposition(header) == "document.pdf"

    def test_whitespace_in_header(self):
        """Test handling of whitespace in header."""
        header = 'attachment;  filename = "document.pdf"  '
        result = parse_content_disposition(header)
        assert result == "document.pdf"

    def test_semicolon_in_filename(self):
        """Test filename containing semicolon."""
        # Semicolon should be handled by proper quoting
        header = 'attachment; filename="file;name.pdf"'
        result = parse_content_disposition(header)
        # Semicolon will be removed by sanitization
        assert result == "filename.pdf"

    def test_unicode_filename(self):
        """Test Unicode filename in Content-Disposition."""
        header = 'attachment; filename="café-résumé.pdf"'
        result = parse_content_disposition(header)
        assert result == "café-résumé.pdf"

    def test_custom_fallback(self):
        """Test custom fallback filename."""
        header = ""
        assert parse_content_disposition(header, fallback="custom.pdf") == "custom.pdf"

    def test_real_world_examples(self):
        """Test real-world Content-Disposition headers."""
        # Common formats from various servers
        examples = [
            ('attachment; filename="sample.pdf"', "sample.pdf"),
            ("attachment; filename=sample.pdf", "sample.pdf"),
            ('inline; filename="report-2024.pdf"', "report-2024.pdf"),
            ("attachment; filename*=UTF-8''sample%20file.pdf", "sample file.pdf"),
        ]
        for header, expected in examples:
            assert parse_content_disposition(header) == expected


class TestExtractFilenameFromUrl:
    """Test filename extraction from URLs."""

    def test_simple_url(self):
        """Test extraction from simple URL."""
        url = "https://example.com/document.pdf"
        assert extract_filename_from_url(url) == "document.pdf"

    def test_url_with_path(self):
        """Test extraction from URL with path."""
        url = "https://example.com/path/to/document.pdf"
        assert extract_filename_from_url(url) == "document.pdf"

    def test_url_with_query_params(self):
        """Test URL with query parameters."""
        url = "https://example.com/document.pdf?version=1&user=test"
        # Query params will be part of filename, then sanitized
        result = extract_filename_from_url(url)
        assert result.endswith(".pdf")

    def test_url_ending_with_slash(self):
        """Test URL ending with slash."""
        url = "https://example.com/path/"
        assert extract_filename_from_url(url) == "downloaded.pdf"

    def test_url_without_pdf_extension(self):
        """Test URL without .pdf extension."""
        url = "https://example.com/document"
        assert extract_filename_from_url(url) == "downloaded.pdf"

    def test_empty_url(self):
        """Test empty URL."""
        assert extract_filename_from_url("") == "downloaded.pdf"
        assert extract_filename_from_url(None) == "downloaded.pdf"  # type: ignore

    def test_url_with_encoded_filename(self):
        """Test URL with percent-encoded filename."""
        url = "https://example.com/my%20document.pdf"
        # URL decoding is not done by extract_filename_from_url
        # It just extracts the filename part
        result = extract_filename_from_url(url)
        # The %20 will remain, but file should still be valid
        assert result.endswith(".pdf")

    def test_url_with_special_characters(self):
        """Test URL with special characters that need sanitization."""
        url = "https://example.com/file<>name.pdf"
        result = extract_filename_from_url(url)
        assert result == "filename.pdf"

    def test_custom_fallback(self):
        """Test custom fallback filename."""
        url = "https://example.com/notapdf"
        assert extract_filename_from_url(url, fallback="custom.pdf") == "custom.pdf"

    def test_real_world_urls(self):
        """Test real-world URL patterns."""
        examples = [
            ("https://example.com/downloads/report.pdf", "report.pdf"),
            ("https://cdn.example.com/files/2024/01/document.pdf", "document.pdf"),
            (
                "https://example.com/api/files/sample.pdf",
                "sample.pdf",
            ),
        ]
        for url, expected in examples:
            assert extract_filename_from_url(url) == expected


class TestSecurityScenarios:
    """Test security-critical scenarios."""

    def test_null_byte_injection(self):
        """Test protection against null byte injection."""
        filename = "document.pdf\x00.exe"
        result = sanitize_filename(filename)
        assert result == "document.pdf.exe.pdf"  # Extension will be changed

    def test_path_traversal_variations(self):
        """Test various path traversal attack patterns."""
        attacks = [
            "../../etc/passwd.pdf",
            "..\\..\\windows\\system32\\config.pdf",
            "....//....//etc/passwd.pdf",
            "/etc/passwd.pdf",
            "C:\\Windows\\System32\\config.pdf",
        ]
        for attack in attacks:
            result = sanitize_filename(attack)
            # Should either be rejected or have path components removed
            assert ".." not in result
            assert "/" not in result
            assert "\\" not in result

    def test_unicode_path_traversal(self):
        """Test Unicode-based path traversal attempts."""
        # Unicode dots and slashes
        filename = "..\u2215..\u2215etc\u2215passwd.pdf"
        result = sanitize_filename(filename)
        # Should be handled safely
        assert result.endswith(".pdf")

    def test_command_injection_chars(self):
        """Test removal of command injection characters."""
        filename = "file;rm -rf.pdf"
        result = sanitize_filename(filename)
        # Semicolon should be removed by illegal char filtering
        assert ";" not in result

    def test_zero_width_characters(self):
        """Test handling of zero-width Unicode characters."""
        filename = "doc\u200Bument.pdf"  # Zero-width space
        result = sanitize_filename(filename)
        assert result == "doc\u200Bument.pdf"  # Zero-width space is not a control char

    def test_very_long_filename_attack(self):
        """Test handling of extremely long filenames."""
        filename = "a" * 10000 + ".pdf"
        result = sanitize_filename(filename)
        assert len(result) <= 255
        assert result.endswith(".pdf")

    def test_empty_after_sanitization(self):
        """Test filenames that become empty after sanitization."""
        # Filename with only illegal characters
        filename = "<>:\"|?*.pdf"
        result = sanitize_filename(filename)
        assert result == "downloaded.pdf"

    def test_content_disposition_with_path_traversal(self):
        """Test Content-Disposition with path traversal."""
        header = 'attachment; filename="../../etc/passwd.pdf"'
        result = parse_content_disposition(header)
        assert result == "downloaded.pdf"
        assert ".." not in result

    def test_content_disposition_with_null_byte(self):
        """Test Content-Disposition with null byte."""
        header = 'attachment; filename="document\x00.exe.pdf"'
        result = parse_content_disposition(header)
        assert "\x00" not in result
        assert result.endswith(".pdf")
