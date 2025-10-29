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

// Debounce delay for search operations (ms)
const SEARCH_DEBOUNCE_DELAY = 300;

export const usePDFSearch = (document: PDFDocumentProxy | null) => {
  const [searchState, setSearchState] = useState<SearchState>({
    query: '',
    matches: [],
    currentMatchIndex: -1,
    isSearching: false,
  });

  const searchAbortController = useRef<AbortController | null>(null);
  const debounceTimer = useRef<NodeJS.Timeout | null>(null);

  const performSearch = useCallback(
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
      const normalizedQuery = query.toLowerCase();

      try {
        for (let pageNum = 1; pageNum <= document.numPages; pageNum++) {

        const normalizedQuery = query.toLowerCase();


          if (signal.aborted) break;

          const page = await document.getPage(pageNumber);
          const textContent = await page.getTextContent();

          // Pre-allocate array for better performance
          const textParts: string[] = new Array(textContent.items.length);
          
          for (let i = 0; i < textContent.items.length; i++) {
            const item = textContent.items[i];
            if ('str' in item) {
              textParts[i] = item.str;
            }
          }

          // Join once instead of concatenating in loop
          const pageText = textParts.join(' ');
          const normalizedPageText = pageText.toLowerCase();
          
          // Find all matches in this page
          let searchIndex = 0;
          while ((searchIndex = normalizedPageText.indexOf(normalizedQuery, searchIndex)) !== -1) {
            matches.push({
              pageIndex: pageNum - 1,
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

  const searchInDocument = useCallback(
    (query: string) => {
      // Clear existing debounce timer
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }

      // Debounce the search to avoid excessive processing
      debounceTimer.current = setTimeout(() => {
        performSearch(query);
      }, SEARCH_DEBOUNCE_DELAY);
    },
    [performSearch]
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
    // Clear debounce timer
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }
    
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
