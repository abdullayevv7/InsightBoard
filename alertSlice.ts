/**
 * Pie/Donut Chart component using Recharts.
 * Supports custom labels, tooltips, and inner radius for donut style.
 */

import React, { useCallback } from "react";
import {
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { getChartColor } from "../../utils/chartHelpers";

interface PieDataItem {
  name: string;
  value: number;
  percentage?: number;
}

interface PieChartProps {
  data: PieDataItem[];
  height?: number;
  donut?: boolean;
  showLegend?: boolean;
  showLabels?: boolean;
  colors?: string[];
  innerRadius?: number;
  outerRadius?: number;
  tooltipFormatter?: (value: number) => string;
}

interface CustomLabelProps {
  cx: number;
  cy: number;
  midAngle: number;
  innerRadius: number;
  outerRadius: number;
  percent: number;
  name: string;
}

const RADIAN = Math.PI / 180;

const renderCustomLabel = ({
  cx,
  cy,
  midAngle,
  innerRadius,
  outerRadius,
  percent,
  name,
}: CustomLabelProps) => {
  if (percent < 0.05) return null;

  const radius = innerRadius + (outerRadius - innerRadius) * 1.3;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);

  return (
    <text
      x={x}
      y={y}
      fill="#374151"
      textAnchor={x > cx ? "start" : "end"}
      dominantBaseline="central"
      fontSize={11}
    >
      {name} ({(percent * 100).toFixed(1)}%)
    </text>
  );
};

const PieChartComponent: React.FC<PieChartProps> = ({
  data,
  height = 300,
  donut = false,
  showLegend = true,
  showLabels = true,
  colors,
  innerRadius: customInnerRadius,
  outerRadius: customOuterRadius,
  tooltipFormatter,
}) => {
  const innerRadius = customInnerRadius ?? (donut ? 60 : 0);
  const outerRadius = customOuterRadius ?? 100;

  const labelRenderer = useCallback(
    (props: CustomLabelProps) => (showLabels ? renderCustomLabel(props) : null),
    [showLabels]
  );

  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        No data available
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsPieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={innerRadius}
          outerRadius={outerRadius}
          dataKey="value"
          nameKey="name"
          label={labelRenderer}
          labelLine={showLabels}
          animationBegin={0}
          animationDuration={800}
        >
          {data.map((_, index) => (
            <Cell
              key={`cell-${index}`}
              fill={getChartColor(index, colors)}
              strokeWidth={2}
              stroke="#fff"
            />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            backgroundColor: "#fff",
            border: "1px solid #e5e7eb",
            borderRadius: "8px",
            boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
          }}
          formatter={tooltipFormatter
            ? (value: number) => [tooltipFormatter(value)]
            : (value: number) => [value.toLocaleString()]
          }
        />
        {showLegend && (
          <Legend
            layout="vertical"
            align="right"
            verticalAlign="middle"
            iconType="circle"
            wrapperStyle={{ fontSize: 12 }}
          />
        )}
      </RechartsPieChart>
    </ResponsiveContainer>
  );
};

export default PieChartComponent;
