import React, { useEffect, useState, useCallback } from 'react';
import * as pdfjsLib from 'pdfjs-dist';
import { devError } from '../../utils/devLogger';

interface PDFMetadata {
  title?: string;
  author?: string;
  subject?: string;
  keywords?: string;
  creator?: string;
  producer?: string;
  creationDate?: Date;
  modificationDate?: Date;
  pageCount: number;
  fileSize: number;
  encrypted: boolean;
  version?: string;
}

interface PDFDocumentInfo {
  Title?: string;
  Author?: string;
  Subject?: string;
  Keywords?: string;
  Creator?: string;
  Producer?: string;
  CreationDate?: string;
  ModDate?: string;
}

interface PDFDocumentWithInfo {
  _pdfInfo?: {
    PDFFormatVersion?: string;
  };
}

interface PDFMetadataPanelProps {
  pdfDocument: pdfjsLib.PDFDocumentProxy | null;
  fileMetadata?: {
    filename: string;
    file_size: number;
    upload_time: string;
    mime_type: string;
  };
  isVisible: boolean;
  className?: string;
}

export const PDFMetadataPanel: React.FC<PDFMetadataPanelProps> = ({
  pdfDocument,
  fileMetadata,
  isVisible,
  className = '',
}) => {
  const [metadata, setMetadata] = useState<PDFMetadata | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const extractMetadata = useCallback(async () => {
    if (!pdfDocument) return;

    setLoading(true);
    setError(null);

    try {
      const info = await pdfDocument.getMetadata();

      const pdfMetadata: PDFMetadata = {
        pageCount: pdfDocument.numPages,
        fileSize: fileMetadata?.file_size || 0,
        encrypted: false, // PDF.js auto-decrypts, so this would be false if we can read it
        version: `PDF ${(pdfDocument as PDFDocumentWithInfo)?._pdfInfo?.PDFFormatVersion || 'Unknown'}`,
      };

      // Extract document info
      if (info.info) {
        const docInfo = info.info as PDFDocumentInfo;
        pdfMetadata.title = docInfo.Title || undefined;
        pdfMetadata.author = docInfo.Author || undefined;
        pdfMetadata.subject = docInfo.Subject || undefined;
        pdfMetadata.keywords = docInfo.Keywords || undefined;
        pdfMetadata.creator = docInfo.Creator || undefined;
        pdfMetadata.producer = docInfo.Producer || undefined;

        // Parse dates
        if (docInfo.CreationDate) {
          try {
            pdfMetadata.creationDate = new Date(docInfo.CreationDate);
          } catch {
            console.warn('Failed to parse creation date:', docInfo.CreationDate);
          }
        }

        if (docInfo.ModDate) {
          try {
            pdfMetadata.modificationDate = new Date(docInfo.ModDate);
          } catch {
            console.warn('Failed to parse modification date:', docInfo.ModDate);
          }
        }
      }

      setMetadata(pdfMetadata);
    } catch (error) {
      devError('Error extracting PDF metadata:', error);
      setError('Failed to extract PDF metadata');
    } finally {
      setLoading(false);
    }
  }, [pdfDocument, fileMetadata]);

  useEffect(() => {
    if (!pdfDocument || !isVisible) {
      setMetadata(null);
      return;
    }

    extractMetadata();
  }, [pdfDocument, isVisible, extractMetadata]);

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const bytesPerKilobyte = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const sizeUnitIndex = Math.floor(Math.log(bytes) / Math.log(bytesPerKilobyte));
    return (
      parseFloat((bytes / Math.pow(bytesPerKilobyte, sizeUnitIndex)).toFixed(2)) +
      ' ' +
      sizes[sizeUnitIndex]
    );
  };

  const formatDate = (date: Date): string => {
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  if (!isVisible) {
    return null;
  }

  return (
    <div className={`w-80 bg-white border-l border-gray-200 overflow-y-auto ${className}`}>
      <div className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Document Information</h3>

        {loading && (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
            <span className="ml-2 text-sm text-gray-600">Loading metadata...</span>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-4">
            <div className="text-sm text-red-600">{error}</div>
          </div>
        )}

        {metadata && (
          <div className="space-y-6">
            {/* File Information */}
            <div>
              <h4 className="text-sm font-medium text-gray-900 mb-3">File Information</h4>
              <div className="space-y-2">
                {fileMetadata?.filename && (
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Filename:</span>
                    <span className="text-sm text-gray-900 font-medium break-all ml-2">
                      {fileMetadata.filename}
                    </span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">File Size:</span>
                  <span className="text-sm text-gray-900 font-medium">
                    {formatFileSize(metadata.fileSize)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Pages:</span>
                  <span className="text-sm text-gray-900 font-medium">{metadata.pageCount}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Version:</span>
                  <span className="text-sm text-gray-900 font-medium">
                    {metadata.version || 'Unknown'}
                  </span>
                </div>
                {fileMetadata?.upload_time && (
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Uploaded:</span>
                    <span className="text-sm text-gray-900 font-medium">
                      {formatDate(new Date(fileMetadata.upload_time))}
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Document Properties */}
            {(metadata.title || metadata.author || metadata.subject || metadata.creator) && (
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-3">Document Properties</h4>
                <div className="space-y-2">
                  {metadata.title && (
                    <div>
                      <span className="text-sm text-gray-600 block">Title:</span>
                      <span className="text-sm text-gray-900 font-medium break-words">
                        {metadata.title}
                      </span>
                    </div>
                  )}
                  {metadata.author && (
                    <div>
                      <span className="text-sm text-gray-600 block">Author:</span>
                      <span className="text-sm text-gray-900 font-medium">{metadata.author}</span>
                    </div>
                  )}
                  {metadata.subject && (
                    <div>
                      <span className="text-sm text-gray-600 block">Subject:</span>
                      <span className="text-sm text-gray-900 font-medium break-words">
                        {metadata.subject}
                      </span>
                    </div>
                  )}
                  {metadata.creator && (
                    <div>
                      <span className="text-sm text-gray-600 block">Creator:</span>
                      <span className="text-sm text-gray-900 font-medium">{metadata.creator}</span>
                    </div>
                  )}
                  {metadata.producer && (
                    <div>
                      <span className="text-sm text-gray-600 block">Producer:</span>
                      <span className="text-sm text-gray-900 font-medium">{metadata.producer}</span>
                    </div>
                  )}
                  {metadata.keywords && (
                    <div>
                      <span className="text-sm text-gray-600 block">Keywords:</span>
                      <span className="text-sm text-gray-900 font-medium break-words">
                        {metadata.keywords}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Dates */}
            {(metadata.creationDate || metadata.modificationDate) && (
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-3">Dates</h4>
                <div className="space-y-2">
                  {metadata.creationDate && (
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Created:</span>
                      <span className="text-sm text-gray-900 font-medium">
                        {formatDate(metadata.creationDate)}
                      </span>
                    </div>
                  )}
                  {metadata.modificationDate && (
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Modified:</span>
                      <span className="text-sm text-gray-900 font-medium">
                        {formatDate(metadata.modificationDate)}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Security */}
            <div>
              <h4 className="text-sm font-medium text-gray-900 mb-3">Security</h4>
              <div className="flex items-center">
                <div
                  className={`w-3 h-3 rounded-full mr-2 ${metadata.encrypted ? 'bg-yellow-500' : 'bg-green-500'}`}
                ></div>
                <span className="text-sm text-gray-900">
                  {metadata.encrypted ? 'Encrypted' : 'Not encrypted'}
                </span>
              </div>
            </div>

            {/* Performance Info */}
            <div>
              <h4 className="text-sm font-medium text-gray-900 mb-3">Performance</h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Pages per MB:</span>
                  <span className="text-sm text-gray-900 font-medium">
                    {metadata.fileSize > 0
                      ? Math.round(metadata.pageCount / (metadata.fileSize / (1024 * 1024)))
                      : 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Avg. page size:</span>
                  <span className="text-sm text-gray-900 font-medium">
                    {metadata.pageCount > 0
                      ? formatFileSize(Math.round(metadata.fileSize / metadata.pageCount))
                      : 'N/A'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
