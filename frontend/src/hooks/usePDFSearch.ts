import { useState, useCallback, useRef } from 'react';
import type { PDFDocumentProxy } from 'pdfjs-dist';

interface SearchMatch {
  pageIndex: number;
  matchIndex: number;
  text: string;
}

interface SearchState {
  query: string;
  matches: SearchMatch[];
  currentMatchIndex: number;
  isSearching: boolean;
}

export const usePDFSearch = (document: PDFDocumentProxy | null) => {
  const [searchState, setSearchState] = useState<SearchState>({
    query: '',
    matches: [],
    currentMatchIndex: -1,
    isSearching: false,
  });

  const searchAbortController = useRef<AbortController | null>(null);

  const searchInDocument = useCallback(
    async (query: string) => {
      if (!document || !query.trim()) {
        setSearchState({
          query: '',
          matches: [],
          currentMatchIndex: -1,
          isSearching: false,
        });
        return;
      }

      // Cancel any ongoing search
      if (searchAbortController.current) {
        searchAbortController.current.abort();
      }

      searchAbortController.current = new AbortController();
      const { signal } = searchAbortController.current;

      setSearchState(prev => ({
        ...prev,
        query,
        isSearching: true,
        matches: [],
        currentMatchIndex: -1,
      }));

      const matches: SearchMatch[] = [];

      try {
        const normalizedQuery = query.toLowerCase();

        for (let pageNumber = 1; pageNumber <= document.numPages; pageNumber++) {
          if (signal.aborted) break;

          const page = await document.getPage(pageNumber);
          const textContent = await page.getTextContent();

          // Combine all text items into a single string for searching
          let pageText = '';
          const textItems = textContent.items;

          for (const item of textItems) {
            if ('str' in item) {
              pageText += item.str + ' ';
            }
          }

          // Search for matches in the page text
          const normalizedPageText = pageText.toLowerCase();
          let currentSearchPosition = 0;

          while ((currentSearchPosition = normalizedPageText.indexOf(normalizedQuery, currentSearchPosition)) !== -1) {
            matches.push({
              pageIndex: pageNumber - 1, // Convert to 0-based index
              matchIndex: matches.length,
              text: pageText.substring(currentSearchPosition, currentSearchPosition + query.length),
            });
            currentSearchPosition += normalizedQuery.length;
          }
        }

        if (!signal.aborted) {
          setSearchState({
            query,
            matches,
            currentMatchIndex: matches.length > 0 ? 0 : -1,
            isSearching: false,
          });
        }
      } catch (error) {
        if (!signal.aborted) {
          console.error('Error searching PDF:', error);
          setSearchState(prev => ({
            ...prev,
            isSearching: false,
          }));
        }
      }
    },
    [document]
  );

  const nextMatch = useCallback(() => {
    setSearchState(prev => ({
      ...prev,
      currentMatchIndex:
        prev.matches.length > 0 ? (prev.currentMatchIndex + 1) % prev.matches.length : -1,
    }));
  }, []);

  const previousMatch = useCallback(() => {
    setSearchState(prev => ({
      ...prev,
      currentMatchIndex:
        prev.matches.length > 0
          ? prev.currentMatchIndex <= 0
            ? prev.matches.length - 1
            : prev.currentMatchIndex - 1
          : -1,
    }));
  }, []);

  const clearSearch = useCallback(() => {
    if (searchAbortController.current) {
      searchAbortController.current.abort();
    }
    setSearchState({
      query: '',
      matches: [],
      currentMatchIndex: -1,
      isSearching: false,
    });
  }, []);

  const getCurrentMatch = useCallback(() => {
    const { matches, currentMatchIndex } = searchState;
    if (currentMatchIndex >= 0 && currentMatchIndex < matches.length) {
      return matches[currentMatchIndex];
    }
    return null;
  }, [searchState]);

  return {
    searchQuery: searchState.query,
    searchMatches: searchState.matches,
    currentMatchIndex: searchState.currentMatchIndex,
    isSearching: searchState.isSearching,
    totalMatches: searchState.matches.length,
    search: searchInDocument,
    nextMatch,
    previousMatch,
    clearSearch,
    getCurrentMatch,
  };
};
