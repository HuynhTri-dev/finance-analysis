/**
 * @file LeftSidebar.tsx
 * @description Collapsible left sidebar containing the brand header, stock ticker search input,
 * dynamic user watchlist with realtime quotes, and status indicators.
 */

"use client";

import React from "react";
import { TrendingUp, PanelLeftClose, Search, RefreshCw, X, Briefcase } from "lucide-react";

export interface LeftSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  watchlist: any[];
  watchlistQuotes: Record<string, any>;
  activeSymbol: string | null;
  onSelectSymbol: (symbol: string | null) => void;
  searchSymbol: string;
  onSearchChange: (value: string) => void;
  onAddWatchlist: (e: React.KeyboardEvent<HTMLInputElement>) => void;
  onRemoveWatchlist: (e: React.MouseEvent, symbol: string) => void;
  onRefreshQuotes: () => void;
  holdings?: string[];
  onToggleHolding?: (symbol: string) => void;
}

export const LeftSidebar: React.FC<LeftSidebarProps> = ({
  isOpen,
  onClose,
  watchlist = [],
  watchlistQuotes = {},
  activeSymbol = null,
  onSelectSymbol,
  searchSymbol = "",
  onSearchChange,
  onAddWatchlist,
  onRemoveWatchlist,
  onRefreshQuotes,
  holdings = [],
  onToggleHolding = () => {},
}) => {
  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-20 md:hidden backdrop-blur-sm transition-opacity"
          onClick={onClose}
        />
      )}

      <aside
        className={`${
          isOpen
            ? "w-72 lg:w-80 translate-x-0"
            : "w-0 -translate-x-full md:translate-x-0 md:w-0 border-r-0"
        } bg-[#161B22] border-r border-[#30363D] flex flex-col flex-shrink-0 transition-all duration-300 ease-in-out overflow-hidden z-30 md:static fixed inset-y-0 left-0 shadow-2xl md:shadow-none`}
      >
        <div className="w-72 lg:w-80 flex flex-col h-full">
          {/* Header Brand + Collapse Button */}
          <div className="p-4 border-b border-[#30363D] flex items-center justify-between bg-[#161B22]">
            <div
              className="flex items-center space-x-3 cursor-pointer hover:opacity-80 transition-opacity"
              onClick={() => onSelectSymbol(null)}
            >
              <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
                <TrendingUp className="text-white w-5 h-5" />
              </div>
              <div>
                <div className="font-bold text-base text-gray-100 tracking-wide">
                  AI Finance Pro
                </div>
                <div className="text-[11px] text-gray-400">Stock Dashboard & Analytics</div>
              </div>
            </div>

            <button
              onClick={onClose}
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
                onChange={(e) => onSearchChange(e.target.value)}
                onKeyDown={onAddWatchlist}
                className="w-full pl-9 pr-3 py-2 bg-[#0D1117] border border-[#30363D] rounded-lg text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500 transition-colors uppercase"
              />
            </div>
          </div>

          {/* Watchlist Section */}
          <div className="flex-1 overflow-y-auto px-3 py-2">
            <div className="flex justify-between items-center px-1 pb-2 text-[11px] font-semibold text-gray-400 tracking-wider">
              <span>DANH MỤC THEO DÕI</span>
              <button
                onClick={onRefreshQuotes}
                className="hover:text-gray-200 transition-colors p-1 rounded hover:bg-[#21262D]"
                title="Làm mới giá"
              >
                <RefreshCw size={12} />
              </button>
            </div>

            <div className="space-y-1.5">
              {watchlist.map((item: any) => {
                const sym = typeof item === "string" ? item : item.symbol;
                const isSelected = activeSymbol === sym;
                const q = watchlistQuotes[sym] || {};
                const price = q.price ? q.price.toLocaleString() : "--";
                const changePct = q.change_pct !== undefined ? q.change_pct : null;
                const isUp = (changePct || 0) > 0;
                const isDown = (changePct || 0) < 0;
                const isHolding = holdings.includes(sym);

                return (
                  <div
                    key={sym}
                    onClick={() => onSelectSymbol(sym)}
                    className={`group relative flex justify-between items-center p-2.5 rounded-lg cursor-pointer transition-all border ${
                      isSelected
                        ? "bg-[#21262D] border-blue-500/60 shadow-sm"
                        : "bg-[#161B22] border-transparent hover:bg-[#1F242C] hover:border-[#30363D]"
                    }`}
                  >
                    <div className="flex flex-col min-w-0 pr-2">
                      <span className="font-bold text-sm text-gray-100 flex items-center gap-1.5">
                        {sym}
                        {isHolding && (
                          <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[9px] font-semibold px-1 py-0.2 rounded-md">
                            Đang nắm giữ
                          </span>
                        )}
                      </span>
                      <span className="text-[10px] text-gray-400 truncate max-w-[110px]">
                        {q.company_name || "Cổ phiếu"}
                      </span>
                    </div>

                    <div className="flex items-center space-x-2 flex-shrink-0">
                      <div className="text-right">
                        <div className="text-xs font-semibold text-gray-200">{price}</div>
                        {changePct !== null ? (
                          <div
                            className={`text-[11px] font-medium ${
                              isUp ? "text-emerald-400" : isDown ? "text-rose-400" : "text-amber-400"
                            }`}
                          >
                            {isUp ? "+" : ""}
                            {changePct}%
                          </div>
                        ) : (
                          <div className="text-[11px] text-gray-500">--%</div>
                        )}
                      </div>

                      <div className="flex items-center space-x-1">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onToggleHolding(sym);
                          }}
                          className={`p-1 rounded hover:bg-[#30363D] transition-all ${
                            isHolding 
                              ? "text-emerald-400 opacity-100" 
                              : "opacity-0 group-hover:opacity-100 text-gray-500 hover:text-emerald-400"
                          }`}
                          title={isHolding ? "Hủy đánh dấu đang nắm giữ" : "Đánh dấu đang nắm giữ"}
                        >
                          <Briefcase size={12} />
                        </button>

                        <button
                          onClick={(e) => onRemoveWatchlist(e, sym)}
                          className="opacity-0 group-hover:opacity-100 p-1 text-gray-500 hover:text-rose-400 hover:bg-[#30363D] rounded transition-all"
                          title="Xóa khỏi danh sách"
                        >
                          <X size={13} />
                        </button>
                      </div>
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
    </>
  );
};
