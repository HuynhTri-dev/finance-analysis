/**
 * @file page.tsx
 * @description Main dashboard page orchestrator for AI Finance Pro.
 * Coordinates market data fetching, watchlist management, AI analysis streams,
 * and responsive multi-column layout with modular sub-components.
 */

"use client";

import { useEffect, useState } from "react";
import {
  marketApi,
  watchlistApi,
  analyzeApi,
  newsApi,
  reportApi,
} from "@/lib/api";
import {
  LoadingScreen,
  LeftSidebar,
  Header,
  MarketOverview,
  StockHero,
  StockKeyStats,
  StockTechnicalChart,
  StockOrderFlowCards,
  StockNews,
  RightSidebar,
} from "@/components";

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
  const [isGeneratingQuickPdf, setIsGeneratingQuickPdf] = useState(false);
  const [deletingReportId, setDeletingReportId] = useState<string | null>(null);
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
   */
  const fetchInitialData = async (showLoading = true): Promise<void> => {
    try {
      if (showLoading) setLoading(true);
      const [overviewData, watchlistData] = await Promise.all([
        marketApi.getOverview(),
        watchlistApi.getWatchlist(),
      ]);
      setOverview(overviewData);

      const symbolsRaw = watchlistData.symbols || watchlistData || [];
      const symbolsClean = symbolsRaw.map((item: any) =>
        typeof item === "string" ? item : item.symbol
      );
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
   */
  const loadSymbolDetail = async (
    symbol: string,
    timeframe: string = "3M"
  ): Promise<void> => {
    try {
      setLoadingDetail(true);
      const [detailData, newsData] = await Promise.all([
        marketApi.getDetail(symbol, timeframe),
        newsApi.getNewsBySymbol(symbol),
      ]);
      setSymbolDetail(detailData);
      const articles = Array.isArray(newsData)
        ? newsData
        : newsData?.articles || newsData?.news || [];
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

    // Keyboard shortcut: Command + Shift + P (or Ctrl + Shift + P) to toggle AI / PDF tab
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && (e.key === "p" || e.key === "P")) {
        e.preventDefault();
        setIsRightSidebarOpen(true);
        setSidebarTab((prev) => (prev === "chat" ? "pdf" : "chat"));
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const handleSelectSymbol = (symbol: string | null) => {
    setActiveSymbol(symbol);
    if (symbol) {
      loadSymbolDetail(symbol, selectedTimeframe);
    }
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
   */
  const handleAnalyze = async () => {
    setIsRightSidebarOpen(true);
    setSidebarTab("chat");
    setIsAnalyzing(true);
    setAgentLogs([
      { type: "system", content: "Đang tiến hành phân tích dữ liệu chuyên sâu..." },
    ]);

    try {
      let res;
      if (activeSymbol) {
        res = await analyzeApi.analyzeSymbol(activeSymbol);
      } else {
        res = await analyzeApi.analyzeOverview();
      }

      setAgentLogs((prev) => [
        ...prev,
        {
          type: "markdown",
          content: res.data?.markdown_content || "Không có nội dung phân tích.",
        },
      ]);

      if (res.data?.pdf_url) {
        setAgentLogs((prev) => [...prev, { type: "pdf", content: res.data.pdf_url }]);
        fetchPdfReports();
      }
    } catch (e) {
      setAgentLogs((prev) => [
        ...prev,
        { type: "error", content: "Lỗi trong quá trình AI phân tích." },
      ]);
    } finally {
      setIsAnalyzing(false);
    }
  };

  /**
   * Triggers quick PDF report generation and reveals right panel preview
   */
  const handleGenerateQuickReport = async () => {
    if (!activeSymbol || isGeneratingQuickPdf || isAnalyzing) return;
    setIsGeneratingQuickPdf(true);
    setIsRightSidebarOpen(true);
    setSidebarTab("chat");
    try {
      setAgentLogs([
        {
          type: "system",
          content: `Đang tạo PDF báo cáo nhanh cho mã ${activeSymbol}...`,
        },
      ]);
      const res = await reportApi.generateQuickReport(activeSymbol);
      if (res.pdf_url) {
        setAgentLogs((prev) => [...prev, { type: "pdf", content: res.pdf_url }]);
        fetchPdfReports();
      }
    } catch (e) {
      setAgentLogs((prev) => [
        ...prev,
        { type: "error", content: "Lỗi khi tạo PDF báo cáo." },
      ]);
    } finally {
      setIsGeneratingQuickPdf(false);
    }
  };

  /**
   * Deletes a generated PDF report from PostgreSQL (Neon) and storage
   */
  const handleDeleteReport = async (e: React.MouseEvent, report: any) => {
    e.stopPropagation();
    const reportId = report.id || report.filename;
    if (!reportId) return;

    const confirmMsg = `Bạn có chắc chắn muốn xoá báo cáo "${
      report.title || report.filename
    }"?`;
    if (!window.confirm(confirmMsg)) {
      return;
    }

    try {
      setDeletingReportId(reportId);
      await reportApi.deleteReport(reportId);
      if (selectedPdf === report.url) {
        setSelectedPdf(null);
      }
      await fetchPdfReports();
    } catch (err) {
      console.error("Failed to delete report:", err);
      alert("Lỗi khi xoá báo cáo.");
    } finally {
      setDeletingReportId(null);
    }
  };

  if (loading) {
    return <LoadingScreen />;
  }

  const quote = symbolDetail?.quote || {};
  const technicals = symbolDetail?.technicals || {};
  const orderBook = symbolDetail?.order_book || { bids: [], offers: [] };
  const foreignFlow = symbolDetail?.foreign_flow || {};
  const orderFlow = symbolDetail?.order_flow || {};
  const chartRecords =
    symbolDetail?.history?.records || symbolDetail?.records || [];

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#0D1117] text-gray-200 relative">
      {/* 1. Left Sidebar: Watchlist & Search */}
      <LeftSidebar
        isOpen={isLeftSidebarOpen}
        onClose={() => setIsLeftSidebarOpen(false)}
        watchlist={watchlist}
        watchlistQuotes={watchlistQuotes}
        activeSymbol={activeSymbol}
        onSelectSymbol={handleSelectSymbol}
        searchSymbol={searchSymbol}
        onSearchChange={setSearchSymbol}
        onAddWatchlist={handleAddWatchlist}
        onRemoveWatchlist={handleRemoveWatchlist}
        onRefreshQuotes={() => fetchInitialData(false)}
      />

      {/* 2. Main Dashboard Panel */}
      <main className="flex-1 flex flex-col overflow-hidden bg-[#0D1117] min-w-0 transition-all duration-300">
        {/* Top Header Bar */}
        <Header
          isLeftSidebarOpen={isLeftSidebarOpen}
          onOpenLeftSidebar={() => setIsLeftSidebarOpen(true)}
          isRightSidebarOpen={isRightSidebarOpen}
          onToggleRightSidebar={() => setIsRightSidebarOpen(!isRightSidebarOpen)}
          activeSymbol={activeSymbol}
          pdfCount={pdfReports.length}
          isAnalyzing={isAnalyzing}
        />

        {/* Main Content Area */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
          {/* VIEW 1: MARKET OVERVIEW (When no symbol is chosen) */}
          {!activeSymbol && overview && (
            <MarketOverview
              overview={overview}
              isAnalyzing={isAnalyzing}
              onAnalyze={handleAnalyze}
              onSelectSymbol={handleSelectSymbol}
            />
          )}

          {/* VIEW 2: INDIVIDUAL STOCK DASHBOARD */}
          {activeSymbol && (
            <div className="space-y-5 max-w-[1600px] mx-auto min-w-0">
              {/* 1. Top Header Row with Hero Price & Action Buttons */}
              <StockHero
                activeSymbol={activeSymbol}
                symbolDetail={symbolDetail}
                isGeneratingQuickPdf={isGeneratingQuickPdf}
                isAnalyzing={isAnalyzing}
                onGenerateQuickReport={handleGenerateQuickReport}
                onAnalyze={handleAnalyze}
              />

              {/* 2. Key Stats Strip */}
              <StockKeyStats quote={quote} />

              {/* 3. Interactive Technical Chart */}
              <StockTechnicalChart
                chartRecords={chartRecords}
                loadingDetail={loadingDetail}
                selectedTimeframe={selectedTimeframe}
                onTimeframeChange={handleTimeframeChange}
                showMAs={showMAs}
                onToggleMAs={() => setShowMAs(!showMAs)}
              />

              {/* 4. Four Analytics Cards Grid */}
              <StockOrderFlowCards
                symbol={activeSymbol}
                chartRecords={chartRecords}
                quote={quote}
                orderBook={orderBook}
                foreignFlow={foreignFlow}
                orderFlow={orderFlow}
                technicals={technicals}
              />

              {/* 5. News Feed */}
              <StockNews news={news} />
            </div>
          )}
        </div>
      </main>

      {/* 3. Right Sidebar: AI Assistant & PDF Management */}
      <RightSidebar
        isOpen={isRightSidebarOpen}
        onClose={() => setIsRightSidebarOpen(false)}
        sidebarTab={sidebarTab}
        onTabChange={setSidebarTab}
        isAnalyzing={isAnalyzing}
        agentLogs={agentLogs}
        pdfReports={pdfReports}
        loadingPdfs={loadingPdfs}
        selectedPdf={selectedPdf}
        onSelectPdf={setSelectedPdf}
        onRefreshPdfs={fetchPdfReports}
        onDeleteReport={handleDeleteReport}
        deletingReportId={deletingReportId}
      />
    </div>
  );
}
