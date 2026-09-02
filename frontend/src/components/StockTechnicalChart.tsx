/**
 * @file StockTechnicalChart.tsx
 * @description Advanced financial technical analysis chart utilizing Recharts.
 * Renders high-performance Japanese Candlestick (OHLC) bars, volume overlays,
 * MA20/MA50 overlays, and a synced secondary RSI (Relative Strength Index) line chart pane.
 */

"use client";

import React, { useState } from "react";
import { format } from "date-fns";
import { BarChart3, RefreshCw, TrendingUp } from "lucide-react";
import {
  ComposedChart,
  Line,
  Bar,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  ReferenceLine,
} from "recharts";

export interface StockTechnicalChartProps {
  chartRecords: any[];
  loadingDetail: boolean;
  selectedTimeframe: string;
  onTimeframeChange: (timeframe: string) => void;
  showMAs: boolean;
  onToggleMAs: () => void;
}

/**
 * Custom Candlestick shape renderer for Recharts Bar.
 * Draws the wick (high to low) and body (open to close) for each trading record.
 */
const CandlestickShape = (props: any) => {
  const { x, y, width, height, payload } = props;
  if (!payload) return null;

  const { open, close, high, low } = payload;
  if (open === undefined || close === undefined || high === undefined || low === undefined) {
    return null;
  }

  const isUp = close >= open;
  const color = isUp ? "#22c55e" : "#ef4444"; // Green for gain, Red for loss

  const priceDiff = Math.abs(close - open);
  // Scale factor (pixels per unit of price)
  // If priceDiff is 0 (Doji), use a fallback or default scale
  const scaleFactor = priceDiff > 0 ? height / priceDiff : 1.0;

  // Body top and bottom coordinates
  const yOpen = isUp ? y + height : y;
  const yClose = isUp ? y : y + height;

  // Wick coordinates (higher price has smaller Y coordinate in SVG)
  const yHigh = yOpen - (high - open) * scaleFactor;
  const yLow = yOpen - (low - open) * scaleFactor;

  const centerX = x + width / 2;

  return (
    <g>
      {/* Wick / Shadow (High to Low) */}
      <line
        x1={centerX}
        y1={yHigh}
        x2={centerX}
        y2={yLow}
        stroke={color}
        strokeWidth={1.5}
      />
      {/* Real Body (Open to Close) */}
      <rect
        x={x}
        y={y}
        width={width}
        height={Math.max(height, 1)}
        fill={color}
        stroke={color}
        strokeWidth={1}
      />
    </g>
  );
};

export const StockTechnicalChart: React.FC<StockTechnicalChartProps> = ({
  chartRecords,
  loadingDetail,
  selectedTimeframe,
  onTimeframeChange,
  showMAs,
  onToggleMAs,
}) => {
  const [showBB, setShowBB] = useState<boolean>(false);
  return (
    <div className="bg-[#161B22] border border-[#30363D] rounded-xl p-4 sm:p-5 shadow-sm space-y-4">
      {/* Header controls bar */}
      <div className="flex flex-wrap items-center justify-between pb-3 border-b border-[#30363D]/80 gap-3">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1.5 text-xs font-semibold text-gray-200">
            <BarChart3 size={16} className="text-blue-400" />
          </div>

          <button
            onClick={onToggleMAs}
            className={`text-[11px] px-2 py-0.5 rounded border transition-colors ${showMAs
                ? "bg-blue-500/20 text-blue-400 border-blue-500/40"
                : "bg-[#21262D] text-gray-400 border-[#30363D]"
              }`}
          >
            MA20 / MA50
          </button>

          <button
            onClick={() => setShowBB(!showBB)}
            className={`text-[11px] px-2 py-0.5 rounded border transition-colors ${showBB
                ? "bg-blue-500/20 text-blue-400 border-blue-500/40"
                : "bg-[#21262D] text-gray-400 border-[#30363D]"
              }`}
          >
            Dải Bollinger
          </button>
        </div>

        {/* Timeframe Buttons */}
        <div className="flex items-center space-x-1 bg-[#0D1117] p-1 rounded-lg border border-[#30363D]">
          {["1M", "3M", "6M", "1Y"].map((tf) => (
            <button
              key={tf}
              onClick={() => onTimeframeChange(tf)}
              className={`px-2.5 sm:px-3 py-1 text-xs font-semibold rounded-md transition-all ${selectedTimeframe === tf
                  ? "bg-blue-600 text-white shadow"
                  : "text-gray-400 hover:text-gray-200 hover:bg-[#21262D]"
                }`}
            >
              {tf}
            </button>
          ))}
        </div>
      </div>

      {loadingDetail ? (
        <div className="flex items-center justify-center h-[380px] text-xs text-gray-400">
          <RefreshCw className="animate-spin mr-2" size={16} />
          Đang cập nhật biểu đồ...
        </div>
      ) : chartRecords && chartRecords.length > 0 ? (
        <div className="space-y-4">
          {/* Pane 1: Candlestick Price + MA + Volume Chart */}
          <div className="h-[250px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart
                data={chartRecords}
                syncId="stockChart"
                margin={{ top: 10, right: 35, left: 5, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#21262D" vertical={false} />
                <XAxis
                  dataKey="time"
                  hide
                />
                <YAxis
                  yAxisId="price"
                  orientation="right"
                  domain={["auto", "auto"]}
                  stroke="#6E7681"
                  tick={{ fontSize: 11, fill: "#9CA3AF" }}
                  axisLine={{ stroke: "#30363D" }}
                  tickLine={{ stroke: "#30363D" }}
                  tickFormatter={(val) => (val >= 1000 ? `${(val / 1000).toFixed(0)}k` : val)}
                />
                <YAxis yAxisId="vol" orientation="right" domain={[0, "dataMax * 3.5"]} hide />

                <Tooltip
                  content={({ active, payload, label }) => {
                    if (active && payload && payload.length) {
                      const d = payload[0].payload;
                      return (
                        <div className="bg-[#161B22] border border-[#30363D] p-3 rounded-lg shadow-xl text-xs space-y-1 z-50">
                          <div className="font-bold text-gray-200 border-b border-[#30363D] pb-1">
                            {d.time ? format(new Date(d.time), "dd/MM/yyyy") : label}
                          </div>
                          <div className="grid grid-cols-2 gap-x-4 gap-y-0.5 text-[11px] pt-1">
                            <span className="text-gray-400">Đóng cửa:</span>
                            <span className="font-bold text-emerald-400 text-right">
                              {d.close?.toLocaleString()}
                            </span>
                            <span className="text-gray-400">Mở cửa:</span>
                            <span className="text-gray-200 text-right">{d.open?.toLocaleString()}</span>
                            <span className="text-gray-400">Cao nhất:</span>
                            <span className="text-emerald-300 text-right">{d.high?.toLocaleString()}</span>
                            <span className="text-gray-400">Thấp nhất:</span>
                            <span className="text-rose-300 text-right">{d.low?.toLocaleString()}</span>
                            <span className="text-gray-400">Khối lượng:</span>
                            <span className="text-blue-400 text-right">{d.volume?.toLocaleString()}</span>
                            {d.ma20 && (
                              <>
                                <span className="text-amber-400">MA20:</span>
                                <span className="text-amber-300 text-right">
                                  {d.ma20?.toLocaleString()}
                                </span>
                              </>
                            )}
                            {d.ma50 && (
                              <>
                                <span className="text-purple-400">MA50:</span>
                                <span className="text-purple-300 text-right">
                                  {d.ma50?.toLocaleString()}
                                </span>
                              </>
                            )}
                            {d.rsi && (
                              <>
                                <span className="text-pink-400">RSI (14):</span>
                                <span className="text-pink-300 text-right">{d.rsi}</span>
                              </>
                            )}
                            {d.bb_upper && d.bb_lower && (
                              <>
                                <span className="text-blue-400">BB Upper:</span>
                                <span className="text-blue-300 text-right">{d.bb_upper?.toLocaleString()}</span>
                                <span className="text-blue-400">BB Lower:</span>
                                <span className="text-blue-300 text-right">{d.bb_lower?.toLocaleString()}</span>
                              </>
                            )}
                          </div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />

                {/* Current Price Dashed Reference Line */}
                {chartRecords[chartRecords.length - 1]?.close !== undefined && (
                  <ReferenceLine
                    yAxisId="price"
                    y={chartRecords[chartRecords.length - 1].close}
                    stroke={
                      (chartRecords[chartRecords.length - 1].close >=
                        (chartRecords[chartRecords.length - 1].open || 0))
                        ? "#22c55e"
                        : "#ef4444"
                    }
                    strokeDasharray="2 2"
                    strokeWidth={1}
                    opacity={0.8}
                  />
                )}

                {/* Volume Bar */}
                <Bar
                  yAxisId="vol"
                  dataKey="volume"
                  fill="#238636"
                  opacity={0.2}
                  radius={[2, 2, 0, 0]}
                  barSize={8}
                />

                {/* Moving Average Overlays */}
                {showMAs && (
                  <>
                    <Line
                      yAxisId="price"
                      type="monotone"
                      dataKey="ma20"
                      stroke="#F59E0B"
                      dot={false}
                      strokeWidth={1.2}
                      name="MA20"
                    />
                    <Line
                      yAxisId="price"
                      type="monotone"
                      dataKey="ma50"
                      stroke="#8B5CF6"
                      dot={false}
                      strokeWidth={1.2}
                      name="MA50"
                    />
                  </>
                )}

                {/* Bollinger Bands Overlay */}
                {showBB && (
                  <>
                    <Area
                      yAxisId="price"
                      type="monotone"
                      dataKey={(d: any) => [d.bb_lower, d.bb_upper]}
                      stroke="none"
                      fill="#2196F3"
                      fillOpacity={0.06}
                      name="Dải Bollinger"
                    />
                    <Line
                      yAxisId="price"
                      type="monotone"
                      dataKey="bb_upper"
                      stroke="#2196F3"
                      strokeWidth={1}
                      strokeDasharray="3 3"
                      dot={false}
                      name="BB Upper"
                    />
                    <Line
                      yAxisId="price"
                      type="monotone"
                      dataKey="bb_lower"
                      stroke="#2196F3"
                      strokeWidth={1}
                      strokeDasharray="3 3"
                      dot={false}
                      name="BB Lower"
                    />
                  </>
                )}

                {/* Candlestick Body & Wicks */}
                <Bar
                  yAxisId="price"
                  dataKey={(d: any) => [d.open, d.close]}
                  shape={<CandlestickShape />}
                  name="Candlestick"
                  barSize={7}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          {/* Pane 2: Synced RSI Line Chart */}
          <div className="h-[90px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart
                data={chartRecords}
                syncId="stockChart"
                margin={{ top: 5, right: 35, left: 5, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#21262D" vertical={false} />
                <XAxis
                  dataKey="time"
                  tickFormatter={(timeStr) => {
                    try {
                      return format(new Date(timeStr), "dd/MM");
                    } catch {
                      return timeStr;
                    }
                  }}
                  stroke="#6E7681"
                  tick={{ fontSize: 10 }}
                  minTickGap={25}
                />
                <YAxis
                  yAxisId="rsiAxis"
                  orientation="right"
                  domain={[0, 100]}
                  ticks={[30, 50, 70]}
                  stroke="#6E7681"
                  tick={{ fontSize: 9, fill: "#9CA3AF" }}
                  axisLine={{ stroke: "#30363D" }}
                  tickLine={{ stroke: "#30363D" }}
                />

                {/* Boundaries Reference Lines for Overbought (70) and Oversold (30) */}
                <ReferenceLine yAxisId="rsiAxis" y={70} stroke="#ef4444" strokeDasharray="3 3" opacity={0.5} />
                <ReferenceLine yAxisId="rsiAxis" y={30} stroke="#22c55e" strokeDasharray="3 3" opacity={0.5} />
                <ReferenceLine yAxisId="rsiAxis" y={50} stroke="#6E7681" strokeDasharray="3 3" opacity={0.3} />

                {/* RSI Line */}
                <Line
                  yAxisId="rsiAxis"
                  type="monotone"
                  dataKey="rsi"
                  stroke="#ec4899"
                  dot={false}
                  strokeWidth={1.5}
                  name="RSI"
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center h-[380px] text-gray-500">
          <TrendingUp size={40} className="text-gray-700 mb-2" />
          <p className="text-xs">
            Không có dữ liệu biểu đồ cho mã này trong khoảng thời gian đã chọn
          </p>
        </div>
      )}
    </div>
  );
};
