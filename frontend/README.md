# PDF Viewer Frontend

[![React](https://img.shields.io/badge/React-19.1-blue.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6-blue.svg)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-6.0-646CFF.svg)](https://vitejs.dev/)
[![Material-UI](https://img.shields.io/badge/Material--UI-7-blue.svg)](https://mui.com/)

React 19 + TypeScript + Vite frontend for the PDF Viewer POC.

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Available Scripts](#available-scripts)
- [Project Structure](#project-structure)
- [Key Technologies](#key-technologies)
- [Testing](#testing)
- [Environment Variables](#environment-variables)
- [Browser Support](#browser-support)
- [Known Issues](#known-issues)
- [Development Tips](#development-tips)

## Features

- PDF rendering with PDF.js
- Virtual scrolling for performance
- Full-text search with highlighting
- Test PDF loader for demos
- Material Design UI (MUI v7)
- Responsive design
- React 19 Strict Mode compatible

## Quick Start

```bash
# Install dependencies
npm install

# Development server
npm run dev

# Type checking
npm run type-check

# Tests
npm test
npm run test:coverage

# Build for production
npm run build
```

## Available Scripts

- `npm run dev` - Start development server (port 5173)
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run format` - Format with Prettier
- `npm run type-check` - TypeScript type checking
- `npm test` - Run tests in watch mode
- `npm run test:coverage` - Generate coverage report

## Project Structure

```
src/
├── components/
│   ├── PDFViewer/         # Main PDF viewer components
│   │   ├── PDFViewer.tsx
│   │   ├── PDFControls.tsx
│   │   ├── PDFPage.tsx
│   │   ├── PDFThumbnails.tsx
│   │   ├── PDFExtractedFields.tsx
│   │   └── PDFSearchHighlight.tsx
│   ├── Upload/            # File upload components
│   └── TestPDFLoader.tsx  # Quick PDF demo loader
├── hooks/                 # Custom React hooks
│   ├── useFileUpload.ts
│   ├── usePDFDocument.ts
│   └── usePDFSearch.ts
├── services/              # API and PDF services
│   ├── api.ts
│   └── pdfService.ts
└── types/                 # TypeScript definitions
```

## Key Technologies

- **React 19.1** - Latest React with improved performance
- **TypeScript 5.6** - Type safety and better DX
- **Vite 6.0** - Fast build tool
- **PDF.js 4.9** - PDF rendering engine
- **Material UI 7** - Component library
- **Vitest** - Unit testing framework
- **Playwright** - E2E testing

## Testing

```bash
# Unit tests
npm test

# Coverage report
npm run test:coverage

# E2E tests (from root)
cd ../tests/e2e && npm test
```

## Environment Variables

Create `.env.local`:
```env
VITE_API_BASE_URL=http://localhost:8000/api
```

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## Known Issues

- Large PDFs (>10MB) may have initial load delays
- Search highlighting performance degrades with many matches
- Form field extraction is preview only

## Development Tips

1. Use the Test PDF Loader for quick demos
2. Enable React DevTools for debugging
3. Check browser console for PDF.js warnings
4. Use `npm run type-check` before committing
5. Run `npm run format` to fix formatting