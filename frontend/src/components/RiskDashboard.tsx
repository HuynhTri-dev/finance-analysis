'use client';

import React, { useEffect, useState } from 'react';
import { analyzeApi } from '@/lib/api';
import {
  AlertTriangle,
  AlertCircle,
  ShieldCheck,
  Activity,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  XCircle,
  Info,
  TrendingUp,
  TrendingDown,
  Layers,
  BarChart3,
  RefreshCw,
  Sliders,
  BookOpen,
  FileSpreadsheet,
  Calculator,
  HelpCircle,
} from 'lucide-react';

interface FScoreSignal {
  id: string;
  pillar: string;
  title: string;
  passed: boolean;
  value?: string;
  formula?: string;
  calculation?: string;
  source_statement?: string;
  condition?: string;
  desc: string;
}

interface StatementItem {
  item_name: string;
  item_code: string;
  statement: string;
  val_t: number;
  val_t1: number;
  unit: string;
  used_in: string;
}

interface PillarDetail {
  score: number;
  max: number;
  name: string;
}

interface ValuationMetrics {
  pe?: number | null;
  pb?: number | null;
  roe?: number | null;
  debt_to_equity?: number | null;
}

interface ReasonDetail {
  code: string;
  title: string;
}

interface RiskData {
  symbol: string;
  as_of_date: string;
  f_score: number | null;
  buy_score: number;
  sell_score: number;
  buy_level: string;
  sell_level: string;
  exchange_limit_hit?: boolean;
  scenario: string;
  valuation?: ValuationMetrics;
  f_score_details?: {
    f_score: number | null;
    has_data?: boolean;
    latest_year?: string;
    prior_year?: string;
    error_msg?: string;
    pillars: {
      profitability: PillarDetail;
      leverage: PillarDetail;
      efficiency: PillarDetail;
    };
    signals: FScoreSignal[];
    statement_table?: StatementItem[];
    raw_metrics?: {
      latest_year?: string;
      prior_year?: string;
      net_income_bil?: number;
      cfo_bil?: number;
      revenue_bil?: number;
      roa_pct?: number;
      current_ratio?: number;
      gross_margin_pct?: number;
    };
  };
  details: {
    buy_reasons: string[];
    sell_reasons: string[];
    buy_reasons_detail?: ReasonDetail[];
    sell_reasons_detail?: ReasonDetail[];
    buy_components?: Record<string, number>;
    sell_components?: Record<string, number>;
  };
}

interface Props {
  symbol: string;
}

export const RiskDashboard: React.FC<Props> = ({ symbol }) => {
  const [data, setData] = useState<RiskData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [activeTab, setActiveTab] = useState<'fscore' | 'audit' | 'technical' | 'valuation'>('fscore');
  const [expandedSignalId, setExpandedSignalId] = useState<string | null>(null);

  const fetchRiskData = async (forceRefresh: boolean = false) => {
    try {
      if (forceRefresh) setRefreshing(true);
      const res = await analyzeApi.getRiskAnalysis(symbol, forceRefresh);
      setData(res);
      setError(null);
    } catch (err) {
      console.error(err);
      setError('Không thể lấy dữ liệu phân tích rủi ro & cơ bản.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    if (symbol) {
      setLoading(true);
      fetchRiskData(false);
    }
  }, [symbol]);

  if (loading) {
    return (
      <div className="p-6 bg-gray-800/80 border border-gray-700/50 rounded-xl text-gray-400 animate-pulse h-64 flex flex-col items-center justify-center gap-3 mt-6">
        <RefreshCw className="w-6 h-6 animate-spin text-blue-500" />
        <span className="text-sm font-medium">Đang tải và tính toán rủi ro đa chiều cho {symbol}...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-5 bg-red-900/20 border border-red-500/30 text-red-400 rounded-xl mt-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-400 shrink-0" />
          <span className="text-sm">{error}</span>
        </div>
        <button
          onClick={() => fetchRiskData(true)}
          className="px-3 py-1 bg-red-500/20 hover:bg-red-500/30 text-red-300 text-xs rounded-lg transition-colors"
        >
          Thử lại
        </button>
      </div>
    );
  }

  if (!data) return null;

  // Helpers for styling
  const getRiskStyle = (score: number) => {
    if (score >= 75) {
      return {
        badge: 'bg-red-500/20 text-red-400 border border-red-500/30',
        card: 'bg-gradient-to-b from-red-950/20 to-gray-900 border-red-500/30',
        text: 'text-red-400',
        bar: 'bg-red-500',
      };
    }
    if (score >= 60) {
      return {
        badge: 'bg-orange-500/20 text-orange-400 border border-orange-500/30',
        card: 'bg-gradient-to-b from-orange-950/20 to-gray-900 border-orange-500/30',
        text: 'text-orange-400',
        bar: 'bg-orange-500',
      };
    }
    if (score >= 40) {
      return {
        badge: 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30',
        card: 'bg-gradient-to-b from-yellow-950/20 to-gray-900 border-yellow-500/30',
        text: 'text-yellow-400',
        bar: 'bg-yellow-500',
      };
    }
    return {
      badge: 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30',
      card: 'bg-gradient-to-b from-emerald-950/20 to-gray-900 border-emerald-500/30',
      text: 'text-emerald-400',
      bar: 'bg-emerald-500',
    };
  };

  const getFScoreBadge = (score: number | null) => {
    if (score === null) return { text: 'Chưa đủ BCTC', color: 'text-gray-400 bg-gray-700/50' };
    if (score >= 7) return { text: 'Rất vững mạnh', color: 'text-emerald-400 bg-emerald-500/20 border-emerald-500/30' };
    if (score >= 5) return { text: 'Trung bình khá', color: 'text-blue-400 bg-blue-500/20 border-blue-500/30' };
    if (score >= 4) return { text: 'Dưới trung bình', color: 'text-amber-400 bg-amber-500/20 border-amber-500/30' };
    return { text: 'Rất yếu - Rủi ro cao', color: 'text-rose-400 bg-rose-500/20 border-rose-500/30' };
  };

  const getScenarioStyle = (scenario: string) => {
    if (scenario.includes('CẢNH BÁO') || scenario.includes('RỦI RO NỘI TẠI')) {
      return {
        card: 'bg-rose-950/30 border-rose-500/40 text-rose-300',
        iconBg: 'bg-rose-500/20 text-rose-400',
        icon: <AlertTriangle className="w-5 h-5" />,
      };
    }
    if (scenario.includes('GIẢM TỶ TRỌNG') || scenario.includes('THẬN TRỌNG')) {
      return {
        card: 'bg-amber-950/30 border-amber-500/40 text-amber-300',
        iconBg: 'bg-amber-500/20 text-amber-400',
        icon: <AlertCircle className="w-5 h-5" />,
      };
    }
    if (scenario.includes('MỞ MUA') || scenario.includes('TÍCH LŨY')) {
      return {
        card: 'bg-emerald-950/30 border-emerald-500/40 text-emerald-300',
        iconBg: 'bg-emerald-500/20 text-emerald-400',
        icon: <ShieldCheck className="w-5 h-5" />,
      };
    }
    return {
      card: 'bg-blue-950/30 border-blue-500/40 text-blue-300',
      iconBg: 'bg-blue-500/20 text-blue-400',
      icon: <Activity className="w-5 h-5" />,
    };
  };

  const buyStyle = getRiskStyle(data.buy_score);
  const sellStyle = getRiskStyle(data.sell_score);
  const fBadge = getFScoreBadge(data.f_score);
  const scenarioStyle = getScenarioStyle(data.scenario);

  const pillars = data.f_score_details?.pillars || {
    profitability: { score: 0, max: 4, name: 'Khả năng sinh lời' },
    leverage: { score: 0, max: 3, name: 'Đòn bẩy & Thanh khoản' },
    efficiency: { score: 0, max: 2, name: 'Hiệu quả hoạt động' },
  };

  const signals = data.f_score_details?.signals || [];
  const statementTable = data.f_score_details?.statement_table || [];
  const rawMetrics = data.f_score_details?.raw_metrics;
  const valuation = data.valuation;
  const latestYear = data.f_score_details?.latest_year || '2025';
  const priorYear = data.f_score_details?.prior_year || '2024';

  const buyReasonsList = data.details?.buy_reasons_detail || data.details?.buy_reasons?.map((r) => ({ code: r, title: r })) || [];
  const sellReasonsList = data.details?.sell_reasons_detail || data.details?.sell_reasons?.map((r) => ({ code: r, title: r })) || [];

  return (
    <div className="@container bg-gray-850 border border-gray-700/60 rounded-xl p-4 sm:p-5 mt-6 shadow-2xl transition-all">
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5 pb-4 border-b border-gray-700/60">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-base sm:text-lg md:text-xl font-bold text-white flex items-center gap-2 truncate">
              <Layers className="w-5 h-5 text-blue-400 shrink-0" />
              <span>Phân Tích Cơ Bản & Rủi Ro: <span className="text-blue-400">{symbol}</span></span>
            </h2>
            <span className="text-xs text-gray-400 px-2 py-0.5 bg-gray-800 border border-gray-700 rounded-md shrink-0">
              {data.as_of_date}
            </span>
            {data.exchange_limit_hit && (
              <span className="text-xs text-amber-400 bg-amber-500/10 border border-amber-500/30 px-2 py-0.5 rounded-md flex items-center gap-1 shrink-0">
                <AlertCircle className="w-3.5 h-3.5" /> Biên độ Trần/Sàn
              </span>
            )}
          </div>
          <p className="text-gray-400 text-xs mt-1">
            Đánh giá toàn diện 9 tiêu chuẩn Piotroski F-Score kết hợp hệ thống chấm điểm rủi ro EOD
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0 self-start sm:self-auto">
          <button
            onClick={() => fetchRiskData(true)}
            disabled={refreshing}
            className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 active:scale-95 text-gray-200 text-xs rounded-lg transition-all flex items-center gap-1.5 border border-gray-600/50 whitespace-nowrap"
            title="Tính toán lại dữ liệu mới nhất từ vnstock"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-blue-400' : ''}`} />
            <span>{refreshing ? 'Đang tính...' : 'Làm mới'}</span>
          </button>

          <button
            onClick={() => setExpanded(!expanded)}
            className="px-3 py-1.5 bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 border border-blue-500/30 text-xs font-medium rounded-lg transition-all flex items-center gap-1.5 whitespace-nowrap"
          >
            <Sliders className="w-3.5 h-3.5 text-blue-400" />
            <span>{expanded ? 'Thu gọn' : 'Xem chi tiết số liệu & công thức'}</span>
            {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* 3 CARDS GRID: Responsive across Viewport and Parent Container */}
      <div className="grid grid-cols-1 @xl:grid-cols-3 gap-3.5 sm:gap-4">
        {/* CARD 1: BUY RISK */}
        <div className={`p-4 rounded-xl border flex flex-col justify-between transition-all min-w-0 ${buyStyle.card}`}>
          <div>
            <div className="flex items-center justify-between gap-2 mb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-gray-300 flex items-center gap-1.5 min-w-0 truncate">
                <TrendingUp className="w-4 h-4 text-gray-400 shrink-0" />
                <span className="truncate">Rủi ro Mua Đuổi</span>
              </span>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md border shrink-0 whitespace-nowrap ${buyStyle.badge}`}>
                {data.buy_level}
              </span>
            </div>

            <div className="flex items-baseline gap-1.5 mb-2">
              <span className={`text-3xl sm:text-4xl font-extrabold ${buyStyle.text}`}>{data.buy_score}</span>
              <span className="text-xs text-gray-500 font-medium">/ 100</span>
            </div>

            <div className="w-full bg-gray-800 rounded-full h-1.5 overflow-hidden mb-3">
              <div className={`h-full transition-all duration-500 ${buyStyle.bar}`} style={{ width: `${data.buy_score}%` }} />
            </div>

            <div className="space-y-1.5">
              {buyReasonsList.length > 0 ? (
                buyReasonsList.map((r, i) => (
                  <div key={i} className="text-xs text-gray-300 bg-gray-800/80 px-2.5 py-1.5 rounded-lg border border-gray-700/40 flex items-start gap-1.5 leading-snug break-words">
                    <span className="text-red-400 shrink-0 mt-0.5">•</span>
                    <span className="break-words">{r.title}</span>
                  </div>
                ))
              ) : (
                <div className="text-xs text-gray-400 italic">Không có dấu hiệu rủi ro mua đuổi.</div>
              )}
            </div>
          </div>
          <div className="text-[11px] text-gray-500 mt-3 pt-2 border-t border-gray-800/80">
            {data.buy_score >= 60 ? '⚠️ Cảnh báo: Tránh mở vị thế mua đuổi giá cao' : '✓ Vùng giá an toàn, không có phân kỳ đỉnh'}
          </div>
        </div>

        {/* CARD 2: F-SCORE (RESPONSIVE PROGRESS PILLARS) */}
        <div className="p-4 rounded-xl border border-gray-700/60 bg-gradient-to-b from-gray-800/40 to-gray-900 flex flex-col justify-between min-w-0">
          <div>
            <div className="flex items-center justify-between gap-2 mb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-gray-300 flex items-center gap-1.5 min-w-0 truncate">
                <BarChart3 className="w-4 h-4 text-blue-400 shrink-0" />
                <span className="truncate">Chất Lượng F-Score</span>
              </span>
              <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-md border shrink-0 whitespace-nowrap ${fBadge.color}`}>
                {fBadge.text}
              </span>
            </div>

            <div className="flex items-baseline gap-1.5 mb-2.5">
              <span className="text-3xl sm:text-4xl font-extrabold text-white">
                {data.f_score !== null ? data.f_score : '--'}
              </span>
              <span className="text-xs text-gray-500 font-medium">/ 9 Tiêu chí</span>
            </div>

            <div className="space-y-2 my-2">
              {/* Pillar 1 */}
              <div>
                <div className="flex justify-between text-[11px] sm:text-xs mb-1">
                  <span className="text-gray-300">1. Sinh lời</span>
                  <span className="text-gray-400 font-mono font-medium">
                    {pillars.profitability.score} / {pillars.profitability.max}
                  </span>
                </div>
                <div className="w-full bg-gray-800 rounded-full h-1.5 overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      pillars.profitability.score >= 3 ? 'bg-emerald-500' : pillars.profitability.score >= 2 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${(pillars.profitability.score / pillars.profitability.max) * 100}%` }}
                  />
                </div>
              </div>

              {/* Pillar 2 */}
              <div>
                <div className="flex justify-between text-[11px] sm:text-xs mb-1">
                  <span className="text-gray-300">2. Đòn bẩy & TK</span>
                  <span className="text-gray-400 font-mono font-medium">
                    {pillars.leverage.score} / {pillars.leverage.max}
                  </span>
                </div>
                <div className="w-full bg-gray-800 rounded-full h-1.5 overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      pillars.leverage.score >= 2 ? 'bg-emerald-500' : 'bg-amber-500'
                    }`}
                    style={{ width: `${(pillars.leverage.score / pillars.leverage.max) * 100}%` }}
                  />
                </div>
              </div>

              {/* Pillar 3 */}
              <div>
                <div className="flex justify-between text-[11px] sm:text-xs mb-1">
                  <span className="text-gray-300">3. Hiệu quả HĐ</span>
                  <span className="text-gray-400 font-mono font-medium">
                    {pillars.efficiency.score} / {pillars.efficiency.max}
                  </span>
                </div>
                <div className="w-full bg-gray-800 rounded-full h-1.5 overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      pillars.efficiency.score >= 1 ? 'bg-emerald-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${(pillars.efficiency.score / pillars.efficiency.max) * 100}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="text-[11px] text-gray-400 mt-2 pt-2 border-t border-gray-800/80 flex flex-wrap items-center justify-between gap-1">
            <span>P/E: {valuation?.pe ? `${valuation.pe}x` : '--'} | P/B: {valuation?.pb ? `${valuation.pb}x` : '--'}</span>
            <span
              className="text-blue-400 cursor-pointer hover:underline flex items-center gap-0.5 whitespace-nowrap"
              onClick={() => { setExpanded(true); setActiveTab('fscore'); }}
            >
              Công thức & đối chiếu →
            </span>
          </div>
        </div>

        {/* CARD 3: SELL RISK */}
        <div className={`p-4 rounded-xl border flex flex-col justify-between transition-all min-w-0 ${sellStyle.card}`}>
          <div>
            <div className="flex items-center justify-between gap-2 mb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-gray-300 flex items-center gap-1.5 min-w-0 truncate">
                <TrendingDown className="w-4 h-4 text-gray-400 shrink-0" />
                <span className="truncate">Rủi ro Bán Cạn Cung</span>
              </span>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md border shrink-0 whitespace-nowrap ${sellStyle.badge}`}>
                {data.sell_level}
              </span>
            </div>

            <div className="flex items-baseline gap-1.5 mb-2">
              <span className={`text-3xl sm:text-4xl font-extrabold ${sellStyle.text}`}>{data.sell_score}</span>
              <span className="text-xs text-gray-500 font-medium">/ 100</span>
            </div>

            <div className="w-full bg-gray-800 rounded-full h-1.5 overflow-hidden mb-3">
              <div className={`h-full transition-all duration-500 ${sellStyle.bar}`} style={{ width: `${data.sell_score}%` }} />
            </div>

            <div className="space-y-1.5">
              {sellReasonsList.length > 0 ? (
                sellReasonsList.map((r, i) => (
                  <div key={i} className="text-xs text-gray-300 bg-gray-800/80 px-2.5 py-1.5 rounded-lg border border-gray-700/40 flex items-start gap-1.5 leading-snug break-words">
                    <span className="text-emerald-400 shrink-0 mt-0.5">•</span>
                    <span className="break-words">{r.title}</span>
                  </div>
                ))
              ) : (
                <div className="text-xs text-gray-400 italic">Không có dấu hiệu bán cạn cung / hoảng loạn.</div>
              )}
            </div>
          </div>

          <div className="text-[11px] text-gray-500 mt-3 pt-2 border-t border-gray-800/80">
            {data.sell_score >= 60 ? '⚠️ Cảnh báo: Vùng cạn cung, tránh bán tháo hoảng loạn' : '✓ Áp lực cung bán ở mức bình thường'}
          </div>
        </div>
      </div>

      {/* DECISION SUPPORT SCENARIO */}
      <div className={`mt-4 p-4 rounded-xl border flex items-start gap-3.5 transition-all ${scenarioStyle.card}`}>
        <div className={`p-2.5 rounded-lg shrink-0 ${scenarioStyle.iconBg}`}>
          {scenarioStyle.icon}
        </div>
        <div className="flex-1">
          <div className="text-xs font-semibold uppercase tracking-wider opacity-80 mb-0.5">
            Kịch Bản Đề Xuất (Multi-Factor Decision Support)
          </div>
          <p className="text-sm md:text-base font-bold text-white leading-relaxed">
            {data.scenario}
          </p>
        </div>
      </div>

      {/* EXPANDABLE DETAILS & VERIFICATION PANEL */}
      {expanded && (
        <div className="mt-5 pt-5 border-t border-gray-700/80 animate-in fade-in duration-300">
          {/* TABS HEADER */}
          <div className="flex flex-wrap items-center gap-2 border-b border-gray-700 pb-3 mb-4">
            <button
              onClick={() => setActiveTab('fscore')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5 ${
                activeTab === 'fscore' ? 'bg-blue-600 text-white shadow-md' : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
              }`}
            >
              <Calculator className="w-3.5 h-3.5" />
              9 Tiêu Chí & Công Thức ({data.f_score ?? 0}/9)
            </button>

            <button
              onClick={() => setActiveTab('audit')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5 ${
                activeTab === 'audit' ? 'bg-blue-600 text-white shadow-md' : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
              }`}
            >
              <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-400" />
              Bảng Đối Chiếu Số Liệu Gốc BCTC (Verify)
            </button>

            <button
              onClick={() => setActiveTab('technical')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5 ${
                activeTab === 'technical' ? 'bg-blue-600 text-white shadow-md' : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
              }`}
            >
              <Activity className="w-3.5 h-3.5" />
              Thành Phần Điểm Rủi Ro Kỹ Thuật
            </button>

            <button
              onClick={() => setActiveTab('valuation')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5 ${
                activeTab === 'valuation' ? 'bg-blue-600 text-white shadow-md' : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
              }`}
            >
              <BookOpen className="w-3.5 h-3.5" />
              Chỉ Số Định Giá & Tổng Quan
            </button>
          </div>

          {/* TAB 1: 9 PIOTROSKI F-SCORE CRITERIA WITH FORMULAS */}
          {activeTab === 'fscore' && (
            <div className="space-y-4">
              <div className="text-xs text-gray-300 bg-blue-950/20 p-3 rounded-lg border border-blue-500/30 flex items-start gap-2.5">
                <HelpCircle className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
                <div className="leading-relaxed">
                  <strong>Hướng dẫn đối chiếu:</strong> Mỗi tiêu chí dưới đây được trích xuất trực tiếp từ Báo cáo tài chính kiểm toán của 2 niên độ gần nhất ({latestYear} và {priorYear}). Bạn có thể bấm vào từng tiêu chí để xem công thức toán học, phép tính số thật và mã mục tài chính tương ứng.
                </div>
              </div>

              {signals.length > 0 ? (
                <div className="grid grid-cols-1 @2xl:grid-cols-3 gap-3.5">
                  {['Sinh lời', 'Đòn bẩy', 'Hiệu quả'].map((pillarName, idx) => {
                    const pillarPassed = signals.filter((s) => s.pillar === pillarName && s.passed).length;
                    const pillarTotal = signals.filter((s) => s.pillar === pillarName).length;
                    return (
                      <div key={pillarName} className="bg-gray-900/70 border border-gray-700/60 rounded-xl p-3.5 min-w-0">
                        <div className="text-xs font-bold text-gray-200 pb-2.5 mb-3 border-b border-gray-700/60 flex items-center justify-between gap-2">
                          <span className="whitespace-nowrap font-bold text-gray-100">
                            Trụ cột {idx + 1}: {pillarName}
                          </span>
                          <span className="text-[11px] font-semibold text-gray-300 bg-gray-800 px-2 py-0.5 rounded border border-gray-700 shrink-0">
                            {pillarPassed}/{pillarTotal} đạt
                          </span>
                        </div>

                        <div className="space-y-2.5">
                          {signals
                            .filter((s) => s.pillar === pillarName)
                            .map((sig) => {
                              const isDetailOpen = expandedSignalId === sig.id;
                              return (
                                <div
                                  key={sig.id}
                                  className={`rounded-lg border text-xs transition-all overflow-hidden ${
                                    sig.passed
                                      ? 'bg-emerald-950/20 border-emerald-500/30'
                                      : 'bg-rose-950/20 border-rose-500/20'
                                  }`}
                                >
                                  <div
                                    className="p-3 cursor-pointer flex flex-col gap-2 select-none"
                                    onClick={() => setExpandedSignalId(isDetailOpen ? null : sig.id)}
                                  >
                                    <div className="flex items-start justify-between gap-2">
                                      <span className="font-bold text-gray-100 leading-snug">
                                        {sig.id}. {sig.title}
                                      </span>
                                      {sig.passed ? (
                                        <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                                      ) : (
                                        <XCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                                      )}
                                    </div>

                                    <div className="flex flex-wrap items-center justify-between gap-2">
                                      {sig.value && (
                                        <div className="text-[11px] font-mono text-gray-200 bg-black/40 px-2 py-0.5 rounded border border-gray-700/40 break-all font-semibold">
                                          {sig.value}
                                        </div>
                                      )}
                                      <span className="text-[11px] text-blue-400 hover:underline flex items-center gap-0.5 font-medium ml-auto shrink-0">
                                        {isDetailOpen ? 'Ẩn công thức' : 'Chi tiết phép tính'}
                                        {isDetailOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                                      </span>
                                    </div>

                                    <p className="text-[11px] text-gray-400 leading-relaxed">{sig.desc}</p>
                                  </div>

                                {/* DROPDOWN FORMULA BREAKDOWN */}
                                {isDetailOpen && (
                                  <div className="p-2.5 pt-2 bg-black/50 border-t border-gray-700/60 space-y-1.5 text-[11px]">
                                    {sig.formula && (
                                      <div>
                                        <span className="text-gray-400 font-medium">📐 Công thức: </span>
                                        <span className="text-blue-300 font-mono">{sig.formula}</span>
                                      </div>
                                    )}
                                    {sig.calculation && (
                                      <div>
                                        <span className="text-gray-400 font-medium">🔢 Phép tính: </span>
                                        <span className="text-yellow-300 font-mono">{sig.calculation}</span>
                                      </div>
                                    )}
                                    {sig.source_statement && (
                                      <div>
                                        <span className="text-gray-400 font-medium">📄 Nguồn: </span>
                                        <span className="text-gray-300">{sig.source_statement}</span>
                                      </div>
                                    )}
                                    {sig.condition && (
                                      <div>
                                        <span className="text-gray-400 font-medium">⚖️ Điều kiện xét: </span>
                                        <span className="text-emerald-300 font-semibold">{sig.condition}</span>
                                      </div>
                                    )}
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="p-4 bg-gray-900/40 text-gray-400 text-xs text-center rounded-lg">
                  Doanh nghiệp chưa công bố đủ lịch sử 2 năm BCTC kiểm toán trên hệ thống.
                </div>
              )}
            </div>
          )}

          {/* TAB 2: AUDIT & VERIFICATION STATEMENT TABLE */}
          {activeTab === 'audit' && (
            <div className="space-y-4">
              <div className="text-xs text-gray-300 bg-emerald-950/20 p-3 rounded-lg border border-emerald-500/30 flex items-start gap-2.5">
                <FileSpreadsheet className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <div className="leading-relaxed">
                  <strong>Bảng kiểm chứng số liệu gốc (Audit Trail):</strong> Toàn bộ 9 chỉ tiêu cấu thành F-Score được trích xuất từ BCTC đã kiểm toán của {symbol} trong 2 niên độ gần nhất ({latestYear} và {priorYear}). Bạn có thể mở Báo cáo tài chính gốc của doanh nghiệp để đối chiếu trực tiếp từng con số.
                </div>
              </div>

              {statementTable.length > 0 ? (
                <div className="overflow-x-auto rounded-xl border border-gray-700/60 bg-gray-900/80">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="bg-gray-800/80 border-b border-gray-700/80 text-gray-300 uppercase tracking-wider font-semibold text-[11px]">
                        <th className="py-2.5 px-3">Khoản mục BCTC</th>
                        <th className="py-2.5 px-3">Báo cáo nguồn & Mã</th>
                        <th className="py-2.5 px-3 text-right">Năm {latestYear}</th>
                        <th className="py-2.5 px-3 text-right">Năm {priorYear}</th>
                        <th className="py-2.5 px-3 text-right">Chênh lệch YoY</th>
                        <th className="py-2.5 px-3">Ứng dụng trong F-Score</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-800">
                      {statementTable.map((item, idx) => {
                        const diff = item.val_t - item.val_t1;
                        const pctChange = item.val_t1 !== 0 ? ((diff / Math.abs(item.val_t1)) * 100) : 0;
                        return (
                          <tr key={idx} className="hover:bg-gray-800/40 transition-colors">
                            <td className="py-2 px-3 font-semibold text-gray-200">{item.item_name}</td>
                            <td className="py-2 px-3 text-gray-400 text-[11px] font-mono">
                              <span className="px-1.5 py-0.5 bg-gray-800 rounded border border-gray-700">{item.item_code}</span>
                            </td>
                            <td className="py-2 px-3 text-right font-mono font-bold text-white">
                              {item.val_t.toLocaleString()} <span className="text-[10px] text-gray-400 font-normal">{item.unit}</span>
                            </td>
                            <td className="py-2 px-3 text-right font-mono text-gray-300">
                              {item.val_t1.toLocaleString()} <span className="text-[10px] text-gray-500 font-normal">{item.unit}</span>
                            </td>
                            <td className="py-2 px-3 text-right font-mono">
                              <span
                                className={`text-[11px] font-medium ${
                                  diff > 0 ? 'text-emerald-400' : diff < 0 ? 'text-rose-400' : 'text-gray-400'
                                }`}
                              >
                                {diff > 0 ? '+' : ''}
                                {diff.toLocaleString()} ({diff > 0 ? '+' : ''}{pctChange.toFixed(1)}%)
                              </span>
                            </td>
                            <td className="py-2 px-3 text-[11px] text-blue-300 font-medium">{item.used_in}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="p-4 bg-gray-900/40 text-gray-400 text-xs text-center rounded-lg">
                  Chưa có bảng dữ liệu đối chiếu cho mã này.
                </div>
              )}
            </div>
          )}

          {/* TAB 3: TECHNICAL COMPONENTS */}
          {activeTab === 'technical' && (
            <div className="space-y-4">
              <div className="text-xs text-gray-400 bg-gray-900/60 p-3 rounded-lg border border-gray-700/50 flex items-center gap-2">
                <Info className="w-4 h-4 text-blue-400 shrink-0" />
                <span>
                  <strong>Hệ thống Chấm điểm Rủi ro (High-Risk Framework):</strong> Thang điểm 0–100 đánh giá độc lập nguy cơ mua đuổi đỉnh hoặc bán tháo đáy. Có áp dụng cổng xác nhận (Confirmation Gate) và cờ biên độ trần/sàn HOSE/HNX.
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* BUY SCORE BREAKDOWN */}
                <div className="bg-gray-900/70 border border-gray-700/60 rounded-xl p-4">
                  <h4 className="text-xs font-bold text-red-400 uppercase tracking-wider mb-3 flex items-center justify-between">
                    <span>Thành phần cấu thành BUY_RISK</span>
                    <span>{data.buy_score}/100</span>
                  </h4>

                  <div className="space-y-2.5 text-xs">
                    <div className="flex justify-between items-center text-gray-300">
                      <span>1. Động lượng suy kiệt (Phân kỳ RSI/MACD)</span>
                      <span className="font-mono text-gray-200">{data.details?.buy_components?.momentum ?? 0}/25</span>
                    </div>
                    <div className="flex justify-between items-center text-gray-300">
                      <span>2. Phân phối giá–khối lượng (Râu nến & Vol cao)</span>
                      <span className="font-mono text-gray-200">{data.details?.buy_components?.distribution ?? 0}/25</span>
                    </div>
                    <div className="flex justify-between items-center text-gray-300">
                      <span>3. Biến động cực trị (Z-Score & ATR)</span>
                      <span className="font-mono text-gray-200">{data.details?.buy_components?.extremes ?? 0}/20</span>
                    </div>
                    <div className="flex justify-between items-center text-gray-300">
                      <span>4. Cấu trúc giá (Gãy hỗ trợ / Pivot High)</span>
                      <span className="font-mono text-gray-200">{data.details?.buy_components?.structure ?? 0}/15</span>
                    </div>
                    <div className="flex justify-between items-center text-gray-300">
                      <span>5. Bối cảnh thị trường (Yếu hơn VN-Index)</span>
                      <span className="font-mono text-gray-200">{data.details?.buy_components?.context ?? 0}/15</span>
                    </div>
                  </div>
                </div>

                {/* SELL SCORE BREAKDOWN */}
                <div className="bg-gray-900/70 border border-gray-700/60 rounded-xl p-4">
                  <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider mb-3 flex items-center justify-between">
                    <span>Thành phần cấu thành SELL_RISK</span>
                    <span>{data.sell_score}/100</span>
                  </h4>

                  <div className="space-y-2.5 text-xs">
                    <div className="flex justify-between items-center text-gray-300">
                      <span>1. Quá bán & Phân kỳ tăng (RSI Bull Div)</span>
                      <span className="font-mono text-gray-200">{data.details?.sell_components?.oversold ?? 0}/30</span>
                    </div>
                    <div className="flex justify-between items-center text-gray-300">
                      <span>2. Capitulation giá–khối lượng (Rút chân cạn cung)</span>
                      <span className="font-mono text-gray-200">{data.details?.sell_components?.capitulation ?? 0}/25</span>
                    </div>
                    <div className="flex justify-between items-center text-gray-300">
                      <span>3. Biến động hoảng loạn (Top 5% phiên xấu)</span>
                      <span className="font-mono text-gray-200">{data.details?.sell_components?.panic ?? 0}/15</span>
                    </div>
                    <div className="flex justify-between items-center text-gray-300">
                      <span>4. Xác nhận hồi phục (Vượt đỉnh nến trước)</span>
                      <span className="font-mono text-gray-200">{data.details?.sell_components?.recovery ?? 0}/15</span>
                    </div>
                    <div className="flex justify-between items-center text-gray-300">
                      <span>5. Bối cảnh thị trường (Mạnh hơn VN-Index)</span>
                      <span className="font-mono text-gray-200">{data.details?.sell_components?.context ?? 0}/15</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: VALUATION & RAW FINANCIALS */}
          {activeTab === 'valuation' && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-gray-900/80 p-3 rounded-lg border border-gray-700/50">
                  <div className="text-[11px] text-gray-400 mb-1">P/E Trailing</div>
                  <div className="text-lg font-bold text-white">{valuation?.pe ? `${valuation.pe}x` : 'N/A'}</div>
                  <div className="text-[10px] text-gray-500">Giá / Thu nhập mỗi cp</div>
                </div>

                <div className="bg-gray-900/80 p-3 rounded-lg border border-gray-700/50">
                  <div className="text-[11px] text-gray-400 mb-1">P/B</div>
                  <div className="text-lg font-bold text-white">{valuation?.pb ? `${valuation.pb}x` : 'N/A'}</div>
                  <div className="text-[10px] text-gray-500">Giá / Giá trị sổ sách</div>
                </div>

                <div className="bg-gray-900/80 p-3 rounded-lg border border-gray-700/50">
                  <div className="text-[11px] text-gray-400 mb-1">ROE</div>
                  <div className="text-lg font-bold text-emerald-400">{valuation?.roe ? `${valuation.roe}%` : 'N/A'}</div>
                  <div className="text-[10px] text-gray-500">Sinh lời trên VCSH</div>
                </div>

                <div className="bg-gray-900/80 p-3 rounded-lg border border-gray-700/50">
                  <div className="text-[11px] text-gray-400 mb-1">D/E (Nợ / VCSH)</div>
                  <div className="text-lg font-bold text-white">{valuation?.debt_to_equity ? `${valuation.debt_to_equity}x` : 'N/A'}</div>
                  <div className="text-[10px] text-gray-500">Mức độ sử dụng đòn bẩy</div>
                </div>
              </div>

              {rawMetrics && (
                <div className="bg-gray-900/60 p-4 rounded-xl border border-gray-700/50 text-xs">
                  <h4 className="font-semibold text-gray-300 mb-2">Số Liệu Tài Chính Niên Độ Gần Nhất ({latestYear}):</h4>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-gray-300 font-mono">
                    <div>Doanh thu: <span className="text-white font-bold">{rawMetrics.revenue_bil ?? '--'} tỷ</span></div>
                    <div>LNST: <span className="text-white font-bold">{rawMetrics.net_income_bil ?? '--'} tỷ</span></div>
                    <div>Dòng tiền CFO: <span className="text-white font-bold">{rawMetrics.cfo_bil ?? '--'} tỷ</span></div>
                    <div>ROA: <span className="text-white font-bold">{rawMetrics.roa_pct ?? '--'}%</span></div>
                    <div>Thanh toán hiện hành: <span className="text-white font-bold">{rawMetrics.current_ratio ?? '--'}x</span></div>
                    <div>Biên lãi gộp: <span className="text-white font-bold">{rawMetrics.gross_margin_pct ?? '--'}%</span></div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
