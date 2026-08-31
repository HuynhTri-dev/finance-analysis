/**
 * @file RightSidebar.tsx
 * @description Collapsible right sidebar housing the AI Analysis Assistant (streaming reasoning logs & markdown output)
 * and the PDF Report Management Center (embedded iframe previewer, list of generated reports, and deletion controls).
 */

"use client";

import React from "react";
import { format } from "date-fns";
import {
  Sparkles,
  FileText,
  PanelRightClose,
  Bot,
  ExternalLink,
  ArrowLeft,
  RefreshCw,
  Loader2,
  Trash2,
} from "lucide-react";

export interface RightSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  sidebarTab: "chat" | "pdf";
  onTabChange: (tab: "chat" | "pdf") => void;
  isAnalyzing: boolean;
  agentLogs: { type: string; content: string }[];
  pdfReports: any[];
  loadingPdfs: boolean;
  selectedPdf: string | null;
  onSelectPdf: (url: string | null) => void;
  onRefreshPdfs: () => void;
  onDeleteReport: (e: React.MouseEvent, report: any) => void;
  deletingReportId: string | null;
}

export const RightSidebar: React.FC<RightSidebarProps> = ({
  isOpen,
  onClose,
  sidebarTab,
  onTabChange,
  isAnalyzing,
  agentLogs,
  pdfReports,
  loadingPdfs,
  selectedPdf,
  onSelectPdf,
  onRefreshPdfs,
  onDeleteReport,
  deletingReportId,
}) => {
  return (
    <>
      {/* Mobile Overlay Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-20 xl:hidden backdrop-blur-sm transition-opacity"
          onClick={onClose}
        />
      )}

      <aside
        className={`${
          isOpen
            ? "w-full sm:w-[400px] xl:w-[420px] translate-x-0"
            : "w-0 translate-x-full xl:translate-x-0 xl:w-0 border-l-0"
        } bg-[#161B22] border-l border-[#30363D] flex flex-col flex-shrink-0 transition-all duration-300 ease-in-out overflow-hidden z-30 fixed xl:static inset-y-0 right-0 shadow-2xl xl:shadow-none`}
      >
        <div className="w-full sm:w-[400px] xl:w-[420px] flex flex-col h-full">
          {/* Header Controls */}
          <div className="h-14 border-b border-[#30363D] flex items-center justify-between px-4 bg-[#161B22]">
            <div className="flex items-center space-x-2">
              <div
                className={`w-2.5 h-2.5 rounded-full ${
                  isAnalyzing ? "bg-emerald-500 animate-ping" : "bg-blue-500"
                }`}
              ></div>
              <h2 className="text-sm font-semibold text-gray-100">Trợ Lý Phân Tích AI</h2>
            </div>

            <div className="flex items-center space-x-2">
              <div className="flex items-center bg-[#0D1117] p-0.5 rounded-lg border border-[#30363D]">
                <button
                  onClick={() => onTabChange("chat")}
                  className={`px-2.5 py-1 text-xs font-medium rounded-md transition-all flex items-center gap-1.5 ${
                    sidebarTab === "chat"
                      ? "bg-[#21262D] text-blue-400 font-semibold shadow-sm border border-[#30363D]"
                      : "text-gray-400 hover:text-gray-200"
                  }`}
                  title="Phân tích AI (⌘ + Shift + P)"
                >
                  <Sparkles size={13} />
                  <span>AI</span>
                </button>
                <button
                  onClick={() => onTabChange("pdf")}
                  className={`px-2.5 py-1 text-xs font-medium rounded-md transition-all flex items-center gap-1.5 ${
                    sidebarTab === "pdf"
                      ? "bg-[#21262D] text-blue-400 font-semibold shadow-sm border border-[#30363D]"
                      : "text-gray-400 hover:text-gray-200"
                  }`}
                  title="Báo cáo PDF (⌘ + Shift + P)"
                >
                  <FileText size={13} />
                  <span>PDF</span>
                  {pdfReports.length > 0 && (
                    <span
                      className={`px-1.5 py-0.2 text-[10px] font-bold rounded-full transition-colors ${
                        sidebarTab === "pdf"
                          ? "bg-blue-500/20 text-blue-300"
                          : "bg-[#21262D] text-gray-400"
                      }`}
                    >
                      {pdfReports.length}
                    </span>
                  )}
                </button>
              </div>

              {/* Close / Collapse Right Sidebar Button */}
              <button
                onClick={onClose}
                className="p-1.5 text-gray-400 hover:text-gray-200 hover:bg-[#21262D] rounded-lg transition-colors"
                title="Thu gọn Trợ lý AI (Collapse)"
              >
                <PanelRightClose size={18} />
              </button>
            </div>
          </div>

          {/* Body Content */}
          {sidebarTab === "chat" ? (
            <div className="flex-1 overflow-y-auto p-4 space-y-3.5">
              {agentLogs.length === 0 ? (
                <div className="text-center py-16 flex flex-col items-center justify-center space-y-3">
                  <div className="w-12 h-12 rounded-2xl bg-blue-600/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
                    <Bot size={24} />
                  </div>
                  <p className="text-gray-400 text-xs px-6 leading-relaxed">
                    Nhấn nút <strong className="text-gray-200">&quot;AI Đánh Giá Mã Này&quot;</strong>{" "}
                    hoặc <strong className="text-gray-200">&quot;Tải PDF Nhanh&quot;</strong> để hệ
                    thống tiến hành phân tích chuyên sâu đa chiều.
                  </p>
                </div>
              ) : (
                agentLogs.map((log, i) => (
                  <div
                    key={i}
                    className={`p-4 rounded-xl border text-xs leading-relaxed ${
                      log.type === "system"
                        ? "bg-[#0D1117] border-[#30363D] text-gray-400"
                        : log.type === "error"
                        ? "bg-rose-950/20 border-rose-900/50 text-rose-300"
                        : "bg-[#1C2128] border-[#30363D] text-gray-200"
                    }`}
                  >
                    {log.type === "markdown" ? (
                      <div className="whitespace-pre-wrap font-sans text-gray-200 space-y-2">
                        {log.content}
                      </div>
                    ) : log.type === "pdf" ? (
                      <div className="flex flex-col space-y-2">
                        <div className="text-xs text-gray-300 font-semibold">
                          Báo cáo PDF đã được khởi tạo thành công:
                        </div>
                        <div className="flex items-center space-x-2 pt-1">
                          <button
                            onClick={() => {
                              onSelectPdf(log.content);
                              onTabChange("pdf");
                            }}
                            className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg flex items-center space-x-1.5 transition-colors shadow"
                          >
                            <FileText size={14} />
                            <span>Xem Trực Tiếp</span>
                          </button>
                          <a
                            href={log.content}
                            target="_blank"
                            rel="noreferrer"
                            className="px-3 py-1.5 bg-[#21262D] hover:bg-[#30363D] text-gray-300 text-xs font-semibold rounded-lg flex items-center space-x-1.5 transition-colors border border-[#30363D]"
                          >
                            <ExternalLink size={14} />
                            <span>Mở Tab Mới</span>
                          </a>
                        </div>
                      </div>
                    ) : (
                      <span>{log.content}</span>
                    )}
                  </div>
                ))
              )}
              {isAnalyzing && (
                <div className="p-4 rounded-xl bg-[#0D1117] border border-[#30363D] flex items-center space-x-3">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
                    <div
                      className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"
                      style={{ animationDelay: "0.15s" }}
                    ></div>
                    <div
                      className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"
                      style={{ animationDelay: "0.3s" }}
                    ></div>
                  </div>
                  <span className="text-xs text-gray-400">
                    AI Agent đang đọc dữ liệu tài chính & tổng hợp báo cáo...
                  </span>
                </div>
              )}
            </div>
          ) : (
            <div className="flex-1 flex flex-col overflow-hidden">
              {selectedPdf ? (
                <div className="flex-1 flex flex-col h-full bg-[#0D1117]">
                  <div className="p-2 border-b border-[#30363D] bg-[#161B22] flex items-center justify-between">
                    <button
                      onClick={() => onSelectPdf(null)}
                      className="flex items-center space-x-1 text-xs text-gray-300 hover:text-white px-2.5 py-1.5 rounded-md bg-[#21262D] hover:bg-[#30363D] transition-colors"
                    >
                      <ArrowLeft size={14} />
                      <span>Quay lại danh sách</span>
                    </button>
                    <a
                      href={selectedPdf}
                      target="_blank"
                      rel="noreferrer"
                      className="flex items-center space-x-1 text-xs text-blue-400 hover:underline px-2 py-1"
                    >
                      <ExternalLink size={14} />
                      <span>Mở tab riêng</span>
                    </a>
                  </div>
                  <iframe
                    src={selectedPdf}
                    className="w-full flex-1 border-none"
                    title="PDF Preview"
                  />
                </div>
              ) : (
                <div className="flex-1 overflow-y-auto p-4 space-y-3">
                  <div className="flex items-center justify-between pb-2 border-b border-[#30363D]">
                    <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                      Tất cả báo cáo đã tạo ({pdfReports.length})
                    </div>
                    <button
                      onClick={onRefreshPdfs}
                      disabled={loadingPdfs}
                      className="p-1 text-gray-400 hover:text-gray-200 rounded hover:bg-[#21262D] transition-colors"
                      title="Làm mới danh sách"
                    >
                      <RefreshCw size={14} className={loadingPdfs ? "animate-spin" : ""} />
                    </button>
                  </div>

                  {loadingPdfs && pdfReports.length === 0 ? (
                    <div className="text-center py-12 text-xs text-gray-500">
                      Đang tải danh sách báo cáo...
                    </div>
                  ) : pdfReports.length === 0 ? (
                    <div className="text-center py-16 flex flex-col items-center justify-center space-y-3">
                      <FileText size={36} className="text-gray-700" />
                      <p className="text-gray-500 text-xs px-4">
                        Chưa có báo cáo PDF nào. Nhấn &quot;Tải PDF Nhanh&quot; hoặc &quot;AI Đánh
                        giá Mã này&quot; để tạo báo cáo.
                      </p>
                    </div>
                  ) : (
                    pdfReports.map((report, idx) => (
                      <div
                        key={idx}
                        className="p-3.5 rounded-xl bg-[#0D1117] border border-[#30363D] hover:border-gray-600 transition-all flex flex-col space-y-2.5"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex items-start space-x-2.5">
                            <div className="w-8 h-8 rounded-lg bg-rose-950/40 border border-rose-800/40 text-rose-400 flex items-center justify-center flex-shrink-0 mt-0.5">
                              <FileText size={16} />
                            </div>
                            <div className="min-w-0 flex-1">
                              <div className="flex items-center justify-between gap-1">
                                <h4 className="text-xs font-semibold text-gray-200 line-clamp-1">
                                  {report.title || report.filename.replace(".pdf", "")}
                                </h4>
                                {report.symbol && (
                                  <span className="px-1.5 py-0.5 text-[10px] font-bold rounded bg-blue-500/15 text-blue-400 border border-blue-500/30 flex-shrink-0">
                                    {report.symbol}
                                  </span>
                                )}
                              </div>
                              <div className="flex items-center space-x-2 text-[11px] text-gray-500 mt-0.5">
                                <span>{report.size_kb ? `${report.size_kb} KB` : ""}</span>
                                <span>•</span>
                                <span>
                                  {report.created_at
                                    ? format(new Date(report.created_at), "dd/MM/yyyy HH:mm")
                                    : ""}
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center space-x-2 pt-1 border-t border-[#30363D]/60">
                          <button
                            onClick={() => onSelectPdf(report.url)}
                            className="flex-1 py-1.5 bg-[#21262D] hover:bg-[#30363D] text-blue-400 text-xs font-semibold rounded-lg flex items-center justify-center space-x-1.5 transition-colors"
                          >
                            <FileText size={13} />
                            <span>Xem ngay</span>
                          </button>
                          <a
                            href={report.url}
                            target="_blank"
                            rel="noreferrer"
                            className="px-2.5 py-1.5 bg-[#21262D] hover:bg-[#30363D] text-gray-300 hover:text-white text-xs rounded-lg flex items-center justify-center transition-colors border border-[#30363D]"
                            title="Mở tab mới"
                          >
                            <ExternalLink size={13} />
                          </a>
                          <button
                            onClick={(e) => onDeleteReport(e, report)}
                            disabled={deletingReportId === (report.id || report.filename)}
                            className="px-2.5 py-1.5 bg-[#21262D] hover:bg-rose-950/40 text-gray-400 hover:text-rose-400 text-xs rounded-lg flex items-center justify-center transition-colors border border-[#30363D] hover:border-rose-800/40 disabled:opacity-50"
                            title="Xoá báo cáo này"
                          >
                            {deletingReportId === (report.id || report.filename) ? (
                              <Loader2 size={13} className="animate-spin text-rose-400" />
                            ) : (
                              <Trash2 size={13} />
                            )}
                          </button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </aside>
    </>
  );
};
