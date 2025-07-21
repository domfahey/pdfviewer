import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export const testFiles = {
  // Small valid PDF for basic tests
  smallPDF: {
    path: path.join(__dirname, '..', '..', 'fixtures', 'sample.pdf'),
    name: 'sample.pdf',
    size: 3028, // bytes
    pages: 1,
  },
  
  // EPA sample PDF for real-world testing
  epaPDF: {
    path: path.join(__dirname, '..', '..', 'fixtures', 'epa_sample.pdf'),
    name: 'epa_sample.pdf',
    size: 245938, // bytes
    pages: 2,
  },

  // Invalid file types for error testing
  invalidFile: {
    path: path.join(__dirname, 'invalid-file.txt'),
    name: 'invalid-file.txt',
    size: 100,
  },

  // Large file for performance testing
  largePDF: {
    path: path.join(__dirname, '..', '..', 'fixtures', 'anyline_sample.pdf'),
    name: 'anyline_sample.pdf',
    size: 4154253, // ~4MB
    pages: 52,
  },
};