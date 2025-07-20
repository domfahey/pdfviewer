export interface Annotation {
  id: string;
  type: 'text' | 'highlight' | 'link' | 'form' | 'stamp';
  pageNumber: number;
  rect: [number, number, number, number];
  content?: string;
  url?: string;
}

export interface AnnotationLayerProps {
  annotations: Annotation[];
  viewport: unknown;
  onAnnotationClick?: (annotation: Annotation) => void;
}

export interface FormField {
  id: string;
  type: 'text' | 'checkbox' | 'radio' | 'dropdown';
  name: string;
  value: string | boolean;
  rect: [number, number, number, number];
  pageNumber: number;
}
