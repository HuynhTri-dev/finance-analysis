/**
 * @file MarketOverview.tsx
 * @description General Vietnam stock market overview view displaying key index cards (VNINDEX, HNXINDEX, UPCOMINDEX),
 * AI Market-Wide Analysis banner, top gainers, and top liquidity volume tables.
 */

"use client";

import React from "react";
import { Bot, TrendingUp, Activity } from "lucide-react";

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
              className="p-4 rounded-xl bg-[#161B22] border border-[#30363D] shadow-sm hover:border-gray-600 transition-all"
            >
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-bold text-gray-200">{idx.symbol}</span>
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
              <div className="text-2xl font-bold text-gray-100">
                {idx.close ? idx.close.toLocaleString() : "--"}
              </div>
              <div
                className={`text-xs ${
                  isPositive ? "text-emerald-400" : "text-rose-400"
                } flex items-center mt-1`}
              >
                {isPositive ? "+" : ""}
                {idx.change || 0} điểm
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
    </div>
  );
};
