import React, { useEffect, useRef } from 'react';

interface PDFSearchHighlightProps {
  searchQuery: string;
  textLayer: HTMLDivElement | null;
  isCurrentPage: boolean;
}

export const PDFSearchHighlight: React.FC<PDFSearchHighlightProps> = ({
  searchQuery,
  textLayer,
  isCurrentPage,
}) => {
  const highlightedElements = useRef<Element[]>([]);

  useEffect(() => {
    if (!textLayer || !searchQuery.trim()) {
      // Clear existing highlights
      highlightedElements.current.forEach(el => {
        if (el.parentElement) {
          el.parentElement.replaceChild(el.firstChild || document.createTextNode(''), el);
        }
      });
      highlightedElements.current = [];
      return;
    }

    const normalizedQuery = searchQuery.toLowerCase();
    const textElements = textLayer.querySelectorAll('span');
    const newHighlights: Element[] = [];

    textElements.forEach(span => {
      const text = span.textContent || '';
      const normalizedText = text.toLowerCase();

      if (normalizedText.includes(normalizedQuery)) {
        const regex = new RegExp(`(${searchQuery})`, 'gi');
        const parts = text.split(regex);

        const highlightedContent = document.createElement('span');

        parts.forEach(part => {
          if (part.toLowerCase() === normalizedQuery) {
            const mark = document.createElement('mark');
            mark.textContent = part;
            mark.style.backgroundColor = isCurrentPage ? '#ff9632' : '#ffeb3b';
            mark.style.padding = '0 2px';
            mark.style.borderRadius = '2px';
            highlightedContent.appendChild(mark);
            newHighlights.push(mark);
          } else {
            highlightedContent.appendChild(document.createTextNode(part));
          }
        });

        span.innerHTML = '';
        span.appendChild(highlightedContent);
      }
    });

    highlightedElements.current = newHighlights;

    return () => {
      // Cleanup highlights when unmounting
      highlightedElements.current.forEach(el => {
        if (el.parentElement) {
          const text = el.textContent || '';
          el.parentElement.replaceChild(document.createTextNode(text), el);
        }
      });
      highlightedElements.current = [];
    };
  }, [searchQuery, textLayer, isCurrentPage]);

  return null;
};
