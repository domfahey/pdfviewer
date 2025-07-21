/**
 * Sample PDFs for E2E testing
 * These are the same PDFs available in the UI test loader
 */

export interface SamplePDF {
  name: string;
  url: string;
  description: string;
  localPath?: string; // Path to downloaded file for offline testing
}

export const SAMPLE_PDFS: SamplePDF[] = [
  {
    name: 'EPA Sample Letter',
    url: 'https://19january2021snapshot.epa.gov/sites/static/files/2016-02/documents/epa_sample_letter_sent_to_commissioners_dated_february_29_2015.pdf',
    description: 'Official EPA document with text content (3 pages)',
    localPath: 'tests/e2e/fixtures/epa_sample.pdf'
  },
  {
    name: 'Image-based PDF',
    url: 'https://nlsblog.org/wp-content/uploads/2020/06/image-based-pdf-sample.pdf',
    description: 'Scanned document without text layer',
    localPath: 'tests/e2e/fixtures/image_based.pdf'
  },
  {
    name: 'Anyline Sample Book',
    url: 'https://anyline.com/app/uploads/2022/03/anyline-sample-scan-book.pdf',
    description: 'Multi-page document with mixed content',
    localPath: 'tests/e2e/fixtures/anyline_book.pdf'
  },
  {
    name: 'NHTSA Form',
    url: 'https://www.nhtsa.gov/sites/nhtsa.gov/files/documents/mo_par_rev01_2012.pdf',
    description: 'Government form with fillable fields',
    localPath: 'tests/e2e/fixtures/nhtsa_form.pdf'
  }
];

// Helper function to download PDFs for offline testing
export async function downloadSamplePDFs(): Promise<void> {
  const https = require('https');
  const fs = require('fs');
  const path = require('path');
  
  for (const pdf of SAMPLE_PDFS) {
    if (pdf.localPath && !fs.existsSync(pdf.localPath)) {
      console.log(`Downloading ${pdf.name}...`);
      const file = fs.createWriteStream(pdf.localPath);
      
      await new Promise((resolve, reject) => {
        https.get(pdf.url, (response: any) => {
          response.pipe(file);
          file.on('finish', () => {
            file.close();
            console.log(`Downloaded ${pdf.name}`);
            resolve(void 0);
          });
        }).on('error', (err: Error) => {
          fs.unlink(pdf.localPath!, () => {});
          reject(err);
        });
      });
    }
  }
}