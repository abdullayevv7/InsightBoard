/**
 * Area Chart component using Recharts.
 * Supports stacked areas, gradients, and multiple series.
 */

import React from "react";
import {
  AreaChart as RechartsAreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { ChartDataPoint, SeriesConfig, getChartColor, formatAxisTick } from "../../utils/chartHelpers";

interface AreaChartProps {
  data: ChartDataPoint[];
  xKey: string;
  series: SeriesConfig[];
  height?: number;
  stacked?: boolean;
  showGrid?: boolean;
  showLegend?: boolean;
  gradient?: boolean;
  curved?: boolean;
  tooltipFormatter?: (value: number) => string;
}

const AreaChartComponent: React.FC<AreaChartProps> = ({
  data,
  xKey,
  series,
  height = 300,
  stacked = false,
  showGrid = true,
  showLegend = true,
  gradient = true,
  curved = true,
  tooltipFormatter,
}) => {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        No data available
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsAreaChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
        {gradient && (
          <defs>
            {series.map((s, index) => {
              const color = s.color || getChartColor(index);
              return (
                <linearGradient key={s.dataKey} id={`gradient-${s.dataKey}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={color} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={color} stopOpacity={0.05} />
                </linearGradient>
              );
            })}
          </defs>
        )}
        {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />}
        <XAxis dataKey={xKey} tick={{ fontSize: 12 }} tickLine={false} />
        <YAxis tickFormatter={formatAxisTick} tick={{ fontSize: 12 }} tickLine={false} />
        <Tooltip
          contentStyle={{
            backgroundColor: "#fff",
            border: "1px solid #e5e7eb",
            borderRadius: "8px",
            boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
          }}
          formatter={tooltipFormatter ? (value: number) => [tooltipFormatter(value)] : undefined}
        />
        {showLegend && (
          <Legend wrapperStyle={{ paddingTop: 10, fontSize: 12 }} />
        )}
        {series.map((s, index) => {
          const color = s.color || getChartColor(index);
          return (
            <Area
              key={s.dataKey}
              type={curved ? "monotone" : "linear"}
              dataKey={s.dataKey}
              name={s.name}
              stroke={color}
              strokeWidth={2}
              fill={gradient ? `url(#gradient-${s.dataKey})` : color}
              fillOpacity={gradient ? 1 : 0.2}
              stackId={stacked ? "stack" : undefined}
              connectNulls
            />
          );
        })}
      </RechartsAreaChart>
    </ResponsiveContainer>
  );
};

export default AreaChartComponent;
