/**
 * @file StockHero.tsx
 * @description Hero banner for the selected stock displaying symbol ticker, exchange, company name,
 * real-time price, price delta badges, and quick action trigger buttons (PDF generation & AI assessment).
 * Also integrates holding status badges and sell recommendations for active holdings.
 */

"use client";

import React from "react";
import { Bot, FileText, RefreshCw, Sparkles, FileSpreadsheet } from "lucide-react";

export interface StockHeroProps {
  activeSymbol: string;
  symbolDetail: any;
  isGeneratingQuickPdf: boolean;
  isAnalyzing: boolean;
  onGenerateQuickReport: () => void;
  onAnalyze: () => void;
  isHolding?: boolean;
  recommendation?: any;
  onGenerateComprehensive?: () => void;
  isGeneratingComprehensive?: boolean;
  hasActiveDoc?: boolean;
  onOpenRightSidebar?: () => void;
}

export const StockHero: React.FC<StockHeroProps> = ({
  activeSymbol,
  symbolDetail,
  isGeneratingQuickPdf,
  isAnalyzing,
  onGenerateQuickReport,
  onAnalyze,
  isHolding = false,
  recommendation = null,
  onGenerateComprehensive,
  isGeneratingComprehensive = false,
  hasActiveDoc = false,
  onOpenRightSidebar,
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
      {/* Symbol details */}
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
            {isHolding && (
              <span className="px-2 py-0.5 rounded text-[10px] font-extrabold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 uppercase tracking-wider">
                Đang nắm giữ
              </span>
            )}
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
              {quote.change ? `${quote.change.toLocaleString()} đ` : "0 đ"}{" "}
              ({isPriceUp ? "+" : ""}{quote.change_pct || 0}%)
            </span>
            <span className="text-[11px] text-gray-400">
              TC: {quote.ref_price ? `${quote.ref_price.toLocaleString()} đ` : "--"}
            </span>
          </div>
        </div>

        {/* Actions */}
        <div className="flex flex-wrap items-center gap-2 sm:gap-2.5">
          {onGenerateComprehensive && (
            <button
              onClick={onGenerateComprehensive}
              disabled={isGeneratingComprehensive || isAnalyzing}
              className={`px-3 sm:px-3.5 py-2 text-xs font-semibold rounded-lg shadow-md transition-all flex items-center space-x-1.5 ${
                isGeneratingComprehensive
                  ? "bg-indigo-600/30 text-indigo-300 border border-indigo-500/40 cursor-not-allowed opacity-90"
                  : "bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-indigo-500/20 disabled:opacity-50"
              }`}
              title="Sinh báo cáo tài chính toàn cảnh 3 phần (Tài chính, Kỹ thuật, Khuyến nghị) kèm xuất PDF"
            >
              <Sparkles size={14} className={isGeneratingComprehensive ? "animate-spin" : "text-amber-300"} />
              <span>{isGeneratingComprehensive ? "Đang tạo báo cáo 3 phần..." : "Báo Cáo Toàn Cảnh"}</span>
            </button>
          )}

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

      {/* Quantitative recommendation warning banner */}
      {recommendation && (
        <div className={`w-full mt-3 p-3 rounded-lg border flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 text-xs transition-all ${
          recommendation.type === "BUY"
            ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
            : recommendation.type === "SELL"
            ? "bg-rose-500/10 border-rose-500/20 text-rose-400"
            : "bg-amber-500/10 border-amber-500/20 text-amber-400"
        }`}>
          <div>
            <div className="flex flex-wrap items-center gap-1.5 font-bold">
              <span>Đánh giá thuật toán:</span>
              <span className={`px-2 py-0.5 rounded text-[10px] font-extrabold uppercase border ${
                recommendation.type === "BUY"
                  ? "bg-emerald-500/20 border-emerald-500/30 text-emerald-400"
                  : recommendation.type === "SELL"
                  ? "bg-rose-500/20 border-rose-500/30 text-rose-400"
                  : "bg-amber-500/20 border-amber-500/30 text-amber-400"
              }`}>
                {recommendation.title}
              </span>
              {isHolding && (
                <span className="bg-blue-500/10 border border-blue-500/20 text-blue-400 text-[10px] px-1.5 py-0.5 rounded font-extrabold">
                  ĐANG NẮM GIỮ (PORTFOLIO)
                </span>
              )}
            </div>
            <p className="text-gray-300 leading-relaxed text-[11px] mt-1">
              {recommendation.reason}
            </p>
          </div>

          {isHolding && recommendation.type === "SELL" && (
            <div className="flex-shrink-0 bg-rose-600 text-white font-extrabold text-[10px] px-3 py-1.5 rounded-lg shadow-md uppercase tracking-wider animate-pulse">
              ⚠️ KHUYẾN NGHỊ BÁN (HẠ TỶ TRỌNG)
            </div>
          )}
        </div>
      )}
    </div>
  );
};
