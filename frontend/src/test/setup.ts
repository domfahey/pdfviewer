import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock PDF.js worker
window.URL.createObjectURL = vi.fn(() => 'mock-url');
window.URL.revokeObjectURL = vi.fn();

// Mock canvas context
HTMLCanvasElement.prototype.getContext = vi.fn(() => ({
  clearRect: vi.fn(),
  fillRect: vi.fn(),
  drawImage: vi.fn(),
  save: vi.fn(),
  restore: vi.fn(),
  scale: vi.fn(),
  translate: vi.fn(),
  getImageData: vi.fn(() => ({ data: new Uint8ClampedArray(4) })),
  putImageData: vi.fn(),
})) as unknown as HTMLCanvasElement['getContext'];

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
  root: null,
  rootMargin: '',
  thresholds: [],
  takeRecords: vi.fn(() => []),
}));

// Mock DOMMatrix constructor
global.DOMMatrix = vi.fn().mockImplementation(() => ({
  a: 1,
  b: 0,
  c: 0,
  d: 1,
  e: 0,
  f: 0,
  m11: 1,
  m12: 0,
  m13: 0,
  m14: 0,
  m21: 0,
  m22: 1,
  m23: 0,
  m24: 0,
  m31: 0,
  m32: 0,
  m33: 1,
  m34: 0,
  m41: 0,
  m42: 0,
  m43: 0,
  m44: 1,
  is2D: true,
  isIdentity: true,
  multiply: vi.fn(),
  scale: vi.fn(),
  translate: vi.fn(),
  inverse: vi.fn(),
})) as unknown as typeof DOMMatrix;

// Mock PDF.js library
vi.mock('pdfjs-dist', () => ({
  getDocument: vi.fn(),
  version: '4.0.0',
  build: '4.0.0',
  GlobalWorkerOptions: {
    workerSrc: 'mock-worker.js',
  },
}));
