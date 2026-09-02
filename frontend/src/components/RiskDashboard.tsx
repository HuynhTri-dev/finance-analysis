'use client';

import React, { useEffect, useState } from 'react';
import { analyzeApi } from '@/lib/api';
import { PolarAngleAxis, PolarGrid, PolarRadiusAxis, Radar, RadarChart, ResponsiveContainer, Tooltip } from 'recharts';
import { AlertTriangle, AlertCircle, ShieldCheck, Activity } from 'lucide-react';

interface RiskData {
  symbol: string;
  as_of_date: string;
  f_score: number;
  buy_score: number;
  sell_score: number;
  buy_level: string;
  sell_level: string;
  scenario: string;
  details: {
    buy_reasons: string[];
    sell_reasons: string[];
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

  const fetchRiskData = async (forceRefresh: boolean = false) => {
    try {
      if (forceRefresh) setRefreshing(true);
      const data = await analyzeApi.getRiskAnalysis(symbol, forceRefresh);
      setData(data);
      setError(null);
    } catch (err) {
      console.error(err);
      setError("Không thể lấy dữ liệu phân tích rủi ro.");
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

  if (loading) return <div className="p-4 bg-gray-900 rounded-lg text-gray-400 animate-pulse h-64 flex items-center justify-center">Đang phân tích rủi ro & định giá...</div>;
  if (error) return <div className="p-4 bg-red-900/20 text-red-400 rounded-lg">{error}</div>;
  if (!data) return null;

  // Radar chart data for F-Score (Mock presentation, since F-Score is 0-9)
  const radarData = [
    { subject: 'Sinh lời', A: data.f_score > 3 ? 100 : (data.f_score * 20), fullMark: 100 },
    { subject: 'Đòn bẩy', A: data.f_score > 6 ? 100 : (data.f_score * 15), fullMark: 100 },
    { subject: 'Hiệu quả', A: data.f_score > 8 ? 100 : (data.f_score * 10), fullMark: 100 },
  ];

  const getRiskColor = (score: number) => {
    if (score >= 75) return 'text-red-500 bg-red-500/10 border-red-500/20';
    if (score >= 60) return 'text-orange-500 bg-orange-500/10 border-orange-500/20';
    if (score >= 40) return 'text-yellow-500 bg-yellow-500/10 border-yellow-500/20';
    return 'text-green-500 bg-green-500/10 border-green-500/20';
  };

  const getIcon = (score: number) => {
    if (score >= 75) return <AlertTriangle className="w-5 h-5 mb-1" />;
    if (score >= 60) return <AlertCircle className="w-5 h-5 mb-1" />;
    if (score >= 40) return <Activity className="w-5 h-5 mb-1" />;
    return <ShieldCheck className="w-5 h-5 mb-1" />;
  };

  return (
    <div className="bg-gray-800 border border-gray-700/50 rounded-xl p-5 mt-6 shadow-xl">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            Phân Tích Cơ Bản & Rủi Ro <span className="text-sm font-normal text-gray-400 px-2 py-0.5 bg-gray-700/50 rounded-md">{data.as_of_date}</span>
          </h2>
          <p className="text-gray-400 text-sm mt-1">Kết hợp Piotroski F-Score và Kỹ thuật</p>
        </div>
        <button
          onClick={() => fetchRiskData(true)}
          disabled={refreshing}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors flex items-center gap-2"
        >
          {refreshing ? 'Đang tính lại...' : 'Làm mới dữ liệu'}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

        {/* BUY RISK */}
        <div className={`p-5 rounded-xl border flex flex-col items-center justify-center text-center ${getRiskColor(data.buy_score)}`}>
          {getIcon(data.buy_score)}
          <div className="text-sm font-semibold uppercase tracking-wider mb-2 opacity-80">Rủi ro Mua Đuổi</div>
          <div className="text-5xl font-bold mb-2">{data.buy_score}</div>
          <div className="text-xs font-medium px-3 py-1 bg-black/20 rounded-full">{data.buy_level}</div>
          <div className="mt-3 text-xs text-left w-full space-y-1 opacity-90">
            {data.details.buy_reasons.map((r, i) => <div key={i}>• {r}</div>)}
          </div>
        </div>

        {/* F-SCORE RADAR */}
        <div className="p-4 rounded-xl border border-gray-700/50 bg-gray-900/30 flex flex-col items-center">
          <div className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-2">Chất lượng (F-Score)</div>
          <div className="text-3xl font-bold text-white mb-2">{data.f_score} <span className="text-gray-500 text-lg">/ 9</span></div>
          <div className="w-full h-40">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
                <PolarGrid stroke="#374151" />
                <PolarAngleAxis dataKey="subject" tick={{ fill: '#9CA3AF', fontSize: 10 }} />
                <Radar name="F-Score" dataKey="A" stroke="#3B82F6" fill="#3B82F6" fillOpacity={0.4} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* SELL RISK */}
        <div className={`p-5 rounded-xl border flex flex-col items-center justify-center text-center ${getRiskColor(data.sell_score)}`}>
          {getIcon(data.sell_score)}
          <div className="text-sm font-semibold uppercase tracking-wider mb-2 opacity-80">Rủi ro Bán Cạn Cung</div>
          <div className="text-5xl font-bold mb-2">{data.sell_score}</div>
          <div className="text-xs font-medium px-3 py-1 bg-black/20 rounded-full">{data.sell_level}</div>
          <div className="mt-3 text-xs text-left w-full space-y-1 opacity-90">
            {data.details.sell_reasons.map((r, i) => <div key={i}>• {r}</div>)}
          </div>
        </div>

      </div>

      <div className="mt-6 p-4 bg-gray-900/50 rounded-lg border border-gray-700/50 flex items-start gap-4">
        <div className="p-2 bg-blue-500/20 text-blue-400 rounded-full">
          <Activity className="w-6 h-6" />
        </div>
        <div>
          <h3 className="text-gray-300 text-sm font-medium mb-1">Kịch Bản Đề Xuất (Decision Support)</h3>
          <p className="text-lg font-bold text-white leading-relaxed">{data.scenario}</p>
        </div>
      </div>
    </div>
  );
};
