# PDF Search Implementation

## Overview
Implemented full-text search functionality for the PDF viewer using PDF.js text extraction capabilities.

## Key Components

### 1. `usePDFSearch` Hook (`hooks/usePDFSearch.ts`)
- Custom React hook that manages search state
- Extracts text from all PDF pages
- Finds matches across the entire document
- Provides navigation between search results
- Handles search cancellation for performance

### 2. Updated `PDFControls` Component
- Enhanced search UI with match counter (e.g., "1 of 5")
- Previous/Next navigation buttons for search results
- Loading state during search
- Clear search functionality

### 3. `PDFSearchHighlight` Component
- Highlights search matches in the text layer
- Different colors for current match vs other matches
- Cleans up highlights when search is cleared

### 4. Integration with `PDFViewer` and `PDFPage`
- Pass search state through component hierarchy
- Automatically navigate to pages with search results
- Highlight matches on the current page

## Features

1. **Case-insensitive search** - Searches are case-insensitive by default
2. **Multi-page search** - Searches across all pages in the document
3. **Search navigation** - Navigate between matches with Previous/Next buttons
4. **Visual feedback** - Current match highlighted in orange, others in yellow
5. **Search counter** - Shows "X of Y" matches
6. **Keyboard support** - Can be extended to support F3/Shift+F3 shortcuts

## Usage

1. Click the search icon in the PDF controls toolbar
2. Enter search term in the search field
3. Press Enter or click the search button
4. Use arrow buttons to navigate between results
5. Click X to clear search and close search bar

## Technical Details

- Uses PDF.js `getTextContent()` API to extract searchable text
- Implements efficient text search with abort controller
- Maintains search state in the main PDFViewer component
- Highlights are applied to the text layer without modifying the PDF

## Future Enhancements

- Regular expression search support
- Case-sensitive search toggle
- Whole word search option
- Search history
- Export search results
- Keyboard shortcuts (F3, Ctrl+F)