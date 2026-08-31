import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api';


export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

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
    const response = await apiClient.post('/analyze/overview');
    return response.data;
  },
  analyzeSymbol: async (symbol: string) => {
    const response = await apiClient.post('/analyze/detail', { symbol });
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

