/**
 * @file StockKeyStats.tsx
 * @description Clean statistical summary strip grouped into 3 distinct logical sections:
 * Price Limits (Ceiling/Floor), Realized Session Values (Open/High/Low/Volume), and Supplemental Info (Avg/Market Cap).
 */

"use client";

import React from "react";

export interface StockKeyStatsProps {
  quote: any;
}

export const StockKeyStats: React.FC<StockKeyStatsProps> = ({ quote = {} }) => {
  const ceilingVal = quote.ceiling?.toLocaleString() || "--";
  const floorVal = quote.floor?.toLocaleString() || "--";
  const openVal = quote.open?.toLocaleString() || "--";
  const highVal = quote.high?.toLocaleString() || "--";
  const lowVal = quote.low?.toLocaleString() || "--";
  const avgVal = quote.avg_price ? Math.round(quote.avg_price).toLocaleString() : "--";
  const volumeVal = quote.total_volume?.toLocaleString() || "--";
  const marketCapVal = quote.market_cap
    ? quote.market_cap >= 1_000_000_000_000
      ? `${(quote.market_cap / 1_000_000_000_000).toFixed(1)} nghìn tỷ`
      : `${(quote.market_cap / 1_000_000_000).toFixed(1)} tỷ`
    : "--";

  return (
    <div className="@container w-full">
      <div className="grid grid-cols-1 @[640px]:grid-cols-12 gap-2.5">
        {/* NHÓM 1: BIÊN ĐỘ GIÁ (TRẦN / SÀN) */}
        <div className="@[640px]:col-span-3 bg-[#161B22] border border-[#30363D] rounded-xl p-3 flex flex-col justify-between">
          <div className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-2">
            Biên độ giá
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <div className="text-[10px] text-gray-400 font-medium uppercase">Trần</div>
              <div className="text-sm font-bold text-purple-400 whitespace-nowrap mt-0.5">
                {ceilingVal}
              </div>
            </div>
            <div>
              <div className="text-[10px] text-gray-400 font-medium uppercase">Sàn</div>
              <div className="text-sm font-bold text-cyan-400 whitespace-nowrap mt-0.5">
                {floorVal}
              </div>
            </div>
          </div>
        </div>

        {/* NHÓM 2: GIAO DỊCH TRONG PHIÊN */}
        <div className="@[640px]:col-span-6 bg-[#161B22] border border-[#30363D] rounded-xl p-3 flex flex-col justify-between">
          <div className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-2">
            Trong phiên
          </div>
          <div className="grid grid-cols-2 @[480px]:grid-cols-4 gap-2">
            <div className="bg-[#0D1117]/60 border border-[#30363D]/50 rounded-lg p-2 min-w-0">
              <div className="text-[10px] text-gray-400 font-semibold uppercase flex items-center gap-1.5 truncate">
                <span className="w-1.5 h-1.5 rounded-full shrink-0 bg-gray-400"></span>
                <span className="truncate">Mở Cửa</span>
              </div>
              <div className="text-sm font-bold text-gray-200 whitespace-nowrap mt-1">
                {openVal}
              </div>
            </div>
            <div className="bg-[#0D1117]/60 border border-[#30363D]/50 rounded-lg p-2 min-w-0">
              <div className="text-[10px] text-gray-400 font-semibold uppercase flex items-center gap-1.5 truncate">
                <span className="w-1.5 h-1.5 rounded-full shrink-0 bg-emerald-400"></span>
                <span className="truncate">Cao Nhất</span>
              </div>
              <div className="text-sm font-bold text-emerald-400 whitespace-nowrap mt-1">
                {highVal}
              </div>
            </div>
            <div className="bg-[#0D1117]/60 border border-[#30363D]/50 rounded-lg p-2 min-w-0">
              <div className="text-[10px] text-gray-400 font-semibold uppercase flex items-center gap-1.5 truncate">
                <span className="w-1.5 h-1.5 rounded-full shrink-0 bg-rose-400"></span>
                <span className="truncate">Thấp Nhất</span>
              </div>
              <div className="text-sm font-bold text-rose-400 whitespace-nowrap mt-1">
                {lowVal}
              </div>
            </div>
            <div className="bg-[#0D1117]/60 border border-[#30363D]/50 rounded-lg p-2 min-w-0">
              <div className="text-[10px] text-gray-400 font-semibold uppercase flex items-center gap-1.5 truncate">
                <span className="w-1.5 h-1.5 rounded-full shrink-0 bg-cyan-400"></span>
                <span className="truncate">Khối Lượng</span>
              </div>
              <div className="text-sm font-bold text-gray-100 whitespace-nowrap mt-1">
                {volumeVal}
              </div>
            </div>
          </div>
        </div>

        {/* NHÓM 3: THÔNG TIN BỔ SUNG */}
        <div className="@[640px]:col-span-3 bg-[#161B22] border border-[#30363D] rounded-xl p-3 flex flex-col justify-between">
          <div className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-2">
            Bổ sung
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <div className="text-[10px] text-gray-400 font-medium uppercase truncate">Trung Bình</div>
              <div className="text-sm font-bold text-amber-400 whitespace-nowrap mt-0.5">
                {avgVal}
              </div>
            </div>
            <div>
              <div className="text-[10px] text-gray-400 font-medium uppercase truncate">Vốn Hóa</div>
              <div className="text-sm font-bold text-blue-400 whitespace-nowrap mt-0.5">
                {marketCapVal}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};


