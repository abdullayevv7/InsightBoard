/**
 * Line Chart component using Recharts.
 * Supports multiple series, custom colors, tooltips, and responsive sizing.
 */

import React from "react";
import {
  LineChart as RechartsLineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { ChartDataPoint, SeriesConfig, getChartColor, formatAxisTick } from "../../utils/chartHelpers";

interface LineChartProps {
  data: ChartDataPoint[];
  xKey: string;
  series: SeriesConfig[];
  height?: number;
  showGrid?: boolean;
  showLegend?: boolean;
  showDots?: boolean;
  curved?: boolean;
  xAxisLabel?: string;
  yAxisLabel?: string;
  tooltipFormatter?: (value: number) => string;
}

const LineChartComponent: React.FC<LineChartProps> = ({
  data,
  xKey,
  series,
  height = 300,
  showGrid = true,
  showLegend = true,
  showDots = true,
  curved = true,
  xAxisLabel,
  yAxisLabel,
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
      <RechartsLineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
        {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />}
        <XAxis
          dataKey={xKey}
          tick={{ fontSize: 12 }}
          tickLine={false}
          axisLine={{ stroke: "#d1d5db" }}
          label={xAxisLabel ? { value: xAxisLabel, position: "insideBottom", offset: -5 } : undefined}
        />
        <YAxis
          tick={{ fontSize: 12 }}
          tickLine={false}
          axisLine={{ stroke: "#d1d5db" }}
          tickFormatter={formatAxisTick}
          label={yAxisLabel ? { value: yAxisLabel, angle: -90, position: "insideLeft" } : undefined}
        />
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
          <Legend
            wrapperStyle={{ paddingTop: 10, fontSize: 12 }}
            iconType="line"
          />
        )}
        {series.map((s, index) => (
          <Line
            key={s.dataKey}
            type={curved ? "monotone" : "linear"}
            dataKey={s.dataKey}
            name={s.name}
            stroke={s.color || getChartColor(index)}
            strokeWidth={2}
            dot={showDots ? { r: 3, strokeWidth: 2 } : false}
            activeDot={{ r: 6, strokeWidth: 2 }}
            connectNulls
          />
        ))}
      </RechartsLineChart>
    </ResponsiveContainer>
  );
};

export default LineChartComponent;
