/**
 * Comprehensive unit tests for usePDFSearch hook.
 *
 * Tests cover search functionality, match navigation,
 * abort handling, and edge cases.
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { usePDFSearch } from '../usePDFSearch';
import { createMockDocument } from '../../test/pdfMockHelpers';

describe('usePDFSearch', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Initial State', () => {
    it('should have correct initial state with null document', () => {
      const { result } = renderHook(() => usePDFSearch(null));

      expect(result.current.searchQuery).toBe('');
      expect(result.current.searchMatches).toEqual([]);
      expect(result.current.currentMatchIndex).toBe(-1);
      expect(result.current.isSearching).toBe(false);
      expect(result.current.totalMatches).toBe(0);
    });

    it('should provide all required functions', () => {
      const { result } = renderHook(() => usePDFSearch(null));

      expect(typeof result.current.search).toBe('function');
      expect(typeof result.current.nextMatch).toBe('function');
      expect(typeof result.current.previousMatch).toBe('function');
      expect(typeof result.current.clearSearch).toBe('function');
      expect(typeof result.current.getCurrentMatch).toBe('function');
    });
  });

  describe('Search Functionality', () => {
    it('should find matches in a single page', async () => {
      const mockDoc = createMockDocument([{ pageNum: 1, text: 'hello world hello universe' }]);

      const { result } = renderHook(() => usePDFSearch(mockDoc));

      await act(async () => {
        await result.current.search('hello');
      });

      await waitFor(() => {
        expect(result.current.searchMatches).toHaveLength(2);
        expect(result.current.totalMatches).toBe(2);
        expect(result.current.currentMatchIndex).toBe(0);
        expect(result.current.isSearching).toBe(false);
      });
    });

    it('should find matches across multiple pages', async () => {
      const mockDoc = createMockDocument([
        { pageNum: 1, text: 'hello world' },
        { pageNum: 2, text: 'goodbye hello' },
        { pageNum: 3, text: 'hello again' },
      ]);

      const { result } = renderHook(() => usePDFSearch(mockDoc));

      await act(async () => {
        await result.current.search('hello');
      });

      await waitFor(() => {
        expect(result.current.totalMatches).toBe(3);
        expect(result.current.searchMatches[0].pageIndex).toBe(0);
        expect(result.current.searchMatches[1].pageIndex).toBe(1);
        expect(result.current.searchMatches[2].pageIndex).toBe(2);
      });
    });

    it('should perform case-insensitive search', async () => {
      const mockDoc = createMockDocument([{ pageNum: 1, text: 'Hello HELLO hello HeLLo' }]);

      const { result } = renderHook(() => usePDFSearch(mockDoc));

      await act(async () => {
        await result.current.search('hello');
      });

      await waitFor(() => {
        expect(result.current.totalMatches).toBe(4);
      });
    });

    it('should handle empty search query', async () => {
      const mockDoc = createMockDocument([{ pageNum: 1, text: 'hello world' }]);

      const { result } = renderHook(() => usePDFSearch(mockDoc));

      await act(async () => {
        await result.current.search('');
      });

      expect(result.current.searchMatches).toEqual([]);
      expect(result.current.currentMatchIndex).toBe(-1);
    });

    it('should handle whitespace-only query', async () => {
      const mockDoc = createMockDocument([{ pageNum: 1, text: 'hello world' }]);

      const { result } = renderHook(() => usePDFSearch(mockDoc));

      await act(async () => {
        await result.current.search('   ');
      });

      expect(result.current.searchMatches).toEqual([]);
      expect(result.current.currentMatchIndex).toBe(-1);
    });

    it('should handle search with no matches', async () => {
      const mockDoc = createMockDocument([{ pageNum: 1, text: 'hello world' }]);

      const { result } = renderHook(() => usePDFSearch(mockDoc));

      await act(async () => {
        await result.current.search('nonexistent');
      });

      await waitFor(() => {
        expect(result.current.totalMatches).toBe(0);
        expect(result.current.currentMatchIndex).toBe(-1);
      });
    });

    it('should set searching state during search', async () => {
      const mockDoc = createMockDocument([{ pageNum: 1, text: 'test document' }]);

      const { result } = renderHook(() => usePDFSearch(mockDoc));

      act(() => {
        result.current.search('test');
      });

      expect(result.current.isSearching).toBe(true);

      await waitFor(() => {
        expect(result.current.isSearching).toBe(false);
      });
    });

    it('should reset state when searching with null document', async () => {
      const { result } = renderHook(() => usePDFSearch(null));

      await act(async () => {
        await result.current.search('test');
      });

      expect(result.current.searchMatches).toEqual([]);
      expect(result.current.currentMatchIndex).toBe(-1);
      expect(result.current.isSearching).toBe(false);
    });
  });

  describe('Match Navigation', () => {
    it('should navigate to next match', async () => {
      const mockDoc = createMockDocument([{ pageNum: 1, text: 'test one test two test three' }]);

      const { result } = renderHook(() => usePDFSearch(mockDoc));

      await act(async () => {
        await result.current.search('test');
      });

      await waitFor(() => {
        expect(result.current.totalMatches).toBe(3);
      });

      expect(result.current.currentMatchIndex).toBe(0);

      act(() => {
        result.current.nextMatch();
      });

      expect(result.current.currentMatchIndex).toBe(1);

      act(() => {
        result.current.nextMatch();
      });

      expect(result.current.currentMatchIndex).toBe(2);
    });

    it('should wrap around to first match when at end', async () => {
      const mockDoc = createMockDocument([{ pageNum: 1, text: 'test one test two' }]);

      const { result } = renderHook(() => usePDFSearch(mockDoc));

      await act(async () => {
        await result.current.search('test');
      });

      await waitFor(() => {
        expect(result.current.totalMatches).toBe(2);
      });

      // At index 0
      act(() => {
        result.current.nextMatch();
      });
      expect(result.current.currentMatchIndex).toBe(1);

      // Wrap around to 0
      act(() => {
        result.current.nextMatch();
      });
      expect(result.current.currentMatchIndex).toBe(0);
    });

    it('should navigate to previous match', async () => {
      const mockDoc = createMockDocument([{ pageNum: 1, text: 'test one test two test three' }]);

      const { result } = renderHook(() => usePDFSearch(mockDoc));

      await act(async () => {
        await result.current.search('test');
      });

      await waitFor(() => {
        expect(result.current.totalMatches).toBe(3);
      });

      // Move to last match first
      act(() => {
        result.current.nextMatch();
        result.current.nextMatch();
      });
      expect(result.current.currentMatchIndex).toBe(2);

      // Go back
      act(() => {
        result.current.previousMatch();
      });
      expect(result.current.currentMatchIndex).toBe(1);
    });

    it('should wrap around to last match when at beginning', async () => {
      const mockDoc = createMockDocument([{ pageNum: 1, text: 'test one test two test three' }]);

      const { result } = renderHook(() => usePDFSearch(mockDoc));

      await act(async () => {
        await result.current.search('test');
      });

      await waitFor(() => {
        expect(result.current.totalMatches).toBe(3);
      });

      // At index 0, go previous wraps to last
      act(() => {
        result.current.previousMatch();
      });
      expect(result.current.currentMatchIndex).toBe(2);
    });

    it('should handle navigation with no matches', () => {
      const mockDoc = createMockDocument([{ pageNum: 1, text: 'no matches here' }]);

      const { result } = renderHook(() => usePDFSearch(mockDoc));

      act(() => {
        result.current.nextMatch();
      });

      expect(result.current.currentMatchIndex).toBe(-1);

      act(() => {
        result.current.previousMatch();
      });

      expect(result.current.currentMatchIndex).toBe(-1);
    });
  });

  describe('getCurrentMatch', () => {
    it('should return current match when valid', async () => {
      const mockDoc = createMockDocument([{ pageNum: 1, text: 'hello world' }]);

      const { result } = renderHook(() => usePDFSearch(mockDoc));

      await act(async () => {
        await result.current.search('hello');
      });

      await waitFor(() => {
        expect(result.current.totalMatches).toBe(1);
      });

      const currentMatch = result.current.getCurrentMatch();
      expect(currentMatch).not.toBeNull();
      expect(currentMatch?.pageIndex).toBe(0);
      expect(currentMatch?.matchIndex).toBe(0);
    });

    it('should return null when no matches', () => {
      const mockDoc = createMockDocument([{ pageNum: 1, text: 'test' }]);

      const { result } = renderHook(() => usePDFSearch(mockDoc));

      const currentMatch = result.current.getCurrentMatch();
      expect(currentMatch).toBeNull();
    });

    it('should return null when currentMatchIndex is -1', async () => {
      const mockDoc = createMockDocument([{ pageNum: 1, text: 'test' }]);

      const { result } = renderHook(() => usePDFSearch(mockDoc));

      await act(async () => {
        await result.current.search('nonexistent');
      });

      await waitFor(() => {
        expect(result.current.currentMatchIndex).toBe(-1);
      });

      const currentMatch = result.current.getCurrentMatch();
      expect(currentMatch).toBeNull();
    });
  });

  describe('clearSearch', () => {
    it('should clear search results', async () => {
      const mockDoc = createMockDocument([{ pageNum: 1, text: 'hello world' }]);

      const { result } = renderHook(() => usePDFSearch(mockDoc));

      await act(async () => {
        await result.current.search('hello');
      });

      await waitFor(() => {
        expect(result.current.totalMatches).toBe(1);
      });

      act(() => {
        result.current.clearSearch();
      });

      expect(result.current.searchQuery).toBe('');
      expect(result.current.searchMatches).toEqual([]);
      expect(result.current.currentMatchIndex).toBe(-1);
      expect(result.current.isSearching).toBe(false);
    });

    it('should abort ongoing search', async () => {
      const mockDoc = createMockDocument([
        { pageNum: 1, text: 'test' },
        { pageNum: 2, text: 'test' },
        { pageNum: 3, text: 'test' },
      ]);

      const { result } = renderHook(() => usePDFSearch(mockDoc));

      act(() => {
        result.current.search('test');
      });

      // Clear while search is in progress
      act(() => {
        result.current.clearSearch();
      });

      expect(result.current.searchMatches).toEqual([]);
      expect(result.current.isSearching).toBe(false);
    });
  });

  describe('Search Abortion', () => {
    it('should abort previous search when new search starts', async () => {
      const mockDoc = createMockDocument([
        { pageNum: 1, text: 'first search term' },
        { pageNum: 2, text: 'second search term' },
      ]);

      const { result } = renderHook(() => usePDFSearch(mockDoc));

      // Start first search
      act(() => {
        result.current.search('first');
      });

      // Immediately start second search
      await act(async () => {
        await result.current.search('second');
      });

      // Should have results from second search
      await waitFor(() => {
        expect(result.current.searchQuery).toBe('second');
        expect(result.current.totalMatches).toBeGreaterThan(0);
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle document with no pages', async () => {
      const mockDoc = createMockDocument([]);

      const { result } = renderHook(() => usePDFSearch(mockDoc));

      await act(async () => {
        await result.current.search('test');
      });

      await waitFor(() => {
        expect(result.current.totalMatches).toBe(0);
      });
    });

    it('should handle empty text content', async () => {
      const mockDoc = createMockDocument([{ pageNum: 1, text: '' }]);

      const { result } = renderHook(() => usePDFSearch(mockDoc));

      await act(async () => {
        await result.current.search('test');
      });

      await waitFor(() => {
        expect(result.current.totalMatches).toBe(0);
      });
    });

    it('should handle special characters in search query', async () => {
      const mockDoc = createMockDocument([{ pageNum: 1, text: 'test@example.com and test123' }]);

      const { result } = renderHook(() => usePDFSearch(mockDoc));

      await act(async () => {
        await result.current.search('test@');
      });

      await waitFor(() => {
        expect(result.current.totalMatches).toBeGreaterThan(0);
      });
    });

    it('should update match indices correctly', async () => {
      const mockDoc = createMockDocument([
        { pageNum: 1, text: 'match match' },
        { pageNum: 2, text: 'match' },
      ]);

      const { result } = renderHook(() => usePDFSearch(mockDoc));

      await act(async () => {
        await result.current.search('match');
      });

      await waitFor(() => {
        expect(result.current.searchMatches).toHaveLength(3);
        expect(result.current.searchMatches[0].matchIndex).toBe(0);
        expect(result.current.searchMatches[1].matchIndex).toBe(1);
        expect(result.current.searchMatches[2].matchIndex).toBe(2);
      });
    });
  });
});
