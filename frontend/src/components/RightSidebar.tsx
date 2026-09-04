/**
 * @file RightSidebar.tsx
 * @description Collapsible right sidebar housing the AI Analysis Assistant, BCTC Document Q&A Center
 * (with Cloudflare R2 Markdown viewer & grounded citations), and the PDF Report Management Center.
 */

"use client";

import React, { useState, useRef, useEffect } from "react";
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
  Send,
  Upload,
  ChevronDown,
  ChevronUp,
  ShieldAlert,
  BookOpen,
  FileCheck2,
  CheckCircle2,
  AlertCircle,
  X,
  User as UserIcon,
} from "lucide-react";
import { BCTCDocumentInfo, ChatMessage, resolveFileUrl } from "@/lib/api";

export interface RightSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  sidebarTab: "chat" | "pdf";
  onTabChange: (tab: "chat" | "pdf") => void;
  isAnalyzing: boolean;
  agentLogs?: { type: string; content: string }[];
  pdfReports: any[];
  loadingPdfs: boolean;
  selectedPdf: string | null;
  onSelectPdf: (url: string | null) => void;
  onRefreshPdfs: () => void;
  onDeleteReport: (e: React.MouseEvent, report: any) => void;
  deletingReportId: string | null;
  // BCTC & Chat Extensions
  activeSymbol?: string | null;
  activeDoc?: BCTCDocumentInfo | null;
  onUploadBCTC?: (file: File) => Promise<void>;
  isUploadingBCTC?: boolean;
  chatMessages?: ChatMessage[];
  onSendMessage?: (text: string) => Promise<void>;
  isSendingChat?: boolean;
  onGenerateComprehensive?: () => Promise<void>;
  isGeneratingComprehensive?: boolean;
  onClearActiveDoc?: () => void;
}

/**
 * Lightweight helper to format markdown-like text into styled React elements
 */
const FormattedMarkdown: React.FC<{ content: string }> = ({ content }) => {
  if (!content) return null;

  const lines = content.split("\n");
  const renderedElements: React.ReactNode[] = [];
  let tableRows: string[][] = [];
  let inTable = false;

  const flushTable = (keyIndex: number) => {
    if (tableRows.length > 0) {
      const header = tableRows[0];
      const rows = tableRows.slice(1).filter((r) => !r.every((c) => c.match(/^[-:| ]+$/)));
      renderedElements.push(
        <div key={`table-${keyIndex}`} className="overflow-x-auto my-2 rounded-lg border border-[#30363D]">
          <table className="min-w-full text-[11px] divide-y divide-[#30363D] text-left">
            <thead className="bg-[#21262D] text-gray-300 font-semibold">
              <tr>
                {header.map((col, ci) => (
                  <th key={ci} className="px-2.5 py-1.5 whitespace-nowrap">
                    {col.trim()}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-[#30363D]/60 bg-[#161B22]">
              {rows.map((row, ri) => (
                <tr key={ri} className="hover:bg-[#21262D]/50 transition-colors">
                  {row.map((cell, ci) => (
                    <td key={ci} className="px-2.5 py-1 text-gray-300">
                      {cell.trim()}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
      tableRows = [];
      inTable = false;
    }
  };

  lines.forEach((line, index) => {
    const trimmed = line.trim();

    // Markdown Tables
    if (trimmed.startsWith("|") && trimmed.endsWith("|")) {
      inTable = true;
      const cells = trimmed
        .split("|")
        .slice(1, -1)
        .map((c) => c.trim());
      tableRows.push(cells);
      return;
    } else if (inTable) {
      flushTable(index);
    }

    // Headers
    if (trimmed.startsWith("### ")) {
      renderedElements.push(
        <h4 key={index} className="text-xs font-bold text-blue-300 mt-2.5 mb-1 flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-400"></span>
          {trimmed.replace("### ", "")}
        </h4>
      );
      return;
    }
    if (trimmed.startsWith("## ")) {
      renderedElements.push(
        <h3 key={index} className="text-sm font-bold text-gray-100 mt-3 mb-1.5 pb-1 border-b border-[#30363D]">
          {trimmed.replace("## ", "")}
        </h3>
      );
      return;
    }
    if (trimmed.startsWith("# ")) {
      renderedElements.push(
        <h2 key={index} className="text-sm font-extrabold text-blue-400 mt-3.5 mb-2 pb-1 border-b border-blue-500/30">
          {trimmed.replace("# ", "")}
        </h2>
      );
      return;
    }

    // Bullet points
    if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
      const itemText = trimmed.substring(2);
      renderedElements.push(
        <div key={index} className="flex items-start gap-1.5 text-xs text-gray-300 my-0.5 ml-1 leading-relaxed">
          <span className="text-blue-400 font-bold mt-0.5">•</span>
          <span>{renderInlineBold(itemText)}</span>
        </div>
      );
      return;
    }

    // Blockquotes
    if (trimmed.startsWith("> ")) {
      renderedElements.push(
        <blockquote
          key={index}
          className="border-l-2 border-blue-500/60 pl-2.5 py-1 text-[11px] italic text-gray-400 bg-blue-500/5 rounded-r my-1.5"
        >
          {renderInlineBold(trimmed.substring(2))}
        </blockquote>
      );
      return;
    }

    // Empty lines
    if (trimmed === "") {
      renderedElements.push(<div key={index} className="h-1.5" />);
      return;
    }

    // Standard paragraph
    renderedElements.push(
      <p key={index} className="text-xs text-gray-300 leading-relaxed my-1">
        {renderInlineBold(line)}
      </p>
    );
  });

  if (inTable) {
    flushTable(lines.length);
  }

  return <div className="space-y-0.5">{renderedElements}</div>;
};

/**
 * Parses bold text (**text**) inside a string
 */
function renderInlineBold(text: string): React.ReactNode {
  const parts = text.split(/(\*\*.*?\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={i} className="text-gray-100 font-semibold">
          {part.slice(2, -2)}
        </strong>
      );
    }
    return part;
  });
}

export const RightSidebar: React.FC<RightSidebarProps> = ({
  isOpen,
  onClose,
  sidebarTab,
  onTabChange,
  isAnalyzing,
  agentLogs = [],
  pdfReports,
  loadingPdfs,
  selectedPdf,
  onSelectPdf,
  onRefreshPdfs,
  onDeleteReport,
  deletingReportId,
  activeSymbol,
  activeDoc,
  onUploadBCTC,
  isUploadingBCTC = false,
  chatMessages = [],
  onSendMessage,
  isSendingChat = false,
  onGenerateComprehensive,
  isGeneratingComprehensive = false,
  onClearActiveDoc,
}) => {
  const [inputText, setInputText] = useState("");
  const [showMetrics, setShowMetrics] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll chat to latest message
  useEffect(() => {
    if (sidebarTab === "chat") {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [chatMessages, isSendingChat, isAnalyzing, isGeneratingComprehensive, sidebarTab]);

  const handleSend = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputText.trim() || isSendingChat || !onSendMessage) return;
    const text = inputText.trim();
    setInputText("");
    await onSendMessage(text);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && onUploadBCTC) {
      onUploadBCTC(file);
    }
    if (e.target) e.target.value = "";
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file && file.type === "application/pdf" && onUploadBCTC) {
      onUploadBCTC(file);
    }
  };

  // Quick suggestion chips
  const suggestions = activeDoc
    ? [
        "Doanh thu & Lợi nhuận so với cùng kỳ?",
        "Ý kiến kiểm toán có điểm ngoại trừ không?",
        "Phân tích cơ cấu nợ vay & khả năng thanh toán?",
        "Chi phí tài chính và lãi vay biến động ra sao?",
      ]
    : [
        `Phân tích kỹ thuật chuyên sâu ${activeSymbol || "thị trường"}`,
        `Định giá P/E, P/B và ROE mã ${activeSymbol || "này"}`,
        "Tín hiệu dòng tiền khối ngoại và tự doanh",
      ];

  const metrics = activeDoc?.metrics || {};

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
            ? "w-full sm:w-[420px] xl:w-[460px] translate-x-0"
            : "w-0 translate-x-full xl:translate-x-0 xl:w-0 border-l-0"
        } bg-[#161B22] border-l border-[#30363D] flex flex-col flex-shrink-0 transition-all duration-300 ease-in-out overflow-hidden z-30 fixed xl:static inset-y-0 right-0 shadow-2xl xl:shadow-none`}
      >
        <div className="w-full sm:w-[420px] xl:w-[460px] flex flex-col h-full">
          {/* Header Controls */}
          <div className="h-14 border-b border-[#30363D] flex items-center justify-between px-4 bg-[#161B22] flex-shrink-0">
            <div className="flex items-center space-x-2">
              <div
                className={`w-2.5 h-2.5 rounded-full ${
                  isAnalyzing || isSendingChat || isGeneratingComprehensive
                    ? "bg-emerald-500 animate-ping"
                    : activeDoc
                    ? "bg-emerald-500"
                    : "bg-blue-500"
                }`}
              ></div>
              <h2 className="text-sm font-semibold text-gray-100 flex items-center gap-1.5">
                <span>Trợ Lý BCTC & AI</span>
                {activeSymbol && (
                  <span className="px-1.5 py-0.5 rounded text-[10px] bg-blue-500/20 text-blue-300 font-bold border border-blue-500/30">
                    {activeSymbol}
                  </span>
                )}
              </h2>
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
                  title="Phân tích AI & Chat BCTC"
                >
                  <Sparkles size={13} />
                  <span>AI & BCTC</span>
                  {activeDoc && (
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                  )}
                </button>
                <button
                  onClick={() => onTabChange("pdf")}
                  className={`px-2.5 py-1 text-xs font-medium rounded-md transition-all flex items-center gap-1.5 ${
                    sidebarTab === "pdf"
                      ? "bg-[#21262D] text-blue-400 font-semibold shadow-sm border border-[#30363D]"
                      : "text-gray-400 hover:text-gray-200"
                  }`}
                  title="Báo cáo PDF"
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
            <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
              {/* Top Banner: BCTC Document Card / Upload Dropzone */}
              <div className="p-3 border-b border-[#30363D] bg-[#0D1117]/80 flex-shrink-0">
                <input
                  type="file"
                  ref={fileInputRef}
                  accept=".pdf"
                  onChange={handleFileChange}
                  className="hidden"
                />

                {!activeDoc ? (
                  <div
                    onDragOver={(e) => {
                      e.preventDefault();
                      setDragOver(true);
                    }}
                    onDragLeave={() => setDragOver(false)}
                    onDrop={handleDrop}
                    onClick={() => fileInputRef.current?.click()}
                    className={`cursor-pointer border border-dashed rounded-xl p-3 flex items-center justify-between gap-3 transition-all ${
                      dragOver
                        ? "border-blue-500 bg-blue-500/10"
                        : "border-[#30363D] hover:border-blue-500/60 bg-[#161B22]/60 hover:bg-[#161B22]"
                    }`}
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400 flex-shrink-0">
                        {isUploadingBCTC ? (
                          <Loader2 size={16} className="animate-spin" />
                        ) : (
                          <Upload size={16} />
                        )}
                      </div>
                      <div className="min-w-0">
                        <div className="text-xs font-semibold text-gray-200 truncate">
                          {isUploadingBCTC ? "Đang trích xuất BCTC..." : "Tải Lên Báo Cáo Tài Chính (PDF)"}
                        </div>
                        <div className="text-[10px] text-gray-400 truncate">
                          {isUploadingBCTC
                            ? "Docling AI bóc tách số liệu & lưu Markdown..."
                            : "Bóc tách doanh thu, LN, lưu Cloudflare R2 & Chat"}
                        </div>
                      </div>
                    </div>
                    <button
                      type="button"
                      disabled={isUploadingBCTC}
                      className="px-2.5 py-1 text-[11px] font-semibold text-blue-400 bg-blue-500/10 hover:bg-blue-500/20 rounded-md border border-blue-500/30 flex-shrink-0 transition-colors"
                    >
                      {isUploadingBCTC ? "Đang tải..." : "Chọn File"}
                    </button>
                  </div>
                ) : (
                  <div className="rounded-xl border border-emerald-500/30 bg-[#161B22] p-2.5 shadow-sm space-y-2">
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2 min-w-0">
                        <div className="w-7 h-7 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 flex-shrink-0">
                          <FileCheck2 size={15} />
                        </div>
                        <div className="min-w-0">
                          <div className="text-xs font-semibold text-gray-200 truncate flex items-center gap-1.5">
                            <span className="truncate">{activeDoc.filename}</span>
                            <span className="px-1.5 py-0.2 text-[9px] font-bold rounded bg-emerald-500/20 text-emerald-300 flex-shrink-0">
                              {activeDoc.page_count} trang
                            </span>
                          </div>
                          <div className="text-[10px] text-emerald-400 flex items-center gap-1">
                            <CheckCircle2 size={10} />
                            <span>Đã xử lý • Lưu Cloudflare R2</span>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-1 flex-shrink-0">
                        <button
                          onClick={() => fileInputRef.current?.click()}
                          title="Đổi file BCTC khác"
                          className="p-1 text-gray-400 hover:text-gray-200 hover:bg-[#21262D] rounded transition-colors"
                        >
                          <RefreshCw size={13} />
                        </button>
                        {onClearActiveDoc && (
                          <button
                            onClick={onClearActiveDoc}
                            title="Đóng BCTC này"
                            className="p-1 text-gray-400 hover:text-rose-400 hover:bg-[#21262D] rounded transition-colors"
                          >
                            <X size={13} />
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Quick action bar */}
                    <div className="flex items-center gap-2 pt-1">
                      {activeDoc.markdown_url && (
                        <a
                          href={resolveFileUrl(activeDoc.markdown_url)}
                          target="_blank"
                          rel="noreferrer"
                          className="px-2 py-1 bg-[#21262D] hover:bg-[#30363D] text-gray-200 text-[11px] font-medium rounded-md border border-[#30363D] flex items-center gap-1 transition-colors"
                          title="Xem toàn văn văn bản Markdown trích xuất trên Cloudflare R2"
                        >
                          <ExternalLink size={12} className="text-blue-400" />
                          <span>Xem Markdown R2</span>
                        </a>
                      )}

                      {onGenerateComprehensive && (
                        <button
                          onClick={onGenerateComprehensive}
                          disabled={isGeneratingComprehensive}
                          className="px-2 py-1 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-[11px] font-semibold rounded-md shadow flex items-center gap-1 transition-all disabled:opacity-50"
                        >
                          <Sparkles size={12} className={isGeneratingComprehensive ? "animate-spin" : ""} />
                          <span>
                            {isGeneratingComprehensive ? "Đang tạo..." : "Báo Cáo Toàn Cảnh (3 Phần)"}
                          </span>
                        </button>
                      )}

                      <button
                        onClick={() => setShowMetrics(!showMetrics)}
                        className="ml-auto text-[11px] text-gray-400 hover:text-gray-200 flex items-center gap-0.5 px-1 py-0.5"
                      >
                        <span>Chỉ số</span>
                        {showMetrics ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                      </button>
                    </div>

                    {/* Collapsible Extracted Metrics Drawer */}
                    {showMetrics && (
                      <div className="pt-2 border-t border-[#30363D] grid grid-cols-2 gap-1.5 text-[11px]">
                        <div className="bg-[#0D1117] p-1.5 rounded border border-[#30363D]/80">
                          <span className="text-gray-400 block text-[10px]">Doanh thu thuần:</span>
                          <span className="text-gray-100 font-semibold">
                            {metrics.revenue != null ? `${Number(metrics.revenue).toLocaleString()} tỷ` : "N/A"}
                          </span>
                        </div>
                        <div className="bg-[#0D1117] p-1.5 rounded border border-[#30363D]/80">
                          <span className="text-gray-400 block text-[10px]">Lợi nhuận sau thuế:</span>
                          <span className="text-emerald-400 font-semibold">
                            {metrics.profit_after_tax != null ? `${Number(metrics.profit_after_tax).toLocaleString()} tỷ` : "N/A"}
                          </span>
                        </div>
                        <div className="bg-[#0D1117] p-1.5 rounded border border-[#30363D]/80">
                          <span className="text-gray-400 block text-[10px]">EPS / ROE:</span>
                          <span className="text-blue-300 font-semibold">
                            {metrics.eps ? `${Number(metrics.eps).toLocaleString()} đ` : "--"} |{" "}
                            {metrics.roe ? `${metrics.roe}%` : "--"}
                          </span>
                        </div>
                        <div className="bg-[#0D1117] p-1.5 rounded border border-[#30363D]/80">
                          <span className="text-gray-400 block text-[10px]">Kiểm toán:</span>
                          <span className="text-gray-200 font-medium truncate block" title={metrics.auditor_opinion || "N/A"}>
                            {metrics.auditor_opinion || "Chấp nhận toàn phần"}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Middle Section: Scrollable Messages */}
              <div className="flex-1 overflow-y-auto p-3.5 space-y-3.5 min-h-0">
                {chatMessages.length === 0 && agentLogs.length === 0 ? (
                  <div className="text-center py-12 flex flex-col items-center justify-center space-y-3">
                    <div className="w-12 h-12 rounded-2xl bg-blue-600/10 border border-blue-500/20 flex items-center justify-center text-blue-400 shadow-inner">
                      <Bot size={24} />
                    </div>
                    <div className="space-y-1 px-4">
                      <p className="text-gray-200 font-medium text-xs">
                        Hỏi đáp tài chính & Báo cáo chuyên sâu
                      </p>
                      <p className="text-gray-400 text-[11px] leading-relaxed">
                        Tải file PDF BCTC lên hoặc nhấn vào các gợi ý bên dưới để AI phân tích ngay.
                      </p>
                    </div>
                  </div>
                ) : null}

                {/* Legacy agent logs support (if any) */}
                {agentLogs.length > 0 && chatMessages.length === 0 && (
                  <div className="space-y-3">
                    {agentLogs.map((log, i) => (
                      <div
                        key={i}
                        className={`p-3.5 rounded-xl border text-xs leading-relaxed ${
                          log.type === "system"
                            ? "bg-[#0D1117] border-[#30363D] text-gray-400"
                            : log.type === "error"
                            ? "bg-rose-950/20 border-rose-900/50 text-rose-300"
                            : "bg-[#1C2128] border-[#30363D] text-gray-200"
                        }`}
                      >
                        {log.type === "markdown" ? (
                          <FormattedMarkdown content={log.content} />
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
                                href={resolveFileUrl(log.content)}
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
                    ))}
                  </div>
                )}

                {/* Primary Chat Messages Stream */}
                {chatMessages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex flex-col ${
                      msg.role === "user" ? "items-end" : "items-start"
                    }`}
                  >
                    <div
                      className={`max-w-[92%] rounded-2xl p-3 text-xs leading-relaxed shadow-sm ${
                        msg.role === "user"
                          ? "bg-blue-600 text-white rounded-tr-sm"
                          : msg.isError
                          ? "bg-rose-950/30 border border-rose-800 text-rose-300 rounded-tl-sm"
                          : msg.role === "system"
                          ? "bg-[#0D1117] border border-[#30363D] text-gray-400 text-[11px]"
                          : "bg-[#1C2128] border border-[#30363D] text-gray-200 rounded-tl-sm"
                      }`}
                    >
                      {/* Message header */}
                      <div className="flex items-center gap-1.5 mb-1 opacity-70 text-[10px]">
                        {msg.role === "user" ? (
                          <>
                            <UserIcon size={11} />
                            <span>Bạn</span>
                          </>
                        ) : (
                          <>
                            <Bot size={11} className="text-blue-400" />
                            <span className="font-semibold text-blue-400">AI Assistant</span>
                          </>
                        )}
                        <span>•</span>
                        <span>{msg.timestamp ? format(new Date(msg.timestamp), "HH:mm") : ""}</span>
                      </div>

                      {/* Content */}
                      {msg.role === "user" ? (
                        <div className="whitespace-pre-wrap font-sans">{msg.content}</div>
                      ) : (
                        <FormattedMarkdown content={msg.content} />
                      )}

                      {/* Citations section (for grounded responses) */}
                      {msg.citations && msg.citations.length > 0 && (
                        <div className="mt-3 pt-2.5 border-t border-[#30363D] space-y-1.5">
                          <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider flex items-center gap-1">
                            <BookOpen size={11} className="text-blue-400" />
                            <span>Nguồn trích dẫn (BCTC):</span>
                          </div>
                          <div className="flex flex-wrap gap-1">
                            {msg.citations.map((cite, ci) => (
                              <span
                                key={ci}
                                className="px-1.5 py-0.5 rounded text-[10px] bg-blue-500/10 text-blue-300 border border-blue-500/20"
                              >
                                {cite}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Attached PDF report link */}
                      {msg.pdf_url && (
                        <div className="mt-3 pt-2 border-t border-[#30363D] flex items-center gap-2">
                          <button
                            onClick={() => {
                              onSelectPdf(msg.pdf_url || null);
                              onTabChange("pdf");
                            }}
                            className="px-2.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-[11px] font-semibold rounded-lg flex items-center gap-1 shadow transition-colors"
                          >
                            <FileText size={13} />
                            <span>Xem PDF Ngay</span>
                          </button>
                          <a
                            href={resolveFileUrl(msg.pdf_url)}
                            target="_blank"
                            rel="noreferrer"
                            className="px-2.5 py-1.5 bg-[#21262D] hover:bg-[#30363D] text-gray-300 text-[11px] font-semibold rounded-lg flex items-center gap-1 border border-[#30363D] transition-colors"
                          >
                            <ExternalLink size={13} />
                            <span>Tải / Tab Mới</span>
                          </a>
                        </div>
                      )}

                      {/* Disclaimer (BR-007) */}
                      {msg.disclaimer && (
                        <div className="mt-2.5 pt-2 border-t border-[#30363D]/60 text-[10px] text-gray-400 flex items-start gap-1">
                          <ShieldAlert size={12} className="text-amber-400 flex-shrink-0 mt-0.5" />
                          <span>{msg.disclaimer}</span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}

                {/* Loading status indicator */}
                {(isAnalyzing || isSendingChat || isGeneratingComprehensive) && (
                  <div className="p-3 rounded-xl bg-[#0D1117] border border-[#30363D] flex items-center space-x-3 text-xs text-gray-300">
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
                    <span className="text-[11px] text-gray-400">
                      {isGeneratingComprehensive
                        ? "Đang sinh Báo Cáo Toàn Cảnh 3 Phần..."
                        : isSendingChat
                        ? "AI đang đọc lại văn bản BCTC từ Cloudflare R2 và phân tích..."
                        : "AI Agent đang tổng hợp dữ liệu chuyên sâu..."}
                    </span>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Bottom Sticky Chat Input & Suggestions */}
              <div className="p-3 border-t border-[#30363D] bg-[#161B22] flex-shrink-0 space-y-2">
                {/* Prompt suggestion chips */}
                <div className="flex items-center gap-1.5 overflow-x-auto pb-1 no-scrollbar">
                  {suggestions.map((sug, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => setInputText(sug)}
                      className="px-2.5 py-1 rounded-full text-[10px] bg-[#21262D] hover:bg-[#30363D] text-gray-300 hover:text-white border border-[#30363D] whitespace-nowrap transition-colors flex-shrink-0"
                    >
                      {sug}
                    </button>
                  ))}
                </div>

                {/* Input form */}
                <form onSubmit={handleSend} className="flex items-center gap-2">
                  <div className="relative flex-1">
                    <input
                      type="text"
                      value={inputText}
                      onChange={(e) => setInputText(e.target.value)}
                      placeholder={
                        activeDoc
                          ? `Hỏi về ${activeDoc.filename}... (VD: Doanh thu thuần, nợ vay)`
                          : `Nhập câu hỏi hoặc tải BCTC lên để hỏi đáp...`
                      }
                      disabled={isSendingChat || isAnalyzing || isGeneratingComprehensive}
                      className="w-full bg-[#0D1117] border border-[#30363D] focus:border-blue-500 rounded-xl px-3.5 py-2 text-xs text-gray-200 placeholder-gray-500 focus:outline-none transition-colors"
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={
                      !inputText.trim() ||
                      isSendingChat ||
                      isAnalyzing ||
                      isGeneratingComprehensive
                    }
                    className="p-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 disabled:hover:bg-blue-600 text-white rounded-xl transition-all shadow-md flex-shrink-0"
                    title="Gửi câu hỏi"
                  >
                    {isSendingChat ? (
                      <Loader2 size={16} className="animate-spin" />
                    ) : (
                      <Send size={16} />
                    )}
                  </button>
                </form>
              </div>
            </div>
          ) : (
            /* PDF Tab Content (Unchanged functionality, preserved perfectly) */
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
                      href={resolveFileUrl(selectedPdf)}
                      target="_blank"
                      rel="noreferrer"
                      className="flex items-center space-x-1 text-xs text-blue-400 hover:underline px-2 py-1"
                    >
                      <ExternalLink size={14} />
                      <span>Mở tab riêng</span>
                    </a>
                  </div>
                  <iframe
                    src={resolveFileUrl(selectedPdf)}
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
                      <Loader2 size={20} className="animate-spin mx-auto mb-2 text-blue-400" />
                      <span>Đang tải danh sách báo cáo...</span>
                    </div>
                  ) : pdfReports.length === 0 ? (
                    <div className="text-center py-16 flex flex-col items-center justify-center space-y-3">
                      <div className="w-12 h-12 rounded-2xl bg-blue-600/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
                        <FileText size={24} />
                      </div>
                      <p className="text-gray-400 text-xs px-6 leading-relaxed">
                        Chưa có báo cáo PDF nào được tạo. Nhấn &quot;Tải PDF Nhanh&quot; hoặc &quot;Báo Cáo Toàn Cảnh (3 Phần)&quot; để sinh tài liệu.
                      </p>
                    </div>
                  ) : (
                    pdfReports.map((report) => (
                      <div
                        key={report.id || report.filename}
                        onClick={() => onSelectPdf(report.url)}
                        className="p-3.5 rounded-xl border border-[#30363D] bg-[#1C2128] hover:border-blue-500/50 hover:bg-[#21262D] transition-all cursor-pointer group flex items-start justify-between"
                      >
                        <div className="flex items-start space-x-3 min-w-0">
                          <div className="p-2 rounded-lg bg-blue-600/10 border border-blue-500/20 text-blue-400 flex-shrink-0 group-hover:scale-105 transition-transform">
                            <FileText size={18} />
                          </div>
                          <div className="min-w-0">
                            <h4 className="text-xs font-semibold text-gray-200 group-hover:text-blue-400 transition-colors truncate">
                              {report.title || report.filename}
                            </h4>
                            <div className="flex items-center space-x-2 text-[10px] text-gray-400 mt-1">
                              {report.created_at && (
                                <span>
                                  {format(new Date(report.created_at), "dd/MM/yyyy HH:mm")}
                                </span>
                              )}
                              {report.size && <span>• {report.size}</span>}
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center space-x-1 flex-shrink-0 ml-2">
                          <button
                            onClick={(e) => onDeleteReport(e, report)}
                            disabled={deletingReportId === (report.id || report.filename)}
                            className="p-1.5 text-gray-500 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors"
                            title="Xoá báo cáo"
                          >
                            {deletingReportId === (report.id || report.filename) ? (
                              <Loader2 size={14} className="animate-spin text-rose-400" />
                            ) : (
                              <Trash2 size={14} />
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
