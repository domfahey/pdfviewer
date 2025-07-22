#!/usr/bin/env python3
"""Test script to check if we can replace python-magic with simple header checking."""

import os
import glob
from pathlib import Path


def check_pdf_header(file_path: str) -> bool:
    """Check if file has PDF header signature."""
    try:
        with open(file_path, 'rb') as f:
            # Read first 5 bytes (enough for %PDF-)
            header = f.read(5)
            # Check if starts with %PDF
            return header.startswith(b'%PDF')
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return False


def main() -> None:
    """Test PDF header checking on all PDF files in uploads directory."""
    upload_dir = Path("uploads")
    
    if not upload_dir.exists():
        print("No uploads directory found")
        return
    
    # Find all PDF files
    pdf_files = list(upload_dir.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF files to test\n")
    
    # Test each file
    valid_count = 0
    invalid_count = 0
    
    for pdf_file in pdf_files:
        is_valid = check_pdf_header(str(pdf_file))
        if is_valid:
            valid_count += 1
            print(f"✓ {pdf_file.name} - Valid PDF header")
        else:
            invalid_count += 1
            print(f"✗ {pdf_file.name} - Invalid PDF header")
            # Show what the header actually is
            try:
                with open(pdf_file, 'rb') as f:
                    actual_header = f.read(10)
                    print(f"  Actual header (hex): {actual_header.hex()}")
                    print(f"  Actual header (ascii): {repr(actual_header)}")
            except:
                pass
    
    print(f"\nSummary:")
    print(f"Valid PDFs: {valid_count}")
    print(f"Invalid PDFs: {invalid_count}")
    
    # Also test with python-magic if available
    try:
        import magic
        print("\n--- Comparing with python-magic ---")
        mime = magic.Magic(mime=True)
        
        for pdf_file in pdf_files[:5]:  # Just test first 5
            header_check = check_pdf_header(str(pdf_file))
            magic_check = mime.from_file(str(pdf_file))
            print(f"{pdf_file.name}:")
            print(f"  Header check: {header_check}")
            print(f"  Magic check: {magic_check}")
            print(f"  Match: {header_check == (magic_check == 'application/pdf')}")
    except ImportError:
        print("\npython-magic not available for comparison")


if __name__ == "__main__":
    main()