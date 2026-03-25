/**
 * Bar Chart component using Recharts.
 * Supports grouped, stacked, and horizontal layouts.
 */

import React from "react";
import {
  BarChart as RechartsBarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { ChartDataPoint, SeriesConfig, getChartColor, formatAxisTick } from "../../utils/chartHelpers";

interface BarChartProps {
  data: ChartDataPoint[];
  xKey: string;
  series: SeriesConfig[];
  height?: number;
  stacked?: boolean;
  horizontal?: boolean;
  showGrid?: boolean;
  showLegend?: boolean;
  barRadius?: number;
  barGap?: number;
  tooltipFormatter?: (value: number) => string;
}

const BarChartComponent: React.FC<BarChartProps> = ({
  data,
  xKey,
  series,
  height = 300,
  stacked = false,
  horizontal = false,
  showGrid = true,
  showLegend = true,
  barRadius = 4,
  barGap = 4,
  tooltipFormatter,
}) => {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        No data available
      </div>
    );
  }

  const Layout = horizontal ? "vertical" : "horizontal";

  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsBarChart
        data={data}
        layout={Layout === "vertical" ? "vertical" : "horizontal"}
        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        barGap={barGap}
      >
        {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />}
        {horizontal ? (
          <>
            <XAxis type="number" tickFormatter={formatAxisTick} tick={{ fontSize: 12 }} />
            <YAxis
              type="category"
              dataKey={xKey}
              tick={{ fontSize: 12 }}
              width={100}
            />
          </>
        ) : (
          <>
            <XAxis dataKey={xKey} tick={{ fontSize: 12 }} tickLine={false} />
            <YAxis tickFormatter={formatAxisTick} tick={{ fontSize: 12 }} tickLine={false} />
          </>
        )}
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
        {series.map((s, index) => (
          <Bar
            key={s.dataKey}
            dataKey={s.dataKey}
            name={s.name}
            fill={s.color || getChartColor(index)}
            stackId={stacked ? "stack" : undefined}
            radius={[barRadius, barRadius, 0, 0]}
            maxBarSize={50}
          />
        ))}
      </RechartsBarChart>
    </ResponsiveContainer>
  );
};

export default BarChartComponent;
