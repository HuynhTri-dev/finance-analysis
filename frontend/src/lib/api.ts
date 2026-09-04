import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Fallback interceptor: if localhost fails with Network Error (common macOS IPv6 issue), retry with 127.0.0.1
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.message === 'Network Error' && error.config && !error.config._retry) {
      error.config._retry = true;
      if (error.config.baseURL?.includes('localhost')) {
        error.config.baseURL = error.config.baseURL.replace('localhost', '127.0.0.1');
        return axios(error.config);
      } else if (error.config.baseURL?.includes('127.0.0.1')) {
        error.config.baseURL = error.config.baseURL.replace('127.0.0.1', 'localhost');
        return axios(error.config);
      }
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  login: async (username: string, password: string) => {
    const response = await apiClient.post('/auth/login', { username, password });
    return response.data;
  },
};

export const marketApi = {
  getOverview: async () => {
    const response = await apiClient.get('/market/overview');
    return response.data;
  },
  getDetail: async (symbol: string, timeframe: string = '3M') => {
    const response = await apiClient.get(`/market/stock/${symbol}`, {
      params: { timeframe },
    });
    return response.data;
  },
  getBatchQuotes: async (symbols: string[]) => {
    if (!symbols || symbols.length === 0) return [];
    const response = await apiClient.get('/market/quotes', {
      params: { symbols: symbols.join(',') },
    });
    return response.data;
  },
  getTopRecommendations: async (limit = 20) => {
    const response = await apiClient.get('/market/top-recommendations', { params: { limit } });
    return response.data;
  },
  triggerScan: async () => {
    const response = await apiClient.post('/market/scan-top');
    return response.data;
  },
};

export const watchlistApi = {
  getWatchlist: async () => {
    const response = await apiClient.get('/watchlist/');
    return response.data;
  },
  addWatchlist: async (symbol: string) => {
    const response = await apiClient.post('/watchlist/', { symbol });
    return response.data;
  },
  removeWatchlist: async (symbol: string) => {
    const response = await apiClient.delete(`/watchlist/${symbol}`);
    return response.data;
  },
  toggleHolding: async (symbol: string) => {
    const response = await apiClient.post(`/watchlist/${symbol}/toggle-holding`);
    return response.data;
  },
};

export const analyzeApi = {
  analyzeOverview: async () => {
    const response = await apiClient.post('/analyze/overview', {}, { timeout: 75000 });
    return response.data;
  },
  analyzeSymbol: async (symbol: string) => {
    const response = await apiClient.post('/analyze/detail', { symbol }, { timeout: 75000 });
    return response.data;
  },
  getRiskAnalysis: async (symbol: string, forceRefresh: boolean = false) => {
    const response = await apiClient.get(`/analyze/risk/${symbol}`, {
      params: { force_refresh: forceRefresh },
      timeout: 75000,
    });
    return response.data;
  },
};

export const reportApi = {
  generateQuickReport: async (symbol: string) => {
    const response = await apiClient.post(`/report/symbol/${symbol}`);
    return response.data;
  },
  listReports: async () => {
    const response = await apiClient.get('/report/list');
    return response.data;
  },
  deleteReport: async (reportId: string) => {
    const response = await apiClient.delete(`/report/${reportId}`);
    return response.data;
  },
};

export const newsApi = {
  getNews: async (type: 'macro' | 'watchlist' = 'macro', limit: number = 20) => {
    const response = await apiClient.get('/news/', {
      params: { type, limit },
    });
    return response.data;
  },
  getNewsBySymbol: async (symbol: string, limit: number = 10) => {
    const response = await apiClient.get(`/news/symbol/${symbol}`, {
      params: { limit },
    });
    return response.data;
  },
  crawlNow: async () => {
    const response = await apiClient.get('/news/crawl-now');
    return response.data;
  },
};

export const financeApi = {
  uploadBCTC: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post('/finance/upload-bctc', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  chatWithDocument: async (
    docId: string,
    query: string,
    chatHistory: { role: string; content: string }[] = []
  ) => {
    const response = await apiClient.post('/finance/chat', {
      doc_id: docId,
      query,
      chat_history: chatHistory,
    });
    return response.data;
  },
  generateComprehensiveReport: async (
    symbol: string,
    docId?: string | null,
    includePdfExport: boolean = true
  ) => {
    const response = await apiClient.post('/finance/comprehensive-report', {
      symbol,
      doc_id: docId || undefined,
      include_pdf_export: includePdfExport,
    });
    return response.data;
  },
  getSymbolRisk: async (symbol: string, forceRefresh: boolean = false) => {
    const response = await apiClient.get(`/finance/risk/${symbol}`, {
      params: { force_refresh: forceRefresh },
    });
    return response.data;
  },
};

/**
 * Resolves static or external URLs (e.g. Cloudflare R2 or local /static) to absolute URLs
 */
export const resolveFileUrl = (url?: string | null): string => {
  if (!url) return "";
  if (url.startsWith("http://") || url.startsWith("https://")) return url;
  const baseUrl =
    process.env.NEXT_PUBLIC_API_URL?.replace(/\/api\/?$/, "") ||
    "http://127.0.0.1:8001";
  return `${baseUrl}${url.startsWith("/") ? "" : "/"}${url}`;
};

export * from "./types";


