"""
Script to generate test PDF fixtures for integration testing.
"""
import io
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from pypdf import PdfWriter, PdfReader


def create_sample_pdf(output_path: Path, num_pages: int = 3, title: str = "Sample PDF"):
    """Create a simple PDF with text content."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    for page_num in range(1, num_pages + 1):
        # Add text to page
        c.drawString(100, 750, f"{title}")
        c.drawString(100, 700, f"Page {page_num} of {num_pages}")
        c.drawString(100, 650, "This is a sample PDF document for testing.")
        c.drawString(100, 600, "It contains searchable text content.")
        c.drawString(100, 550, "The quick brown fox jumps over the lazy dog.")
        
        # Add some form fields for extraction testing
        if page_num == 1:
            c.drawString(100, 500, "Name: John Doe")
            c.drawString(100, 450, "Email: john@example.com")
            c.drawString(100, 400, "Phone: (555) 123-4567")
            c.drawString(100, 350, "Date: 2024-01-15")
        
        c.showPage()
    
    c.save()
    
    # Write to file
    with open(output_path, "wb") as f:
        f.write(buffer.getvalue())
    
    print(f"Created {output_path} ({num_pages} pages)")


def create_large_pdf(output_path: Path, num_pages: int = 100):
    """Create a large PDF for performance testing."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    for page_num in range(1, num_pages + 1):
        c.drawString(100, 750, f"Large PDF - Page {page_num}")
        
        # Add lots of text to make it larger
        y_position = 700
        for line in range(30):
            c.drawString(100, y_position, f"Line {line + 1}: " + "x" * 50)
            y_position -= 20
        
        c.showPage()
    
    c.save()
    
    with open(output_path, "wb") as f:
        f.write(buffer.getvalue())
    
    print(f"Created large PDF {output_path} ({num_pages} pages)")


def create_corrupt_pdf(output_path: Path):
    """Create a corrupt PDF file for error testing."""
    # Start with valid PDF header but corrupt content
    corrupt_content = b"%PDF-1.4\n%\xE2\xE3\xCF\xD3\n"
    corrupt_content += b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    corrupt_content += b"CORRUPTED DATA HERE" * 100
    corrupt_content += b"\n%%EOF"
    
    with open(output_path, "wb") as f:
        f.write(corrupt_content)
    
    print(f"Created corrupt PDF {output_path}")


def create_empty_pdf(output_path: Path):
    """Create an empty PDF file."""
    writer = PdfWriter()
    
    with open(output_path, "wb") as f:
        writer.write(f)
    
    print(f"Created empty PDF {output_path}")


def main():
    """Generate all test fixtures."""
    fixtures_dir = Path(__file__).parent
    fixtures_dir.mkdir(exist_ok=True)
    
    # Create sample PDFs
    create_sample_pdf(fixtures_dir / "sample.pdf", num_pages=3)
    create_sample_pdf(fixtures_dir / "single_page.pdf", num_pages=1)
    create_sample_pdf(fixtures_dir / "multi_page.pdf", num_pages=10)
    
    # Create large PDF (25MB+)
    create_large_pdf(fixtures_dir / "large_sample.pdf", num_pages=100)
    
    # Create problematic PDFs
    create_corrupt_pdf(fixtures_dir / "corrupt.pdf")
    create_empty_pdf(fixtures_dir / "empty.pdf")
    
    print("\nAll test fixtures generated successfully!")


if __name__ == "__main__":
    # Check if required libraries are installed
    try:
        import reportlab
        import pypdf
    except ImportError:
        print("Please install required libraries:")
        print("pip install reportlab pypdf")
        exit(1)
    
    main()