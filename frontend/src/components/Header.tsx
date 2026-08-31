/**
 * @file Header.tsx
 * @description Top navigation bar for the dashboard, providing sidebar expansion controls,
 * current market/symbol title indicator, live timestamp, and the AI/PDF panel toggle.
 */

"use client";

import React, { useEffect, useState } from "react";
import { format } from "date-fns";
import { PanelLeftOpen, PanelRightClose, PanelRightOpen, Bot } from "lucide-react";

export interface HeaderProps {
  isLeftSidebarOpen: boolean;
  onOpenLeftSidebar: () => void;
  isRightSidebarOpen: boolean;
  onToggleRightSidebar: () => void;
  activeSymbol: string | null;
  pdfCount: number;
  isAnalyzing: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  isLeftSidebarOpen,
  onOpenLeftSidebar,
  isRightSidebarOpen,
  onToggleRightSidebar,
  activeSymbol,
  pdfCount,
  isAnalyzing,
}) => {
  const [currentDate, setCurrentDate] = useState<string>("");

  useEffect(() => {
    setCurrentDate(format(new Date(), "dd/MM/yyyy HH:mm"));
  }, []);

  return (
    <header className="h-14 border-b border-[#30363D] flex items-center justify-between px-4 sm:px-6 bg-[#161B22]/80 backdrop-blur z-10">
      <div className="flex items-center space-x-3 min-w-0">
        {/* Toggle Left Sidebar Button (when collapsed) */}
        {!isLeftSidebarOpen && (
          <button
            onClick={onOpenLeftSidebar}
            className="p-2 text-gray-400 hover:text-gray-100 hover:bg-[#21262D] rounded-lg transition-colors border border-[#30363D] flex items-center space-x-1.5"
            title="Mở danh mục theo dõi"
          >
            <PanelLeftOpen size={16} className="text-blue-400" />
            <span className="text-xs font-semibold hidden md:inline text-gray-300">
              Mã cổ phiếu
            </span>
          </button>
        )}

        <div className="flex items-center space-x-2 truncate">
          <span className="text-xs sm:text-sm font-semibold text-gray-200 truncate">
            {activeSymbol ? `Dashboard: ${activeSymbol}` : "Tổng Quan Thị Trường Việt Nam"}
          </span>
        </div>
      </div>

      {/* Right Header Actions */}
      <div className="flex items-center space-x-3 flex-shrink-0">
        <div className="text-xs text-gray-400 hidden lg:block">
          {currentDate}
        </div>

        {/* Toggle Right AI / PDF Panel Button */}
        <button
          onClick={onToggleRightSidebar}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-2 border transition-all ${
            isRightSidebarOpen
              ? "bg-blue-600/15 text-blue-400 border-blue-500/40 shadow-sm"
              : "bg-[#21262D] text-gray-300 border-[#30363D] hover:bg-[#30363D] hover:text-white"
          }`}
          title={isRightSidebarOpen ? "Thu gọn thanh AI & Báo Cáo" : "Mở Trợ lý AI & Báo Cáo"}
        >
          <Bot
            size={15}
            className={isAnalyzing ? "text-emerald-400 animate-spin" : "text-blue-400"}
          />
          <span>Trợ Lý AI & PDF</span>
          {pdfCount > 0 && (
            <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-blue-600 text-white font-bold">
              {pdfCount}
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
  );
};
