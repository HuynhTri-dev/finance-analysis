/**
 * @file page.tsx
 * @description Main dashboard page component for AI Finance Pro, featuring real-time market data,
 * interactive technical charts, order-book and foreign flow analytics, AI stock analysis, and PDF reports
 * with responsive layout and collapsible sidebars.
 */

"use client";

import { useEffect, useState } from "react";
import { 
  Search, 
  Bot, 
  FileText, 
  TrendingUp, 
  TrendingDown, 
  RefreshCw, 
  X, 
  ExternalLink, 
  ArrowLeft,
  Activity,
  Layers,
  Globe,
  BarChart3,
  Compass,
  DollarSign,
  PanelLeftClose,
  PanelLeftOpen,
  PanelRightClose,
  PanelRightOpen,
  Sparkles,
  Menu
} from "lucide-react";
import { marketApi, watchlistApi, analyzeApi, newsApi, reportApi } from "@/lib/api";
import { 
  ComposedChart, 
  Line, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  ReferenceLine
} from "recharts";
import { format } from "date-fns";

export default function Home() {
  const [overview, setOverview] = useState<any>(null);
  const [watchlist, setWatchlist] = useState<any[]>([]);
  const [watchlistQuotes, setWatchlistQuotes] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);
  const [activeSymbol, setActiveSymbol] = useState<string | null>("FPT");
  const [symbolDetail, setSymbolDetail] = useState<any>(null);
  const [selectedTimeframe, setSelectedTimeframe] = useState<string>("3M");
  const [showMAs, setShowMAs] = useState<boolean>(true);
  const [news, setNews] = useState<any[]>([]);
  const [searchSymbol, setSearchSymbol] = useState("");
  const [agentLogs, setAgentLogs] = useState<{ type: string; content: string }[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [sidebarTab, setSidebarTab] = useState<"chat" | "pdf">("chat");
  const [pdfReports, setPdfReports] = useState<any[]>([]);
  const [selectedPdf, setSelectedPdf] = useState<string | null>(null);
  const [loadingPdfs, setLoadingPdfs] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);

  // Layout sidebar collapsible states
  const [isLeftSidebarOpen, setIsLeftSidebarOpen] = useState(true);
  const [isRightSidebarOpen, setIsRightSidebarOpen] = useState(true);

  /**
   * Fetches list of generated PDF reports from the backend
   * @returns {Promise<void>}
   */
  const fetchPdfReports = async (): Promise<void> => {
    try {
      setLoadingPdfs(true);
      const data = await reportApi.listReports();
      setPdfReports(data.reports || []);
    } catch (err) {
      console.error("Failed to fetch PDF reports:", err);
    } finally {
      setLoadingPdfs(false);
    }
  };

  /**
   * Fetches current prices and changes for symbols in the watchlist
   * @param {string[]} symbols - Array of stock ticker symbols
   * @returns {Promise<void>}
   */
  const fetchWatchlistQuotes = async (symbols: string[]): Promise<void> => {
    if (!symbols || symbols.length === 0) return;
    try {
      const quotes = await marketApi.getBatchQuotes(symbols);
      const quoteMap: Record<string, any> = {};
      quotes.forEach((q: any) => {
        quoteMap[q.symbol] = q;
      });
      setWatchlistQuotes(quoteMap);
    } catch (err) {
      console.error("Failed to fetch watchlist quotes:", err);
    }
  };

  /**
   * Loads initial market indices, overview stats, and user watchlist
   * @param {boolean} showLoading - Whether to trigger full-screen loading state
   * @returns {Promise<void>}
   */
  const fetchInitialData = async (showLoading = true): Promise<void> => {
    try {
      if (showLoading) setLoading(true);
      const [overviewData, watchlistData] = await Promise.all([
        marketApi.getOverview(),
        watchlistApi.getWatchlist()
      ]);
      setOverview(overviewData);
      
      const symbolsRaw = watchlistData.symbols || watchlistData || [];
      const symbolsClean = symbolsRaw.map((item: any) => typeof item === 'string' ? item : item.symbol);
      setWatchlist(symbolsRaw);
      
      if (symbolsClean.length > 0) {
        fetchWatchlistQuotes(symbolsClean);
      }
    } catch (error) {
      console.error("Error fetching initial data:", error);
    } finally {
      if (showLoading) setLoading(false);
    }
  };

  /**
   * Loads deep analytics, technical metrics, order book, and related news for a single stock
   * @param {string} symbol - Stock ticker symbol (e.g. FPT, CMG, VNM)
   * @param {string} timeframe - Selected timeframe (1M, 3M, 6M, 1Y)
   * @returns {Promise<void>}
   */
  const loadSymbolDetail = async (symbol: string, timeframe: string = "3M"): Promise<void> => {
    try {
      setLoadingDetail(true);
      const [detailData, newsData] = await Promise.all([
        marketApi.getDetail(symbol, timeframe),
        newsApi.getNewsBySymbol(symbol)
      ]);
      setSymbolDetail(detailData);
      const articles = Array.isArray(newsData) ? newsData : (newsData?.articles || newsData?.news || []);
      setNews(articles);
    } catch (e) {
      console.error("Error loading symbol detail:", e);
    } finally {
      setLoadingDetail(false);
    }
  };

  useEffect(() => {
    fetchInitialData();
    fetchPdfReports();
    if (activeSymbol) {
      loadSymbolDetail(activeSymbol, selectedTimeframe);
    }

    // Auto-adjust default sidebar visibility based on initial screen width
    if (typeof window !== "undefined" && window.innerWidth < 1280) {
      setIsRightSidebarOpen(false);
    }
    if (typeof window !== "undefined" && window.innerWidth < 768) {
      setIsLeftSidebarOpen(false);
    }
  }, []);

  const handleSelectSymbol = (symbol: string) => {
    setActiveSymbol(symbol);
    loadSymbolDetail(symbol, selectedTimeframe);
    // On small screens, collapse left sidebar after selecting
    if (typeof window !== "undefined" && window.innerWidth < 768) {
      setIsLeftSidebarOpen(false);
    }
  };

  const handleTimeframeChange = (tf: string) => {
    setSelectedTimeframe(tf);
    if (activeSymbol) {
      loadSymbolDetail(activeSymbol, tf);
    }
  };

  const handleAddWatchlist = async (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && searchSymbol.trim() !== "") {
      const sym = searchSymbol.trim().toUpperCase();
      try {
        await watchlistApi.addWatchlist(sym);
        setSearchSymbol("");
        handleSelectSymbol(sym);
        fetchInitialData(false);
      } catch (err) {
        console.error("Failed to add symbol:", err);
      }
    }
  };

  const handleRemoveWatchlist = async (e: React.MouseEvent, symbol: string) => {
    e.stopPropagation();
    try {
      await watchlistApi.removeWatchlist(symbol);
      if (activeSymbol === symbol) setActiveSymbol(null);
      fetchInitialData(false);
    } catch (err) {
      console.error("Failed to remove symbol:", err);
    }
  };

  /**
   * Triggers multi-dimensional AI analysis for the selected symbol or general market
   * Automatically opens the right sidebar to display live generation logs
   */
  const handleAnalyze = async () => {
    setIsRightSidebarOpen(true);
    setSidebarTab("chat");
    setIsAnalyzing(true);
    setAgentLogs([{ type: "system", content: "Đang tiến hành phân tích dữ liệu chuyên sâu..." }]);
    
    try {
      let res;
      if (activeSymbol) {
        res = await analyzeApi.analyzeSymbol(activeSymbol);
      } else {
        res = await analyzeApi.analyzeOverview();
      }
      
      setAgentLogs(prev => [
        ...prev,
        { type: "markdown", content: res.data?.markdown_content || "Không có nội dung phân tích." }
      ]);
      
      if (res.data?.pdf_url) {
         setAgentLogs(prev => [
          ...prev,
          { type: "pdf", content: res.data.pdf_url }
        ]);
        fetchPdfReports();
      }
    } catch (e) {
      setAgentLogs(prev => [
        ...prev,
        { type: "error", content: "Lỗi trong quá trình AI phân tích." }
      ]);
    } finally {
      setIsAnalyzing(false);
    }
  };

  /**
   * Triggers quick PDF report generation and reveals right panel preview
   */
  const handleGenerateQuickReport = async () => {
    if (!activeSymbol) return;
    setIsRightSidebarOpen(true);
    setSidebarTab("chat");
    try {
      setAgentLogs([{ type: "system", content: `Đang tạo PDF báo cáo nhanh cho mã ${activeSymbol}...` }]);
      const res = await reportApi.generateQuickReport(activeSymbol);
      if (res.pdf_url) {
        setAgentLogs(prev => [...prev, { type: "pdf", content: res.pdf_url }]);
        fetchPdfReports();
      }
    } catch (e) {
      setAgentLogs(prev => [...prev, { type: "error", content: "Lỗi khi tạo PDF báo cáo." }]);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-[#0E1117]">
        <div className="animate-pulse flex flex-col items-center">
          <div className="h-10 w-10 bg-blue-600 rounded-full mb-4 animate-ping"></div>
          <div className="text-gray-300 font-medium">Đang khởi tạo dữ liệu thị trường...</div>
        </div>
      </div>
    );
  }

  const quote = symbolDetail?.quote || {};
  const technicals = symbolDetail?.technicals || {};
  const orderBook = symbolDetail?.order_book || { bids: [], offers: [] };
  const foreignFlow = symbolDetail?.foreign_flow || {};
  const orderFlow = symbolDetail?.order_flow || {};
  const chartRecords = symbolDetail?.history?.records || symbolDetail?.records || [];

  const isPriceUp = (quote.change || 0) > 0;
  const isPriceDown = (quote.change || 0) < 0;
  const priceColorClass = isPriceUp ? "text-emerald-400" : isPriceDown ? "text-rose-400" : "text-amber-400";
  const priceBgClass = isPriceUp ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" : isPriceDown ? "bg-rose-500/10 text-rose-400 border-rose-500/20" : "bg-amber-500/10 text-amber-400 border-amber-500/20";

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#0D1117] text-gray-200 relative">
      
      {/* Mobile Overlay Backdrop for Left Sidebar */}
      {isLeftSidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/60 z-20 md:hidden backdrop-blur-sm transition-opacity"
          onClick={() => setIsLeftSidebarOpen(false)}
        />
      )}

      {/* 1. Left Sidebar: Watchlist & Search (Collapsible) */}
      <aside 
        className={`${
          isLeftSidebarOpen ? "w-72 lg:w-80 translate-x-0" : "w-0 -translate-x-full md:translate-x-0 md:w-0 border-r-0"
        } bg-[#161B22] border-r border-[#30363D] flex flex-col flex-shrink-0 transition-all duration-300 ease-in-out overflow-hidden z-30 md:static fixed inset-y-0 left-0 shadow-2xl md:shadow-none`}
      >
        <div className="w-72 lg:w-80 flex flex-col h-full">
          {/* Header Brand + Collapse Button */}
          <div className="p-4 border-b border-[#30363D] flex items-center justify-between bg-[#161B22]">
            <div 
              className="flex items-center space-x-3 cursor-pointer hover:opacity-80 transition-opacity"
              onClick={() => setActiveSymbol(null)}
            >
              <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
                <TrendingUp className="text-white w-5 h-5" />
              </div>
              <div>
                <div className="font-bold text-base text-gray-100 tracking-wide">AI Finance Pro</div>
                <div className="text-[11px] text-gray-400">Stock Dashboard & Analytics</div>
              </div>
            </div>

            <button 
              onClick={() => setIsLeftSidebarOpen(false)}
              className="p-1.5 text-gray-400 hover:text-gray-200 hover:bg-[#21262D] rounded-lg transition-colors"
              title="Thu gọn danh mục (Collapse)"
            >
              <PanelLeftClose size={18} />
            </button>
          </div>

          {/* Search Input */}
          <div className="p-3">
            <div className="relative">
              <Search className="absolute left-3 top-2.5 text-gray-400 w-4 h-4" />
              <input 
                type="text" 
                placeholder="Nhập mã (VD: FPT, VNM, HPG) & Enter..."
                value={searchSymbol}
                onChange={(e) => setSearchSymbol(e.target.value)}
                onKeyDown={handleAddWatchlist}
                className="w-full pl-9 pr-3 py-2 bg-[#0D1117] border border-[#30363D] rounded-lg text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500 transition-colors uppercase"
              />
            </div>
          </div>

          {/* Watchlist Section */}
          <div className="flex-1 overflow-y-auto px-3 py-2">
            <div className="flex justify-between items-center px-1 pb-2 text-[11px] font-semibold text-gray-400 tracking-wider">
              <span>DANH MỤC THEO DÕI</span>
              <button 
                onClick={() => fetchInitialData(false)}
                className="hover:text-gray-200 transition-colors p-1 rounded hover:bg-[#21262D]"
                title="Làm mới giá"
              >
                <RefreshCw size={12} />
              </button>
            </div>

            <div className="space-y-1.5">
              {watchlist.map((item: any) => {
                const sym = typeof item === 'string' ? item : item.symbol;
                const isSelected = activeSymbol === sym;
                const q = watchlistQuotes[sym] || {};
                const price = q.price ? q.price.toLocaleString() : "--";
                const changePct = q.change_pct !== undefined ? q.change_pct : null;
                const isUp = (changePct || 0) > 0;
                const isDown = (changePct || 0) < 0;

                return (
                  <div 
                    key={sym} 
                    onClick={() => handleSelectSymbol(sym)}
                    className={`group relative flex justify-between items-center p-2.5 rounded-lg cursor-pointer transition-all border ${
                      isSelected 
                        ? "bg-[#21262D] border-blue-500/60 shadow-sm" 
                        : "bg-[#161B22] border-transparent hover:bg-[#1F242C] hover:border-[#30363D]"
                    }`}
                  >
                    <div className="flex flex-col min-w-0 pr-2">
                      <span className="font-bold text-sm text-gray-100">{sym}</span>
                      <span className="text-[10px] text-gray-400 truncate max-w-[110px]">
                        {q.company_name || "Cổ phiếu"}
                      </span>
                    </div>

                    <div className="flex items-center space-x-2 flex-shrink-0">
                      <div className="text-right">
                        <div className="text-xs font-semibold text-gray-200">{price}</div>
                        {changePct !== null ? (
                          <div className={`text-[11px] font-medium ${isUp ? "text-emerald-400" : isDown ? "text-rose-400" : "text-amber-400"}`}>
                            {isUp ? "+" : ""}{changePct}%
                          </div>
                        ) : (
                          <div className="text-[11px] text-gray-500">--%</div>
                        )}
                      </div>

                      <button 
                        onClick={(e) => handleRemoveWatchlist(e, sym)}
                        className="opacity-0 group-hover:opacity-100 p-1 text-gray-500 hover:text-rose-400 hover:bg-[#30363D] rounded transition-all"
                        title="Xóa khỏi danh sách"
                      >
                        <X size={13} />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Footer info */}
          <div className="p-3 border-t border-[#30363D] flex items-center justify-between text-[11px] text-gray-400 bg-[#161B22]">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
              <span>Dữ liệu trực tiếp (Realtime)</span>
            </div>
            <span className="text-gray-500">v2.0</span>
          </div>
        </div>
      </aside>

      {/* 2. Main Dashboard Panel (Flex-1, Fluid & Auto-Expanding) */}
      <main className="flex-1 flex flex-col overflow-hidden bg-[#0D1117] min-w-0 transition-all duration-300">
        
        {/* Top Header Bar */}
        <header className="h-14 border-b border-[#30363D] flex items-center justify-between px-4 sm:px-6 bg-[#161B22]/80 backdrop-blur z-10">
          <div className="flex items-center space-x-3 min-w-0">
            {/* Toggle Left Sidebar Button (when collapsed) */}
            {!isLeftSidebarOpen && (
              <button
                onClick={() => setIsLeftSidebarOpen(true)}
                className="p-2 text-gray-400 hover:text-gray-100 hover:bg-[#21262D] rounded-lg transition-colors border border-[#30363D] flex items-center space-x-1.5"
                title="Mở danh mục theo dõi"
              >
                <PanelLeftOpen size={16} className="text-blue-400" />
                <span className="text-xs font-semibold hidden md:inline text-gray-300">Mã cổ phiếu</span>
              </button>
            )}

            <div className="flex items-center space-x-2 truncate">
              <span className="text-xs text-gray-400 hidden sm:inline">Trạng thái:</span>
              <span className="text-xs sm:text-sm font-semibold text-gray-200 truncate">
                {activeSymbol ? `Dashboard Cổ Phiếu: ${activeSymbol}` : "Tổng Quan Thị Trường Việt Nam"}
              </span>
            </div>
          </div>

          {/* Right Header Actions */}
          <div className="flex items-center space-x-3 flex-shrink-0">
            <div className="text-xs text-gray-400 hidden lg:block">
              {format(new Date(), "dd/MM/yyyy HH:mm")}
            </div>

            {/* Toggle Right AI / PDF Panel Button */}
            <button
              onClick={() => setIsRightSidebarOpen(!isRightSidebarOpen)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-2 border transition-all ${
                isRightSidebarOpen
                  ? "bg-blue-600/15 text-blue-400 border-blue-500/40 shadow-sm"
                  : "bg-[#21262D] text-gray-300 border-[#30363D] hover:bg-[#30363D] hover:text-white"
              }`}
              title={isRightSidebarOpen ? "Thu gọn thanh AI & Báo Cáo" : "Mở Trợ lý AI & Báo Cáo"}
            >
              <Bot size={15} className={isAnalyzing ? "text-emerald-400 animate-spin" : "text-blue-400"} />
              <span>Trợ Lý AI & PDF</span>
              {pdfReports.length > 0 && (
                <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-blue-600 text-white font-bold">
                  {pdfReports.length}
                </span>
              )}
              {isRightSidebarOpen ? (
                <PanelRightClose size={14} className="hidden sm:inline opacity-70" />
              ) : (
                <PanelRightOpen size={14} className="hidden sm:inline opacity-70" />
              )}
            </button>
          </div>
        </header>

        {/* Main Content Area */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">

          {/* VIEW 1: MARKET OVERVIEW (When no symbol is chosen) */}
          {!activeSymbol && overview && (
            <div className="space-y-6 max-w-7xl mx-auto">
              {/* Indices overview cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {overview.indexes?.map((idx: any) => {
                  const isPositive = (idx.change || 0) >= 0;
                  return (
                    <div key={idx.symbol} className="p-4 rounded-xl bg-[#161B22] border border-[#30363D] shadow-sm hover:border-gray-600 transition-all">
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm font-bold text-gray-200">{idx.symbol}</span>
                        <span className={`text-xs font-semibold px-2 py-0.5 rounded-md border ${
                          isPositive ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" : "bg-rose-500/10 text-rose-400 border-rose-500/20"
                        }`}>
                          {idx.change_pct !== null ? `${isPositive ? '+' : ''}${idx.change_pct}%` : 'N/A'}
                        </span>
                      </div>
                      <div className="text-2xl font-bold text-gray-100">
                        {idx.close ? idx.close.toLocaleString() : '--'}
                      </div>
                      <div className={`text-xs ${isPositive ? 'text-emerald-400' : 'text-rose-400'} flex items-center mt-1`}>
                        {isPositive ? '+' : ''}{idx.change || 0} điểm
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* AI Market Overview Banner */}
              <div className="p-5 rounded-xl bg-gradient-to-r from-blue-900/30 via-indigo-900/20 to-purple-900/30 border border-blue-500/30 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-md">
                <div>
                  <h3 className="font-semibold text-gray-100 text-sm flex items-center space-x-2">
                    <Bot className="text-blue-400 w-4 h-4" />
                    <span>AI Phân Tích Tổng Quan Thị Trường</span>
                  </h3>
                  <p className="text-xs text-gray-400 mt-1">
                    Đánh giá toàn cảnh thị trường chứng khoán, dòng tiền khối ngoại và khuyến nghị tổng quan.
                  </p>
                </div>
                <button 
                  onClick={handleAnalyze} 
                  disabled={isAnalyzing}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-lg shadow-blue-500/30 transition-all flex items-center space-x-2 disabled:opacity-50 flex-shrink-0"
                >
                  <Bot size={15} />
                  <span>{isAnalyzing ? "Đang phân tích..." : "Phân tích AI Ngay"}</span>
                </button>
              </div>

              {/* Top Movers */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-[#161B22] rounded-xl border border-[#30363D] p-5">
                  <h3 className="text-sm font-semibold text-gray-200 mb-3 flex items-center space-x-2">
                    <TrendingUp size={16} className="text-emerald-400" />
                    <span>Top Cổ Phiếu Tăng Giá</span>
                  </h3>
                  <div className="divide-y divide-[#30363D]/60">
                    {overview.top_gainers?.slice(0, 6).map((stock: any) => (
                      <div 
                        key={stock.symbol} 
                        onClick={() => handleSelectSymbol(stock.symbol)} 
                        className="py-2.5 flex justify-between items-center cursor-pointer hover:bg-[#21262D] px-2 rounded-lg transition-colors"
                      >
                        <span className="font-bold text-xs text-gray-200">{stock.symbol}</span>
                        <div className="text-right">
                          <div className="text-xs text-gray-300 font-medium">{stock.close?.toLocaleString()}</div>
                          <div className="text-[11px] text-emerald-400">+{stock.change_pct}%</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-[#161B22] rounded-xl border border-[#30363D] p-5">
                  <h3 className="text-sm font-semibold text-gray-200 mb-3 flex items-center space-x-2">
                    <Activity size={16} className="text-blue-400" />
                    <span>Top Thanh Khoản Thị Trường</span>
                  </h3>
                  <div className="divide-y divide-[#30363D]/60">
                    {overview.top_volume?.slice(0, 6).map((stock: any) => (
                      <div 
                        key={stock.symbol} 
                        onClick={() => handleSelectSymbol(stock.symbol)} 
                        className="py-2.5 flex justify-between items-center cursor-pointer hover:bg-[#21262D] px-2 rounded-lg transition-colors"
                      >
                        <span className="font-bold text-xs text-gray-200">{stock.symbol}</span>
                        <div className="text-right">
                          <div className="text-xs text-gray-300 font-medium">{stock.close?.toLocaleString()}</div>
                          <div className="text-[11px] text-gray-400">Vol: {stock.volume?.toLocaleString()}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* VIEW 2: INDIVIDUAL STOCK DASHBOARD (Fluid Grid) */}
          {activeSymbol && (
            <div className="space-y-5 max-w-[1600px] mx-auto min-w-0">
              
              {/* 1. Top Header Row with Hero Price & Action Buttons */}
              <div className="flex flex-wrap items-center justify-between gap-4 bg-[#161B22] border border-[#30363D] p-4 sm:p-5 rounded-xl shadow-sm">
                <div className="flex items-center space-x-3 sm:space-x-4 min-w-0">
                  <div className="w-11 h-11 sm:w-12 sm:h-12 rounded-xl bg-blue-600/10 border border-blue-500/30 flex items-center justify-center font-black text-lg sm:text-xl text-blue-400 flex-shrink-0">
                    {activeSymbol}
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center space-x-2">
                      <h1 className="text-xl sm:text-2xl font-bold text-gray-100">{activeSymbol}</h1>
                      <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-[#21262D] text-gray-300 border border-[#30363D]">
                        {symbolDetail?.exchange || "HOSE"}
                      </span>
                    </div>
                    <p className="text-xs text-gray-400 mt-0.5 truncate">{symbolDetail?.company_name || "Công ty Cổ phần"}</p>
                  </div>
                </div>

                {/* Hero Price Display & Quick Triggers */}
                <div className="flex flex-wrap items-center gap-4 sm:gap-6">
                  <div className="text-left sm:text-right">
                    <div className={`text-2xl sm:text-3xl font-extrabold ${priceColorClass}`}>
                      {quote.price ? quote.price.toLocaleString() : "--"} <span className="text-sm font-normal text-gray-400">đ</span>
                    </div>
                    <div className="flex items-center justify-start sm:justify-end space-x-2 mt-1">
                      <span className={`px-2 py-0.5 rounded text-xs font-semibold border ${priceBgClass}`}>
                        {isPriceUp ? "+" : ""}{quote.change ? quote.change.toLocaleString() : "0"} ({isPriceUp ? "+" : ""}{quote.change_pct || 0}%)
                      </span>
                      <span className="text-[11px] text-gray-400">TC: {quote.ref_price?.toLocaleString() || "--"}</span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center space-x-2 sm:space-x-2.5">
                    <button 
                      onClick={handleGenerateQuickReport}
                      disabled={isAnalyzing}
                      className="px-3 sm:px-3.5 py-2 bg-[#21262D] hover:bg-[#30363D] text-gray-200 text-xs font-semibold rounded-lg border border-[#30363D] transition-colors flex items-center space-x-1.5 disabled:opacity-50"
                    >
                      <FileText size={14} className="text-blue-400" />
                      <span>Tải PDF Nhanh</span>
                    </button>
                    
                    <button 
                      onClick={handleAnalyze} 
                      disabled={isAnalyzing}
                      className="px-3 sm:px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-md shadow-blue-500/20 transition-all flex items-center space-x-1.5 disabled:opacity-50"
                    >
                      <Bot size={14} className={isAnalyzing ? "animate-bounce" : ""} />
                      <span>{isAnalyzing ? "Đang phân tích..." : "AI Đánh Giá Mã Này"}</span>
                    </button>
                  </div>
                </div>
              </div>

              {/* 2. Key Stats Strip (Responsive Grid: 2 / 4 / 8 columns) */}
              <div className="grid grid-cols-2 sm:grid-cols-4 xl:grid-cols-8 gap-2.5">
                <div className="p-3 bg-[#161B22] border border-[#30363D] rounded-lg min-w-0">
                  <div className="text-[10px] text-gray-400 uppercase font-semibold truncate">Giá Trần</div>
                  <div className="text-xs sm:text-sm font-bold text-purple-400 mt-1 truncate">{quote.ceiling?.toLocaleString() || "--"}</div>
                </div>
                <div className="p-3 bg-[#161B22] border border-[#30363D] rounded-lg min-w-0">
                  <div className="text-[10px] text-gray-400 uppercase font-semibold truncate">Giá Sàn</div>
                  <div className="text-xs sm:text-sm font-bold text-cyan-400 mt-1 truncate">{quote.floor?.toLocaleString() || "--"}</div>
                </div>
                <div className="p-3 bg-[#161B22] border border-[#30363D] rounded-lg min-w-0">
                  <div className="text-[10px] text-gray-400 uppercase font-semibold truncate">Mở Cửa</div>
                  <div className="text-xs sm:text-sm font-bold text-gray-200 mt-1 truncate">{quote.open?.toLocaleString() || "--"}</div>
                </div>
                <div className="p-3 bg-[#161B22] border border-[#30363D] rounded-lg min-w-0">
                  <div className="text-[10px] text-gray-400 uppercase font-semibold truncate">Cao Nhất</div>
                  <div className="text-xs sm:text-sm font-bold text-emerald-400 mt-1 truncate">{quote.high?.toLocaleString() || "--"}</div>
                </div>
                <div className="p-3 bg-[#161B22] border border-[#30363D] rounded-lg min-w-0">
                  <div className="text-[10px] text-gray-400 uppercase font-semibold truncate">Thấp Nhất</div>
                  <div className="text-xs sm:text-sm font-bold text-rose-400 mt-1 truncate">{quote.low?.toLocaleString() || "--"}</div>
                </div>
                <div className="p-3 bg-[#161B22] border border-[#30363D] rounded-lg min-w-0">
                  <div className="text-[10px] text-gray-400 uppercase font-semibold truncate">Trung Bình</div>
                  <div className="text-xs sm:text-sm font-bold text-amber-400 mt-1 truncate">{quote.avg_price ? Math.round(quote.avg_price).toLocaleString() : "--"}</div>
                </div>
                <div className="p-3 bg-[#161B22] border border-[#30363D] rounded-lg min-w-0">
                  <div className="text-[10px] text-gray-400 uppercase font-semibold truncate">KL Khớp Lệnh</div>
                  <div className="text-xs sm:text-sm font-bold text-gray-200 mt-1 truncate">{quote.total_volume?.toLocaleString() || "--"}</div>
                </div>
                <div className="p-3 bg-[#161B22] border border-[#30363D] rounded-lg min-w-0">
                  <div className="text-[10px] text-gray-400 uppercase font-semibold truncate">Vốn Hóa</div>
                  <div className="text-xs sm:text-sm font-bold text-blue-400 mt-1 truncate">
                    {quote.market_cap ? `${(quote.market_cap / 1_000_000_000_000).toFixed(1)} Tỷ` : "--"}
                  </div>
                </div>
              </div>

              {/* 3. Interactive Chart Component */}
              <div className="bg-[#161B22] border border-[#30363D] rounded-xl p-4 sm:p-5 shadow-sm">
                <div className="flex flex-wrap items-center justify-between pb-4 mb-3 border-b border-[#30363D]/80 gap-3">
                  <div className="flex items-center space-x-3">
                    <div className="flex items-center space-x-1.5 text-xs font-semibold text-gray-200">
                      <BarChart3 size={16} className="text-blue-400" />
                      <span>Biểu Đồ Kỹ Thuật (OHLCV & Moving Averages)</span>
                    </div>

                    <button 
                      onClick={() => setShowMAs(!showMAs)}
                      className={`text-[11px] px-2 py-0.5 rounded border transition-colors ${
                        showMAs ? "bg-blue-500/20 text-blue-400 border-blue-500/40" : "bg-[#21262D] text-gray-400 border-[#30363D]"
                      }`}
                    >
                      MA20 / MA50
                    </button>
                  </div>

                  {/* Timeframe Buttons */}
                  <div className="flex items-center space-x-1 bg-[#0D1117] p-1 rounded-lg border border-[#30363D]">
                    {["1M", "3M", "6M", "1Y"].map((tf) => (
                      <button
                        key={tf}
                        onClick={() => handleTimeframeChange(tf)}
                        className={`px-2.5 sm:px-3 py-1 text-xs font-semibold rounded-md transition-all ${
                          selectedTimeframe === tf 
                            ? "bg-blue-600 text-white shadow" 
                            : "text-gray-400 hover:text-gray-200 hover:bg-[#21262D]"
                        }`}
                      >
                        {tf}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Chart Canvas */}
                <div className="h-[340px] sm:h-[380px] w-full">
                  {loadingDetail ? (
                    <div className="flex items-center justify-center h-full text-xs text-gray-400">
                      <RefreshCw className="animate-spin mr-2" size={16} />
                      Đang cập nhật biểu đồ...
                    </div>
                  ) : chartRecords && chartRecords.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <ComposedChart data={chartRecords} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#21262D" vertical={false} />
                        <XAxis 
                          dataKey="time" 
                          tickFormatter={(timeStr) => {
                            try { return format(new Date(timeStr), "dd/MM"); } catch { return timeStr; }
                          }}
                          stroke="#6E7681"
                          tick={{ fontSize: 11 }}
                          minTickGap={25}
                        />
                        <YAxis 
                          yAxisId="price" 
                          domain={['auto', 'auto']} 
                          stroke="#6E7681" 
                          tick={{ fontSize: 11 }}
                          tickFormatter={(val) => (val >= 1000 ? `${(val / 1000).toFixed(0)}k` : val)}
                        />
                        <YAxis yAxisId="vol" orientation="right" domain={[0, 'dataMax * 3']} hide />
                        
                        <Tooltip 
                          content={({ active, payload, label }) => {
                            if (active && payload && payload.length) {
                              const d = payload[0].payload;
                              return (
                                <div className="bg-[#161B22] border border-[#30363D] p-3 rounded-lg shadow-xl text-xs space-y-1 z-50">
                                  <div className="font-bold text-gray-200 border-b border-[#30363D] pb-1">
                                    {d.time ? format(new Date(d.time), "dd/MM/yyyy") : label}
                                  </div>
                                  <div className="grid grid-cols-2 gap-x-4 gap-y-0.5 text-[11px] pt-1">
                                    <span className="text-gray-400">Đóng cửa:</span>
                                    <span className="font-bold text-emerald-400 text-right">{d.close?.toLocaleString()}</span>
                                    <span className="text-gray-400">Mở cửa:</span>
                                    <span className="text-gray-200 text-right">{d.open?.toLocaleString()}</span>
                                    <span className="text-gray-400">Cao nhất:</span>
                                    <span className="text-emerald-300 text-right">{d.high?.toLocaleString()}</span>
                                    <span className="text-gray-400">Thấp nhất:</span>
                                    <span className="text-rose-300 text-right">{d.low?.toLocaleString()}</span>
                                    <span className="text-gray-400">Khối lượng:</span>
                                    <span className="text-blue-400 text-right">{d.volume?.toLocaleString()}</span>
                                    {d.ma20 && (
                                      <>
                                        <span className="text-amber-400">MA20:</span>
                                        <span className="text-amber-300 text-right">{d.ma20?.toLocaleString()}</span>
                                      </>
                                    )}
                                    {d.ma50 && (
                                      <>
                                        <span className="text-purple-400">MA50:</span>
                                        <span className="text-purple-300 text-right">{d.ma50?.toLocaleString()}</span>
                                      </>
                                    )}
                                  </div>
                                </div>
                              );
                            }
                            return null;
                          }}
                        />

                        {/* Volume Bar */}
                        <Bar yAxisId="vol" dataKey="volume" fill="#238636" opacity={0.35} radius={[2, 2, 0, 0]} />

                        {/* Moving Average Overlays */}
                        {showMAs && (
                          <>
                            <Line yAxisId="price" type="monotone" dataKey="ma20" stroke="#F59E0B" dot={false} strokeWidth={1.5} name="MA20" />
                            <Line yAxisId="price" type="monotone" dataKey="ma50" stroke="#8B5CF6" dot={false} strokeWidth={1.5} name="MA50" />
                          </>
                        )}

                        {/* Price Line */}
                        <Line 
                          yAxisId="price" 
                          type="monotone" 
                          dataKey="close" 
                          stroke="#38BDF8" 
                          dot={false} 
                          strokeWidth={2.5} 
                          name="Giá đóng cửa" 
                        />
                      </ComposedChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="flex flex-col items-center justify-center h-full text-gray-500">
                      <TrendingUp size={40} className="text-gray-700 mb-2" />
                      <p className="text-xs">Không có dữ liệu biểu đồ cho mã này trong khoảng thời gian đã chọn</p>
                    </div>
                  )}
                </div>
              </div>

              {/* 4. Four Analytics Cards Grid (Responsive: 1 / 2 / 4 columns) */}
              <div className="grid grid-cols-1 sm:grid-cols-2 2xl:grid-cols-4 gap-4">
                
                {/* Card 1: Sổ lệnh 3 mức giá (Order Book) */}
                <div className="bg-[#161B22] border border-[#30363D] rounded-xl p-4 flex flex-col justify-between min-w-0 shadow-sm">
                  <div>
                    <div className="flex items-center justify-between pb-2 border-b border-[#30363D]">
                      <span className="text-xs font-bold text-gray-200 flex items-center space-x-1.5 truncate">
                        <Layers size={14} className="text-blue-400 flex-shrink-0" />
                        <span className="truncate">Sổ Lệnh 3 Mức Giá</span>
                      </span>
                      <span className="text-[10px] text-gray-500 flex-shrink-0">Bids / Offers</span>
                    </div>

                    <div className="mt-3 space-y-2 text-[11px]">
                      {/* Bids */}
                      <div className="space-y-1">
                        <div className="text-[10px] text-emerald-400 font-semibold">Bên Mua (Bids)</div>
                        {orderBook.bids && orderBook.bids.length > 0 ? (
                          orderBook.bids.map((b: any, idx: number) => (
                            <div key={idx} className="flex justify-between items-center bg-emerald-500/5 px-2 py-1 rounded border border-emerald-500/10">
                              <span className="font-semibold text-emerald-400">{b.price ? b.price.toLocaleString() : "--"}</span>
                              <span className="text-gray-300 font-mono">{b.volume ? b.volume.toLocaleString() : "--"}</span>
                            </div>
                          ))
                        ) : (
                          <div className="text-gray-500 text-[10px]">Chưa có dữ liệu sổ lệnh</div>
                        )}
                      </div>

                      {/* Offers */}
                      <div className="space-y-1 pt-1">
                        <div className="text-[10px] text-rose-400 font-semibold">Bên Bán (Offers)</div>
                        {orderBook.offers && orderBook.offers.length > 0 ? (
                          orderBook.offers.map((o: any, idx: number) => (
                            <div key={idx} className="flex justify-between items-center bg-rose-500/5 px-2 py-1 rounded border border-rose-500/10">
                              <span className="font-semibold text-rose-400">{o.price ? o.price.toLocaleString() : "--"}</span>
                              <span className="text-gray-300 font-mono">{o.volume ? o.volume.toLocaleString() : "--"}</span>
                            </div>
                          ))
                        ) : (
                          <div className="text-gray-500 text-[10px]">Chưa có dữ liệu sổ lệnh</div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Card 2: Dòng tiền Khối Ngoại (Foreign Flow) */}
                <div className="bg-[#161B22] border border-[#30363D] rounded-xl p-4 flex flex-col justify-between min-w-0 shadow-sm">
                  <div>
                    <div className="flex items-center justify-between pb-2 border-b border-[#30363D]">
                      <span className="text-xs font-bold text-gray-200 flex items-center space-x-1.5 truncate">
                        <Globe size={14} className="text-cyan-400 flex-shrink-0" />
                        <span className="truncate">Dòng Tiền Khối Ngoại</span>
                      </span>
                      <span className="text-[10px] text-gray-500 flex-shrink-0">Foreign Net</span>
                    </div>

                    <div className="mt-3 space-y-2.5 text-xs">
                      <div className="flex justify-between items-center">
                        <span className="text-gray-400">Mua ngoại:</span>
                        <span className="font-semibold text-emerald-400">
                          {foreignFlow.buy_val ? `${(foreignFlow.buy_val / 1_000_000_000).toFixed(2)} Tỷ` : "--"}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-gray-400">Bán ngoại:</span>
                        <span className="font-semibold text-rose-400">
                          {foreignFlow.sell_val ? `${(foreignFlow.sell_val / 1_000_000_000).toFixed(2)} Tỷ` : "--"}
                        </span>
                      </div>
                      <div className="flex justify-between items-center pt-1 border-t border-[#30363D]">
                        <span className="text-gray-300 font-semibold">Mua/Bán Ròng:</span>
                        <span className={`font-bold ${
                          (foreignFlow.net_val || 0) >= 0 ? "text-emerald-400" : "text-rose-400"
                        }`}>
                          {(foreignFlow.net_val || 0) >= 0 ? "+" : ""}
                          {foreignFlow.net_val ? `${(foreignFlow.net_val / 1_000_000_000).toFixed(2)} Tỷ` : "--"}
                        </span>
                      </div>
                      <div className="flex justify-between items-center pt-1 border-t border-[#30363D]/60 text-[11px]">
                        <span className="text-gray-500">Room ngoại còn lại:</span>
                        <span className="font-mono text-gray-300">
                          {foreignFlow.room ? `${(foreignFlow.room / 1_000_000).toFixed(1)}M cp` : "--"}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Card 3: Tương quan Cung - Cầu (Order Flow) */}
                <div className="bg-[#161B22] border border-[#30363D] rounded-xl p-4 flex flex-col justify-between min-w-0 shadow-sm">
                  <div>
                    <div className="flex items-center justify-between pb-2 border-b border-[#30363D]">
                      <span className="text-xs font-bold text-gray-200 flex items-center space-x-1.5 truncate">
                        <Activity size={14} className="text-purple-400 flex-shrink-0" />
                        <span className="truncate">Áp Lực Cung - Cầu</span>
                      </span>
                      <span className="text-[10px] text-gray-500 flex-shrink-0">Order Pressure</span>
                    </div>

                    <div className="mt-3 space-y-2.5 text-xs">
                      <div className="flex justify-between items-center">
                        <span className="text-gray-400">Khớp Mua chủ động:</span>
                        <span className="font-semibold text-emerald-400">
                          {orderFlow.active_buy_vol ? orderFlow.active_buy_vol.toLocaleString() : "--"}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-gray-400">Khớp Bán chủ động:</span>
                        <span className="font-semibold text-rose-400">
                          {orderFlow.active_sell_vol ? orderFlow.active_sell_vol.toLocaleString() : "--"}
                        </span>
                      </div>
                      
                      {/* Pressure Bar */}
                      <div className="pt-1">
                        <div className="flex justify-between text-[10px] text-gray-400 mb-1">
                          <span>Mua: {orderFlow.buy_pressure_pct || 50}%</span>
                          <span>Bán: {100 - (orderFlow.buy_pressure_pct || 50)}%</span>
                        </div>
                        <div className="w-full h-2 rounded-full bg-rose-500/40 overflow-hidden flex">
                          <div 
                            className="bg-emerald-500 h-full transition-all duration-500" 
                            style={{ width: `${orderFlow.buy_pressure_pct || 50}%` }}
                          ></div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Card 4: Chỉ Số Kỹ Thuật & Tín Hiệu (Technicals) */}
                <div className="bg-[#161B22] border border-[#30363D] rounded-xl p-4 flex flex-col justify-between min-w-0 shadow-sm">
                  <div>
                    <div className="flex items-center justify-between pb-2 border-b border-[#30363D]">
                      <span className="text-xs font-bold text-gray-200 flex items-center space-x-1.5 truncate">
                        <Compass size={14} className="text-amber-400 flex-shrink-0" />
                        <span className="truncate">Chỉ Số Kỹ Thuật</span>
                      </span>
                      <span className="text-[10px] text-gray-500 flex-shrink-0">Signals</span>
                    </div>

                    <div className="mt-3 space-y-2 text-xs">
                      <div className="flex justify-between items-center">
                        <span className="text-gray-400">RSI (14):</span>
                        <span className={`font-bold ${
                          (technicals.rsi_14 || 50) > 70 ? "text-rose-400" : (technicals.rsi_14 || 50) < 30 ? "text-emerald-400" : "text-amber-400"
                        }`}>
                          {technicals.rsi_14 !== null ? technicals.rsi_14 : "--"}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-gray-400">Đỉnh 52 Tuần:</span>
                        <span className="text-gray-200 font-medium">
                          {technicals.high_52w?.toLocaleString() || "--"} ({technicals.dist_52w_high_pct || 0}%)
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-gray-400">Đáy 52 Tuần:</span>
                        <span className="text-gray-200 font-medium">
                          {technicals.low_52w?.toLocaleString() || "--"} (+{technicals.dist_52w_low_pct || 0}%)
                        </span>
                      </div>
                      <div className="pt-1.5 border-t border-[#30363D]">
                        <div className="text-[10px] text-gray-400 mb-1">Tín hiệu kỹ thuật:</div>
                        <div className="px-2 py-1 rounded bg-blue-500/10 border border-blue-500/20 text-blue-400 text-center font-semibold text-[11px]">
                          {technicals.signal || "Trung lập"}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

              </div>

              {/* 5. News Section */}
              <div className="bg-[#161B22] rounded-xl border border-[#30363D] overflow-hidden shadow-sm">
                <div className="px-5 py-3.5 border-b border-[#30363D] bg-[#161B22] flex items-center justify-between">
                  <h3 className="text-xs font-semibold text-gray-100 uppercase tracking-wider">
                    Tin Tức & Báo Cáo Doanh Nghiệp Liên Quan ({news.length})
                  </h3>
                </div>
                <div className="divide-y divide-[#30363D]/60">
                  {news && news.length > 0 ? (
                    news.slice(0, 8).map((n: any) => (
                      <a 
                        key={n.id || n.url} 
                        href={n.url || n.link} 
                        target="_blank" 
                        rel="noreferrer" 
                        className="block p-4 hover:bg-[#21262D] transition-colors"
                      >
                        <h4 className="text-xs font-semibold text-blue-400 mb-1 leading-snug hover:underline">
                          {n.title}
                        </h4>
                        <p className="text-xs text-gray-400 mb-2 line-clamp-2 leading-relaxed">
                          {n.summary}
                        </p>
                        <div className="flex justify-between items-center text-[11px] text-gray-500">
                          <span className="font-medium text-gray-400">{n.source || "Finance Feed"}</span>
                          <span>{n.published_at ? format(new Date(n.published_at), "dd/MM/yyyy HH:mm") : ''}</span>
                        </div>
                      </a>
                    ))
                  ) : (
                    <div className="p-6 text-center text-gray-500 text-xs italic">
                      Chưa có tin tức cập nhật cho mã cổ phiếu này trong cơ sở dữ liệu.
                    </div>
                  )}
                </div>
              </div>

            </div>
          )}

        </div>
      </main>

      {/* Mobile Overlay Backdrop for Right Sidebar */}
      {isRightSidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/60 z-20 xl:hidden backdrop-blur-sm transition-opacity"
          onClick={() => setIsRightSidebarOpen(false)}
        />
      )}

      {/* 3. Right Sidebar: AI Assistant & PDF Report Tabs (Collapsible) */}
      <aside 
        className={`${
          isRightSidebarOpen ? "w-full sm:w-[400px] xl:w-[420px] translate-x-0" : "w-0 translate-x-full xl:translate-x-0 xl:w-0 border-l-0"
        } bg-[#161B22] border-l border-[#30363D] flex flex-col flex-shrink-0 transition-all duration-300 ease-in-out overflow-hidden z-30 fixed xl:static inset-y-0 right-0 shadow-2xl xl:shadow-none`}
      >
        <div className="w-full sm:w-[400px] xl:w-[420px] flex flex-col h-full">
          {/* Header Controls */}
          <div className="h-14 border-b border-[#30363D] flex items-center justify-between px-4 bg-[#161B22]">
            <div className="flex items-center space-x-2">
              <div className={`w-2.5 h-2.5 rounded-full ${isAnalyzing ? 'bg-emerald-500 animate-ping' : 'bg-blue-500'}`}></div>
              <h2 className="text-sm font-semibold text-gray-100">Trợ Lý Phân Tích AI</h2>
            </div>
            
            <div className="flex items-center space-x-2">
              <div className="flex space-x-1 bg-[#0D1117] p-1 rounded-lg border border-[#30363D]">
                <button 
                  onClick={() => setSidebarTab("chat")}
                  className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
                    sidebarTab === "chat" ? "bg-blue-600 text-white shadow" : "text-gray-400 hover:text-gray-200"
                  }`}
                >
                  Phân Tích
                </button>
                <button 
                  onClick={() => setSidebarTab("pdf")}
                  className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
                    sidebarTab === "pdf" ? "bg-blue-600 text-white shadow" : "text-gray-400 hover:text-gray-200"
                  }`}
                >
                  Báo Cáo PDF ({pdfReports.length})
                </button>
              </div>

              {/* Close / Collapse Right Sidebar Button */}
              <button 
                onClick={() => setIsRightSidebarOpen(false)}
                className="p-1.5 text-gray-400 hover:text-gray-200 hover:bg-[#21262D] rounded-lg transition-colors"
                title="Thu gọn Trợ lý AI (Collapse)"
              >
                <PanelRightClose size={18} />
              </button>
            </div>
          </div>

          {/* Body Content */}
          {sidebarTab === "chat" ? (
            <div className="flex-1 overflow-y-auto p-4 space-y-3.5">
              {agentLogs.length === 0 ? (
                <div className="text-center py-16 flex flex-col items-center justify-center space-y-3">
                  <div className="w-12 h-12 rounded-2xl bg-blue-600/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
                    <Bot size={24} />
                  </div>
                  <p className="text-gray-400 text-xs px-6 leading-relaxed">
                    Nhấn nút <strong className="text-gray-200">&quot;AI Đánh Giá Mã Này&quot;</strong> hoặc <strong className="text-gray-200">&quot;Tải PDF Nhanh&quot;</strong> để hệ thống tiến hành phân tích chuyên sâu đa chiều.
                  </p>
                </div>
              ) : (
                agentLogs.map((log, i) => (
                  <div 
                    key={i} 
                    className={`p-4 rounded-xl border text-xs leading-relaxed ${
                      log.type === 'system' 
                        ? 'bg-[#0D1117] border-[#30363D] text-gray-400' 
                        : log.type === 'error' 
                        ? 'bg-rose-950/20 border-rose-900/50 text-rose-300' 
                        : 'bg-[#1C2128] border-[#30363D] text-gray-200'
                    }`}
                  >
                    {log.type === 'markdown' ? (
                       <div className="whitespace-pre-wrap font-sans text-gray-200 space-y-2">{log.content}</div>
                    ) : log.type === 'pdf' ? (
                       <div className="flex flex-col space-y-2">
                         <div className="text-xs text-gray-300 font-semibold">Báo cáo PDF đã được khởi tạo thành công:</div>
                         <div className="flex items-center space-x-2 pt-1">
                           <button 
                             onClick={() => { setSelectedPdf(log.content); setSidebarTab("pdf"); }}
                             className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg flex items-center space-x-1.5 transition-colors shadow"
                           >
                             <FileText size={14} />
                             <span>Xem Trực Tiếp</span>
                           </button>
                           <a 
                             href={log.content} 
                             target="_blank" 
                             rel="noreferrer" 
                             className="px-3 py-1.5 bg-[#21262D] hover:bg-[#30363D] text-gray-300 text-xs font-semibold rounded-lg flex items-center space-x-1.5 transition-colors border border-[#30363D]"
                           >
                             <ExternalLink size={14} />
                             <span>Mở Tab Mới</span>
                           </a>
                         </div>
                       </div>
                    ) : (
                      <span>{log.content}</span>
                    )}
                  </div>
                ))
              )}
              {isAnalyzing && (
                <div className="p-4 rounded-xl bg-[#0D1117] border border-[#30363D] flex items-center space-x-3">
                   <div className="flex space-x-1">
                     <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
                     <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.15s' }}></div>
                     <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.3s' }}></div>
                   </div>
                   <span className="text-xs text-gray-400">AI Agent đang đọc dữ liệu tài chính & tổng hợp báo cáo...</span>
                </div>
              )}
            </div>
          ) : (
            <div className="flex-1 flex flex-col overflow-hidden">
              {selectedPdf ? (
                <div className="flex-1 flex flex-col h-full bg-[#0D1117]">
                  <div className="p-2 border-b border-[#30363D] bg-[#161B22] flex items-center justify-between">
                    <button 
                      onClick={() => setSelectedPdf(null)} 
                      className="flex items-center space-x-1 text-xs text-gray-300 hover:text-white px-2.5 py-1.5 rounded-md bg-[#21262D] hover:bg-[#30363D] transition-colors"
                    >
                      <ArrowLeft size={14} />
                      <span>Quay lại danh sách</span>
                    </button>
                    <a 
                      href={selectedPdf} 
                      target="_blank" 
                      rel="noreferrer" 
                      className="flex items-center space-x-1 text-xs text-blue-400 hover:underline px-2 py-1"
                    >
                      <ExternalLink size={14} />
                      <span>Mở tab riêng</span>
                    </a>
                  </div>
                  <iframe src={selectedPdf} className="w-full flex-1 border-none" title="PDF Preview" />
                </div>
              ) : (
                <div className="flex-1 overflow-y-auto p-4 space-y-3">
                  <div className="flex items-center justify-between pb-2 border-b border-[#30363D]">
                    <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                      Tất cả báo cáo đã tạo ({pdfReports.length})
                    </div>
                    <button 
                      onClick={fetchPdfReports} 
                      disabled={loadingPdfs}
                      className="p-1 text-gray-400 hover:text-gray-200 rounded hover:bg-[#21262D] transition-colors"
                      title="Làm mới danh sách"
                    >
                      <RefreshCw size={14} className={loadingPdfs ? "animate-spin" : ""} />
                    </button>
                  </div>
                  
                  {loadingPdfs && pdfReports.length === 0 ? (
                    <div className="text-center py-12 text-xs text-gray-500">Đang tải danh sách báo cáo...</div>
                  ) : pdfReports.length === 0 ? (
                    <div className="text-center py-16 flex flex-col items-center justify-center space-y-3">
                      <FileText size={36} className="text-gray-700" />
                      <p className="text-gray-500 text-xs px-4">Chưa có báo cáo PDF nào. Nhấn &quot;Tải PDF Nhanh&quot; hoặc &quot;AI Đánh giá Mã này&quot; để tạo báo cáo.</p>
                    </div>
                  ) : (
                    pdfReports.map((report, idx) => (
                      <div 
                        key={idx} 
                        className="p-3.5 rounded-xl bg-[#0D1117] border border-[#30363D] hover:border-gray-600 transition-all flex flex-col space-y-2.5"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex items-start space-x-2.5">
                            <div className="w-8 h-8 rounded-lg bg-rose-950/40 border border-rose-800/40 text-rose-400 flex items-center justify-center flex-shrink-0 mt-0.5">
                              <FileText size={16} />
                            </div>
                            <div className="min-w-0">
                              <h4 className="text-xs font-semibold text-gray-200 line-clamp-1">
                                {report.filename.replace(".pdf", "")}
                              </h4>
                              <div className="flex items-center space-x-2 text-[11px] text-gray-500 mt-0.5">
                                <span>{report.size_kb ? `${report.size_kb} KB` : ''}</span>
                                <span>•</span>
                                <span>{report.created_at ? format(new Date(report.created_at), "dd/MM/yyyy HH:mm") : ''}</span>
                              </div>
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center space-x-2 pt-1 border-t border-[#30363D]/60">
                          <button 
                            onClick={() => setSelectedPdf(report.url)}
                            className="flex-1 py-1.5 bg-[#21262D] hover:bg-[#30363D] text-blue-400 text-xs font-semibold rounded-lg flex items-center justify-center space-x-1.5 transition-colors"
                          >
                            <FileText size={13} />
                            <span>Xem ngay</span>
                          </button>
                          <a 
                            href={report.url} 
                            target="_blank" 
                            rel="noreferrer" 
                            className="px-2.5 py-1.5 bg-[#21262D] hover:bg-[#30363D] text-gray-300 text-xs rounded-lg flex items-center justify-center transition-colors border border-[#30363D]"
                            title="Mở tab mới"
                          >
                            <ExternalLink size={13} />
                          </a>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </aside>
    </div>
  );
}
