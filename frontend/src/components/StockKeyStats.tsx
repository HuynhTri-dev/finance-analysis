/**
 * @file StockKeyStats.tsx
 * @description 8-column responsive statistical summary card strip displaying Ceiling, Floor,
 * Open, High, Low, Average Price, Total Volume, and Market Capitalization for the selected stock.
 */

"use client";

import React from "react";

export interface StockKeyStatsProps {
  quote: any;
}

export const StockKeyStats: React.FC<StockKeyStatsProps> = ({ quote = {} }) => {
  return (
    <div className="@container w-full">
      <div className="grid grid-cols-2 sm:grid-cols-4 @[880px]:grid-cols-8 gap-2.5">
        <div className="p-3 bg-[#161B22] border border-[#30363D] rounded-lg min-w-0 flex flex-col justify-between">
          <div className="text-[10px] text-gray-400 uppercase font-semibold truncate">Giá Trần</div>
          <div className="text-xs sm:text-sm font-bold text-purple-400 mt-1 truncate">
            {quote.ceiling?.toLocaleString() || "--"}
          </div>
        </div>
        <div className="p-3 bg-[#161B22] border border-[#30363D] rounded-lg min-w-0 flex flex-col justify-between">
          <div className="text-[10px] text-gray-400 uppercase font-semibold truncate">Giá Sàn</div>
          <div className="text-xs sm:text-sm font-bold text-cyan-400 mt-1 truncate">
            {quote.floor?.toLocaleString() || "--"}
          </div>
        </div>
        <div className="p-3 bg-[#161B22] border border-[#30363D] rounded-lg min-w-0 flex flex-col justify-between">
          <div className="text-[10px] text-gray-400 uppercase font-semibold truncate">Mở Cửa</div>
          <div className="text-xs sm:text-sm font-bold text-gray-200 mt-1 truncate">
            {quote.open?.toLocaleString() || "--"}
          </div>
        </div>
        <div className="p-3 bg-[#161B22] border border-[#30363D] rounded-lg min-w-0 flex flex-col justify-between">
          <div className="text-[10px] text-gray-400 uppercase font-semibold truncate">Cao Nhất</div>
          <div className="text-xs sm:text-sm font-bold text-emerald-400 mt-1 truncate">
            {quote.high?.toLocaleString() || "--"}
          </div>
        </div>
        <div className="p-3 bg-[#161B22] border border-[#30363D] rounded-lg min-w-0 flex flex-col justify-between">
          <div className="text-[10px] text-gray-400 uppercase font-semibold truncate">Thấp Nhất</div>
          <div className="text-xs sm:text-sm font-bold text-rose-400 mt-1 truncate">
            {quote.low?.toLocaleString() || "--"}
          </div>
        </div>
        <div className="p-3 bg-[#161B22] border border-[#30363D] rounded-lg min-w-0 flex flex-col justify-between">
          <div className="text-[10px] text-gray-400 uppercase font-semibold truncate">Trung Bình</div>
          <div className="text-xs sm:text-sm font-bold text-amber-400 mt-1 truncate">
            {quote.avg_price ? Math.round(quote.avg_price).toLocaleString() : "--"}
          </div>
        </div>
        <div className="p-3 bg-[#161B22] border border-[#30363D] rounded-lg min-w-0 flex flex-col justify-between">
          <div className="text-[10px] text-gray-400 uppercase font-semibold truncate">
            KL Khớp Lệnh
          </div>
          <div className="text-xs sm:text-sm font-bold text-gray-200 mt-1 truncate">
            {quote.total_volume?.toLocaleString() || "--"}
          </div>
        </div>
        <div className="p-3 bg-[#161B22] border border-[#30363D] rounded-lg min-w-0 flex flex-col justify-between">
          <div className="text-[10px] text-gray-400 uppercase font-semibold truncate">Vốn Hóa</div>
          <div className="text-xs sm:text-sm font-bold text-blue-400 mt-1 truncate">
            {quote.market_cap
              ? `${(quote.market_cap / 1_000_000_000_000).toFixed(1)} Tỷ`
              : "--"}
          </div>
        </div>
      </div>
    </div>
  );
};
