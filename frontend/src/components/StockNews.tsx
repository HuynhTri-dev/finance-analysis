/**
 * @file StockNews.tsx
 * @description News feed and corporate disclosure section for the selected stock,
 * showing published timestamps, source, summary, and external link triggers.
 */

"use client";

import React from "react";
import { format } from "date-fns";

export interface StockNewsProps {
  news: any[];
}

export const StockNews: React.FC<StockNewsProps> = ({ news = [] }) => {
  return (
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
              key={n.id || n.url || n.link}
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
                <span>
                  {n.published_at
                    ? format(new Date(n.published_at), "dd/MM/yyyy HH:mm")
                    : ""}
                </span>
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
  );
};
