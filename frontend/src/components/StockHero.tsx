/**
 * @file StockHero.tsx
 * @description Hero banner for the selected stock displaying symbol ticker, exchange, company name,
 * real-time price, price delta badges, and quick action trigger buttons (PDF generation & AI assessment).
 */

"use client";

import React from "react";
import { Bot, FileText, RefreshCw } from "lucide-react";

export interface StockHeroProps {
  activeSymbol: string;
  symbolDetail: any;
  isGeneratingQuickPdf: boolean;
  isAnalyzing: boolean;
  onGenerateQuickReport: () => void;
  onAnalyze: () => void;
}

export const StockHero: React.FC<StockHeroProps> = ({
  activeSymbol,
  symbolDetail,
  isGeneratingQuickPdf,
  isAnalyzing,
  onGenerateQuickReport,
  onAnalyze,
}) => {
  const quote = symbolDetail?.quote || {};
  const isPriceUp = (quote.change || 0) > 0;
  const isPriceDown = (quote.change || 0) < 0;
  const priceColorClass = isPriceUp
    ? "text-emerald-400"
    : isPriceDown
    ? "text-rose-400"
    : "text-amber-400";
  const priceBgClass = isPriceUp
    ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
    : isPriceDown
    ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
    : "bg-amber-500/10 text-amber-400 border-amber-500/20";

  return (
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
          <p className="text-xs text-gray-400 mt-0.5 truncate">
            {symbolDetail?.company_name || "Công ty Cổ phần"}
          </p>
        </div>
      </div>

      {/* Hero Price Display & Quick Triggers */}
      <div className="flex flex-wrap items-center gap-4 sm:gap-6">
        <div className="text-left sm:text-right">
          <div className={`text-2xl sm:text-3xl font-extrabold ${priceColorClass}`}>
            {quote.price ? quote.price.toLocaleString() : "--"}{" "}
            <span className="text-sm font-normal text-gray-400">đ</span>
          </div>
          <div className="flex items-center justify-start sm:justify-end space-x-2 mt-1">
            <span className={`px-2 py-0.5 rounded text-xs font-semibold border ${priceBgClass}`}>
              {isPriceUp ? "+" : ""}
              {quote.change ? quote.change.toLocaleString() : "0"} ({isPriceUp ? "+" : ""}
              {quote.change_pct || 0}%)
            </span>
            <span className="text-[11px] text-gray-400">
              TC: {quote.ref_price?.toLocaleString() || "--"}
            </span>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center space-x-2 sm:space-x-2.5">
          <button
            onClick={onGenerateQuickReport}
            disabled={isGeneratingQuickPdf || isAnalyzing}
            className={`px-3 sm:px-3.5 py-2 text-xs font-semibold rounded-lg border transition-all flex items-center space-x-1.5 ${
              isGeneratingQuickPdf
                ? "bg-blue-600/20 text-blue-300 border-blue-500/40 cursor-not-allowed opacity-90 shadow-sm"
                : "bg-[#21262D] hover:bg-[#30363D] text-gray-200 border-[#30363D] disabled:opacity-50"
            }`}
            title={
              isGeneratingQuickPdf
                ? "Hệ thống đang tổng hợp dữ liệu và tạo PDF..."
                : "Tạo và tải báo cáo PDF nhanh"
            }
          >
            {isGeneratingQuickPdf ? (
              <RefreshCw size={14} className="text-blue-400 animate-spin" />
            ) : (
              <FileText size={14} className="text-blue-400" />
            )}
            <span>{isGeneratingQuickPdf ? "Đang tạo PDF..." : "Tải PDF Nhanh"}</span>
          </button>

          <button
            onClick={onAnalyze}
            disabled={isAnalyzing}
            className="px-3 sm:px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-md shadow-blue-500/20 transition-all flex items-center space-x-1.5 disabled:opacity-50"
          >
            <Bot size={14} className={isAnalyzing ? "animate-bounce" : ""} />
            <span>{isAnalyzing ? "Đang phân tích..." : "AI Đánh Giá Mã Này"}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
