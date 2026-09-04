/**
 * @file types.ts
 * @description Central TypeScript type definitions for the Finance Analysis platform,
 * including BCTC document metadata, AI chat messages, and financial metrics.
 */

export interface BCTCMetrics {
  revenue?: number | null;
  profit_after_tax?: number | null;
  eps?: number | null;
  pe?: number | null;
  pb?: number | null;
  roe?: number | null;
  debt_to_equity?: number | null;
  auditor_opinion?: string | null;
  currency?: string;
  fiscal_period?: string;
  [key: string]: any;
}

export interface BCTCDocumentInfo {
  doc_id: string;
  filename: string;
  page_count: number;
  markdown_url: string;
  metrics?: BCTCMetrics;
  storage_location?: string;
  created_at?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  citations?: string[];
  doc_id?: string;
  pdf_url?: string | null;
  disclaimer?: string;
  isError?: boolean;
}

export interface ComprehensiveReportResult {
  symbol: string;
  doc_id?: string | null;
  markdown_report: string;
  pdf_url?: string | null;
  metrics: Record<string, any>;
  created_at: string;
}
