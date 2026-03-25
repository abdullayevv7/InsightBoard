/**
 * Widget Renderer: maps widget_type to the appropriate chart component.
 * This is the core component that renders a widget's content based on its type.
 */

import React, { useState, useEffect } from "react";
import { Widget } from "../../api/dashboards";
import { datasourcesApi, QueryResult } from "../../api/datasources";
import { transformToChartData, generateSeriesConfig, calculatePieData } from "../../utils/chartHelpers";
import LineChartComponent from "../charts/LineChart";
import BarChartComponent from "../charts/BarChart";
import PieChartComponent from "../charts/PieChart";
import AreaChartComponent from "../charts/AreaChart";
import MetricCard from "../charts/MetricCard";

interface WidgetRendererProps {
  widget: Widget;
  isEditing?: boolean;
}

const WidgetRenderer: React.FC<WidgetRendererProps> = ({ widget, isEditing = false }) => {
  const [data, setData] = useState<QueryResult | null>(widget.cached_data as QueryResult | null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!widget.data_source || data) return;

    const fetchData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const queryConfig = widget.query_config || {};
        const query = (queryConfig as Record<string, string>).query || "";
        const response = await datasourcesApi.executeQuery(widget.data_source!, query);
        setData(response.data);
      } catch (err) {
        setError("Failed to load widget data");
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [widget.data_source, widget.query_config, data]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full text-red-500 text-sm p-4">
        {error}
      </div>
    );
  }

  if (widget.widget_type === "text") {
    const vizConfig = widget.visualization_config as Record<string, string>;
    return (
      <div className="p-4 prose prose-sm max-w-none">
        <div dangerouslySetInnerHTML={{ __html: vizConfig?.content || "No content" }} />
      </div>
    );
  }

  if (widget.widget_type === "metric_card") {
    const vizConfig = widget.visualization_config as Record<string, unknown>;
    const metricValue = data?.rows?.[0]
      ? (data.rows[0][vizConfig?.valueField as string || "value"] as number) || 0
      : (vizConfig?.staticValue as number) || 0;

    return (
      <MetricCard
        title={widget.title}
        value={metricValue}
        format={(vizConfig?.format as "compact" | "number" | "currency" | "percentage") || "compact"}
        color={(vizConfig?.color as "blue" | "green" | "red") || "blue"}
        previousValue={vizConfig?.previousValue as number | undefined}
        size="lg"
      />
    );
  }

  if (!data || !data.rows || data.rows.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-400 text-sm">
        <span>No data to display</span>
        {isEditing && <span className="text-xs mt-1">Configure a data source and query</span>}
      </div>
    );
  }

  const vizConfig = widget.visualization_config || {};
  const xKey = (vizConfig as Record<string, string>).xAxis || data.columns[0] || "name";
  const yKeys = ((vizConfig as Record<string, string[]>).yAxes) || data.columns.filter((c) => c !== xKey);
  const chartData = transformToChartData(data.rows, xKey, yKeys);
  const series = generateSeriesConfig(
    [xKey, ...yKeys],
    xKey,
    (vizConfig as Record<string, string[]>).colors
  );

  switch (widget.widget_type) {
    case "line_chart":
      return <LineChartComponent data={chartData} xKey={xKey} series={series} />;

    case "bar_chart":
      return <BarChartComponent data={chartData} xKey={xKey} series={series} />;

    case "area_chart":
      return <AreaChartComponent data={chartData} xKey={xKey} series={series} />;

    case "pie_chart":
      return (
        <PieChartComponent
          data={calculatePieData(data.rows, xKey, yKeys[0] || "value")}
        />
      );

    case "data_table":
      return (
        <div className="overflow-auto h-full">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-gray-50">
              <tr>
                {data.columns.map((col) => (
                  <th key={col} className="px-3 py-2 text-left font-medium text-gray-600 border-b">
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.rows.slice(0, 100).map((row, rowIdx) => (
                <tr key={rowIdx} className="hover:bg-gray-50">
                  {data.columns.map((col) => (
                    <td key={col} className="px-3 py-2 border-b border-gray-100">
                      {String(row[col] ?? "")}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );

    default:
      return (
        <div className="flex items-center justify-center h-full text-gray-400 text-sm">
          Unsupported widget type: {widget.widget_type}
        </div>
      );
  }
};

export default WidgetRenderer;
