export interface PDFMetadata {
  title?: string;
  author?: string;
  subject?: string;
  creator?: string;
  producer?: string;
  creation_date?: string;
  modification_date?: string;
  page_count: number;
  file_size: number;
  encrypted: boolean;
}

export interface PDFUploadResponse {
  file_id: string;
  filename: string;
  file_size: number;
  mime_type: string;
  upload_time: string;
  metadata?: PDFMetadata;
}

export interface PDFDocument {
  id: string;
  filename: string;
  url: string;
  metadata: PDFMetadata;
}

export interface PDFPage {
  pageNumber: number;
  viewport: unknown;
  canvas?: HTMLCanvasElement;
  textLayer?: HTMLDivElement;
  annotationLayer?: HTMLDivElement;
}
