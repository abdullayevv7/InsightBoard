/**
 * Metric Card component for displaying KPI values with trends.
 */

import React from "react";
import clsx from "clsx";
import { formatCompact, formatPercentage } from "../../utils/formatters";

interface MetricCardProps {
  title: string;
  value: number | string;
  previousValue?: number;
  format?: "number" | "currency" | "percentage" | "compact" | "raw";
  prefix?: string;
  suffix?: string;
  trend?: "up" | "down" | "neutral";
  trendValue?: number;
  icon?: React.ReactNode;
  color?: "blue" | "green" | "red" | "yellow" | "purple" | "indigo";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
}

const colorClasses: Record<string, { bg: string; text: string; icon: string }> = {
  blue: { bg: "bg-blue-50", text: "text-blue-600", icon: "text-blue-400" },
  green: { bg: "bg-green-50", text: "text-green-600", icon: "text-green-400" },
  red: { bg: "bg-red-50", text: "text-red-600", icon: "text-red-400" },
  yellow: { bg: "bg-yellow-50", text: "text-yellow-600", icon: "text-yellow-400" },
  purple: { bg: "bg-purple-50", text: "text-purple-600", icon: "text-purple-400" },
  indigo: { bg: "bg-indigo-50", text: "text-indigo-600", icon: "text-indigo-400" },
};

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  previousValue,
  format = "raw",
  prefix = "",
  suffix = "",
  trend,
  trendValue,
  icon,
  color = "blue",
  size = "md",
  loading = false,
}) => {
  const colors = colorClasses[color] || colorClasses.blue;

  const formattedValue = React.useMemo(() => {
    if (typeof value === "string") return value;

    switch (format) {
      case "compact":
        return formatCompact(value);
      case "percentage":
        return formatPercentage(value);
      case "currency":
        return `$${formatCompact(value)}`;
      case "number":
        return value.toLocaleString();
      default:
        return String(value);
    }
  }, [value, format]);

  const computedTrend = React.useMemo(() => {
    if (trend) return trend;
    if (previousValue !== undefined && typeof value === "number") {
      if (value > previousValue) return "up" as const;
      if (value < previousValue) return "down" as const;
      return "neutral" as const;
    }
    return undefined;
  }, [trend, previousValue, value]);

  const computedTrendValue = React.useMemo(() => {
    if (trendValue !== undefined) return trendValue;
    if (previousValue !== undefined && typeof value === "number" && previousValue !== 0) {
      return ((value - previousValue) / Math.abs(previousValue)) * 100;
    }
    return undefined;
  }, [trendValue, previousValue, value]);

  const sizeClasses = {
    sm: { card: "p-3", title: "text-xs", value: "text-xl" },
    md: { card: "p-4", title: "text-sm", value: "text-2xl" },
    lg: { card: "p-6", title: "text-base", value: "text-3xl" },
  };
  const sizes = sizeClasses[size];

  if (loading) {
    return (
      <div className={clsx("rounded-lg border border-gray-200 bg-white", sizes.card)}>
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-gray-200 rounded w-1/2" />
          <div className="h-8 bg-gray-200 rounded w-3/4" />
          <div className="h-3 bg-gray-200 rounded w-1/3" />
        </div>
      </div>
    );
  }

  return (
    <div className={clsx("rounded-lg border border-gray-200 bg-white", sizes.card)}>
      <div className="flex items-center justify-between mb-2">
        <h3 className={clsx("font-medium text-gray-500", sizes.title)}>{title}</h3>
        {icon && (
          <div className={clsx("p-2 rounded-lg", colors.bg, colors.icon)}>
            {icon}
          </div>
        )}
      </div>

      <div className={clsx("font-bold", colors.text, sizes.value)}>
        {prefix}{formattedValue}{suffix}
      </div>

      {computedTrend && computedTrendValue !== undefined && (
        <div className="flex items-center mt-2 space-x-1">
          <span
            className={clsx("text-sm font-medium", {
              "text-green-600": computedTrend === "up",
              "text-red-600": computedTrend === "down",
              "text-gray-500": computedTrend === "neutral",
            })}
          >
            {computedTrend === "up" && "^"}
            {computedTrend === "down" && "v"}
            {formatPercentage(Math.abs(computedTrendValue), { decimals: 1 })}
          </span>
          <span className="text-xs text-gray-400">vs previous period</span>
        </div>
      )}
    </div>
  );
};

export default MetricCard;
