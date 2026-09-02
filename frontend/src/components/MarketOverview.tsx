/**
 * @file MarketOverview.tsx
 * @description General Vietnam stock market overview view displaying key index cards (VNINDEX, HNXINDEX, UPCOMINDEX),
 * AI Market-Wide Analysis banner, top gainers, top liquidity volume tables, and a dynamic
 * "Top Buy Recommendations" table populated from the nightly backend quantitative scanner.
 */

"use client";

import React, { useEffect, useState, useCallback } from "react";
import { Bot, TrendingUp, Activity, RefreshCw, Flame, TrendingDown } from "lucide-react";
import { marketApi } from "@/lib/api";

export interface MarketOverviewProps {
  overview: any;
  isAnalyzing: boolean;
  onAnalyze: () => void;
  onSelectSymbol: (symbol: string) => void;
}

export const MarketOverview: React.FC<MarketOverviewProps> = ({
  overview,
  isAnalyzing,
  onAnalyze,
  onSelectSymbol,
}) => {
  const [topRecs, setTopRecs] = useState<any[]>([]);
  const [loadingRecs, setLoadingRecs] = useState(true);
  const [scanningNow, setScanningNow] = useState(false);
  const [lastScanned, setLastScanned] = useState<string | null>(null);

  const fetchTopRecs = useCallback(async () => {
    try {
      setLoadingRecs(true);
      const data = await marketApi.getTopRecommendations(20);
      setTopRecs(data?.items || []);
      if ((data?.items || []).length > 0) {
        const ts = data.items[0]?.recommended_date;
        if (ts) setLastScanned(new Date(ts).toLocaleString("vi-VN"));
      }
    } catch (err) {
      console.error("Failed to fetch top recommendations:", err);
      setTopRecs([]);
    } finally {
      setLoadingRecs(false);
    }
  }, []);

  useEffect(() => {
    fetchTopRecs();
  }, [fetchTopRecs]);

  const handleTriggerScan = async () => {
    if (scanningNow) return;
    setScanningNow(true);
    try {
      await marketApi.triggerScan();
      await fetchTopRecs();
    } catch (err) {
      console.error("Scan trigger failed:", err);
    } finally {
      setScanningNow(false);
    }
  };

  if (!overview) return null;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Indices overview cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {overview.indexes?.map((idx: any) => {
          const isPositive = (idx.change || 0) >= 0;
          return (
            <div
              key={idx.symbol}
              className="p-4 rounded-xl bg-[#161B22] border border-[#30363D] shadow-sm hover:border-gray-600 transition-all flex flex-col justify-between"
            >
              <div className="text-sm font-bold text-gray-200 mb-1">
                {idx.symbol}
              </div>
              <div className="text-2xl font-bold text-gray-100">
                {idx.close ? idx.close.toLocaleString() : "--"}
              </div>
              <div className="mt-2.5 flex flex-col gap-1.5 items-start">
                <div
                  className={`text-xs font-medium ${
                    isPositive ? "text-emerald-400" : "text-rose-400"
                  } flex items-center`}
                >
                  {isPositive ? "+" : ""}
                  {idx.change || 0} điểm
                </div>
                <span
                  className={`text-xs font-semibold px-2 py-0.5 rounded-md border ${
                    isPositive
                      ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                      : "bg-rose-500/10 text-rose-400 border-rose-500/20"
                  }`}
                >
                  {idx.change_pct !== null ? `${isPositive ? "+" : ""}${idx.change_pct}%` : "N/A"}
                </span>
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
          onClick={onAnalyze}
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
                onClick={() => onSelectSymbol(stock.symbol)}
                className="py-2.5 flex justify-between items-center cursor-pointer hover:bg-[#21262D] px-2 rounded-lg transition-colors"
              >
                <span className="font-bold text-xs text-gray-200">{stock.symbol}</span>
                <div className="text-right">
                  <div className="text-xs text-gray-300 font-medium">
                    {stock.close?.toLocaleString()}
                  </div>
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
                onClick={() => onSelectSymbol(stock.symbol)}
                className="py-2.5 flex justify-between items-center cursor-pointer hover:bg-[#21262D] px-2 rounded-lg transition-colors"
              >
                <span className="font-bold text-xs text-gray-200">{stock.symbol}</span>
                <div className="text-right">
                  <div className="text-xs text-gray-300 font-medium">
                    {stock.close?.toLocaleString()}
                  </div>
                  <div className="text-[11px] text-gray-400">
                    Vol: {stock.volume?.toLocaleString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Top BUY Recommendations — Dynamic from scanner API */}
      <div className="bg-[#161B22] rounded-xl border border-[#30363D] p-5 shadow-sm">
        <div className="flex flex-wrap justify-between items-start gap-3 mb-4">
          <div>
            <h3 className="text-sm font-semibold text-gray-200 flex items-center gap-2">
              <Bot size={16} className="text-blue-400" />
              Top Cổ Phiếu Khuyến Nghị Mua (Thuật Toán Định Lượng)
            </h3>
            <p className="text-[11px] text-gray-500 mt-1">
              Quét tự động toàn thị trường HOSE sau 15:30 ICT mỗi ngày dựa trên RSI quá bán · Bollinger Bands · MA Cross.
              {lastScanned && <span className="ml-2 text-gray-600">Cập nhật lần cuối: {lastScanned}</span>}
            </p>
          </div>
          <button
            onClick={handleTriggerScan}
            disabled={scanningNow || loadingRecs}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#21262D] hover:bg-[#30363D] border border-[#30363D] text-gray-300 text-[11px] font-semibold rounded-lg transition-all disabled:opacity-50"
            title="Chạy quét thủ công ngay (mất ~10-15 phút)"
          >
            <RefreshCw size={12} className={scanningNow ? "animate-spin" : ""} />
            {scanningNow ? "Đang quét..." : "Quét ngay"}
          </button>
        </div>

        {loadingRecs ? (
          <div className="py-10 flex flex-col items-center justify-center gap-3 text-gray-500">
            <RefreshCw size={22} className="animate-spin text-blue-400" />
            <span className="text-xs">Đang tải dữ liệu từ database...</span>
          </div>
        ) : topRecs.length === 0 ? (
          <div className="py-10 flex flex-col items-center justify-center gap-3 text-center text-gray-500">
            <Bot size={28} className="text-gray-600" />
            <p className="text-xs max-w-sm leading-relaxed">
              Chưa có dữ liệu quét. Thuật toán sẽ tự động chạy lúc <strong className="text-gray-400">15:30 ICT</strong> sau khi thị trường đóng cửa.
              <br />Hoặc bạn có thể nhấn <strong className="text-gray-400">"Quét ngay"</strong> để chạy thủ công.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left text-gray-400">
              <thead className="text-[10px] text-gray-500 uppercase tracking-wider bg-[#0D1117]/60 border-b border-[#30363D]">
                <tr>
                  <th className="py-2.5 px-3">Mã CP</th>
                  <th className="py-2.5 px-3">Giá</th>
                  <th className="py-2.5 px-3">RSI(14)</th>
                  <th className="py-2.5 px-3">Lý do lọc</th>
                  <th className="py-2.5 px-3 text-center">Streak FOMO</th>
                  <th className="py-2.5 px-3 text-center">Điểm TA</th>
                  <th className="py-2.5 px-3 text-center">Đánh giá</th>
                  <th className="py-2.5 px-3 text-right">Chi tiết</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#30363D]/40">
                {topRecs.map((rec) => {
                  const isMuaManh = rec.rating === "MUA MẠNH";
                  const ratingColor = isMuaManh
                    ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
                    : "text-emerald-400 bg-emerald-500/5 border-emerald-500/10";
                  const isHighFomo = rec.days_in_top >= 3;
                  const isVeryHighFomo = rec.days_in_top >= 5;

                  return (
                    <tr key={rec.symbol} className="hover:bg-[#21262D]/40 transition-colors">
                      <td className="py-3 px-3">
                        <div className="font-bold text-gray-200">{rec.symbol}</div>
                        <div className="text-[10px] text-gray-500">{rec.exchange}</div>
                      </td>
                      <td className="py-3 px-3 font-mono text-gray-300 tabular-nums">
                        {rec.price ? rec.price.toLocaleString("vi-VN") : "--"}
                      </td>
                      <td className="py-3 px-3">
                        {rec.rsi != null ? (
                          <span
                            className={`font-mono font-semibold ${
                              rec.rsi < 30
                                ? "text-emerald-300"
                                : rec.rsi < 40
                                ? "text-emerald-400"
                                : "text-gray-400"
                            }`}
                          >
                            {rec.rsi.toFixed(1)}
                          </span>
                        ) : (
                          "--"
                        )}
                      </td>
                      <td className="py-3 px-3 max-w-[220px]">
                        <p className="text-[11px] text-gray-400 leading-snug line-clamp-2" title={rec.reason}>
                          {rec.reason}
                        </p>
                      </td>
                      <td className="py-3 px-3 text-center">
                        <span
                          className={`inline-flex items-center gap-1 text-[10px] font-bold px-1.5 py-0.5 rounded border ${
                            isVeryHighFomo
                              ? "text-orange-300 bg-orange-500/10 border-orange-500/25"
                              : isHighFomo
                              ? "text-amber-400 bg-amber-500/10 border-amber-500/25"
                              : "text-gray-500 bg-transparent border-transparent"
                          }`}
                        >
                          {isHighFomo && <Flame size={9} />}
                          {rec.days_in_top} ngày
                        </span>
                      </td>
                      <td className="py-3 px-3 text-center">
                        <div className="flex items-center justify-center gap-0.5">
                          {Array.from({ length: 5 }).map((_, i) => (
                            <div
                              key={i}
                              className={`w-1.5 h-3 rounded-sm ${
                                i < rec.tech_score
                                  ? "bg-emerald-400"
                                  : "bg-[#30363D]"
                              }`}
                            />
                          ))}
                        </div>
                      </td>
                      <td className="py-3 px-3 text-center">
                        <span className={`text-[10px] font-extrabold px-2 py-0.5 rounded border ${ratingColor}`}>
                          {rec.rating}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-right">
                        <button
                          onClick={() => onSelectSymbol(rec.symbol)}
                          className="px-2.5 py-1 bg-blue-600/15 hover:bg-blue-600 text-blue-400 hover:text-white border border-blue-500/30 rounded text-[10px] font-semibold transition-all"
                        >
                          Xem →
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
