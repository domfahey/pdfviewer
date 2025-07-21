import { test as base } from '@playwright/test';
import express from 'express';
import path from 'path';
import fs from 'fs';

/**
 * Mock PDF server for reliable E2E testing
 * Serves local PDF files to avoid external URL dependencies
 */

export const test = base.extend<{
  mockPdfServer: {
    url: string;
    port: number;
    stop: () => Promise<void>;
  };
}>({
  mockPdfServer: async ({}, use) => {
    const app = express();
    const port = 9999; // Use a fixed port for the mock server
    
    // Serve static PDF files
    app.get('/pdfs/:filename', (req, res) => {
      const filename = req.params.filename;
      const pdfPath = path.join(process.cwd(), 'tests/fixtures', filename);
      
      if (fs.existsSync(pdfPath)) {
        res.setHeader('Content-Type', 'application/pdf');
        res.sendFile(pdfPath);
      } else {
        res.status(404).send('PDF not found');
      }
    });
    
    // Simulate slow download
    app.get('/pdfs/slow/:filename', async (req, res) => {
      const filename = req.params.filename;
      const pdfPath = path.join(process.cwd(), 'tests/fixtures', filename);
      
      if (fs.existsSync(pdfPath)) {
        // Simulate slow network
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        res.setHeader('Content-Type', 'application/pdf');
        res.sendFile(pdfPath);
      } else {
        res.status(404).send('PDF not found');
      }
    });
    
    // Simulate error
    app.get('/pdfs/error/:filename', (req, res) => {
      res.status(500).send('Internal server error');
    });
    
    // Start server
    const server = await new Promise<any>((resolve) => {
      const s = app.listen(port, () => {
        console.log(`Mock PDF server running on port ${port}`);
        resolve(s);
      });
    });
    
    // Use the mock server
    await use({
      url: `http://localhost:${port}`,
      port,
      stop: async () => {
        await new Promise<void>((resolve) => {
          server.close(() => resolve());
        });
      }
    });
    
    // Cleanup
    await new Promise<void>((resolve) => {
      server.close(() => resolve());
    });
  },
});

// Helper to update test PDFs configuration
export function getMockPDFUrls(serverUrl: string) {
  return [
    {
      name: 'EPA Sample Letter',
      url: `${serverUrl}/pdfs/epa_sample.pdf`,
      description: 'Official EPA document with text content',
    },
    {
      name: 'Image-based PDF',
      url: `${serverUrl}/pdfs/image_based.pdf`,
      description: 'Scanned document without text layer',
    },
    {
      name: 'Anyline Sample Book',
      url: `${serverUrl}/pdfs/anyline_book.pdf`,
      description: 'Multi-page document with mixed content',
    },
    {
      name: 'Slow Loading PDF',
      url: `${serverUrl}/pdfs/slow/epa_sample.pdf`,
      description: 'Simulates slow network conditions',
    },
    {
      name: 'Error PDF',
      url: `${serverUrl}/pdfs/error/test.pdf`,
      description: 'Simulates server error',
    }
  ];
}