#!/usr/bin/env python3
"""
Download sample PDFs for integration testing.
Run this script to download all sample PDFs used in tests.
"""
import os
import requests
from pathlib import Path

SAMPLE_PDFS = [
    {
        'name': 'epa_sample.pdf',
        'url': 'https://19january2021snapshot.epa.gov/sites/static/files/2016-02/documents/epa_sample_letter_sent_to_commissioners_dated_february_29_2015.pdf',
        'description': 'EPA Sample Letter (3 pages, text content)'
    },
    {
        'name': 'image_based.pdf',
        'url': 'https://nlsblog.org/wp-content/uploads/2020/06/image-based-pdf-sample.pdf',
        'description': 'Image-based PDF (scanned document)'
    },
    {
        'name': 'anyline_book.pdf',
        'url': 'https://anyline.com/app/uploads/2022/03/anyline-sample-scan-book.pdf',
        'description': 'Anyline Sample Book (multi-page mixed content)'
    },
    {
        'name': 'nhtsa_form.pdf',
        'url': 'https://www.nhtsa.gov/sites/nhtsa.gov/files/documents/mo_par_rev01_2012.pdf',
        'description': 'NHTSA Form (government form with fillable fields)'
    }
]

def download_samples():
    """Download all sample PDFs."""
    fixtures_dir = Path(__file__).parent
    fixtures_dir.mkdir(exist_ok=True)
    
    for pdf in SAMPLE_PDFS:
        file_path = fixtures_dir / pdf['name']
        
        if file_path.exists():
            print(f"✓ {pdf['name']} already exists")
            continue
            
        print(f"Downloading {pdf['name']}...")
        try:
            response = requests.get(pdf['url'], timeout=30)
            response.raise_for_status()
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
                
            print(f"✓ Downloaded {pdf['name']} - {pdf['description']}")
            
        except Exception as e:
            print(f"✗ Failed to download {pdf['name']}: {e}")
            
    # Create the main sample.pdf symlink to EPA sample
    sample_path = fixtures_dir / 'sample.pdf'
    epa_path = fixtures_dir / 'epa_sample.pdf'
    
    if not sample_path.exists() and epa_path.exists():
        try:
            os.symlink(epa_path, sample_path)
            print("✓ Created sample.pdf symlink to epa_sample.pdf")
        except:
            # On Windows, just copy the file
            import shutil
            shutil.copy(epa_path, sample_path)
            print("✓ Created sample.pdf copy of epa_sample.pdf")

if __name__ == '__main__':
    download_samples()
    print("\nAll sample PDFs ready for testing!")