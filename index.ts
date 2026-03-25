/**
 * Dashboard Grid component using react-grid-layout for drag-and-drop widget arrangement.
 */

import React, { useCallback, useMemo } from "react";
import GridLayout, { Layout } from "react-grid-layout";
import { Widget } from "../../api/dashboards";
import WidgetRenderer from "./WidgetRenderer";
import "react-grid-layout/css/styles.css";

interface DashboardGridProps {
  widgets: Widget[];
  isEditing: boolean;
  onLayoutChange?: (layouts: Layout[]) => void;
  onWidgetEdit?: (widget: Widget) => void;
  onWidgetDelete?: (widgetId: string) => void;
  onWidgetRefresh?: (widgetId: string) => void;
  cols?: number;
  rowHeight?: number;
  containerWidth?: number;
}

const DashboardGrid: React.FC<DashboardGridProps> = ({
  widgets,
  isEditing,
  onLayoutChange,
  onWidgetEdit,
  onWidgetDelete,
  onWidgetRefresh,
  cols = 12,
  rowHeight = 80,
  containerWidth = 1200,
}) => {
  const layout: Layout[] = useMemo(
    () =>
      widgets.map((widget) => ({
        i: widget.id,
        x: widget.position_x,
        y: widget.position_y,
        w: widget.width,
        h: widget.height,
        minW: 2,
        minH: 2,
        static: !isEditing,
      })),
    [widgets, isEditing]
  );

  const handleLayoutChange = useCallback(
    (newLayout: Layout[]) => {
      if (onLayoutChange && isEditing) {
        onLayoutChange(newLayout);
      }
    },
    [onLayoutChange, isEditing]
  );

  if (widgets.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-gray-400">
        <div className="text-6xl mb-4">[+]</div>
        <h3 className="text-lg font-medium text-gray-500 mb-2">No widgets yet</h3>
        <p className="text-sm">
          {isEditing
            ? "Click 'Add Widget' to start building your dashboard."
            : "This dashboard has no widgets."}
        </p>
      </div>
    );
  }

  return (
    <GridLayout
      className="dashboard-grid"
      layout={layout}
      cols={cols}
      rowHeight={rowHeight}
      width={containerWidth}
      onLayoutChange={handleLayoutChange}
      isDraggable={isEditing}
      isResizable={isEditing}
      compactType="vertical"
      margin={[16, 16]}
      containerPadding={[0, 0]}
      useCSSTransforms
    >
      {widgets.map((widget) => (
        <div
          key={widget.id}
          className={`bg-white rounded-lg border shadow-sm overflow-hidden ${
            isEditing ? "border-blue-200 ring-1 ring-blue-100" : "border-gray-200"
          }`}
        >
          {/* Widget Header */}
          <div className="flex items-center justify-between px-4 py-2 border-b border-gray-100 bg-gray-50">
            <h3 className="text-sm font-medium text-gray-700 truncate">
              {widget.title}
            </h3>
            <div className="flex items-center space-x-1">
              {onWidgetRefresh && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onWidgetRefresh(widget.id);
                  }}
                  className="p-1 text-gray-400 hover:text-gray-600 rounded"
                  title="Refresh data"
                >
                  [R]
                </button>
              )}
              {isEditing && onWidgetEdit && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onWidgetEdit(widget);
                  }}
                  className="p-1 text-gray-400 hover:text-blue-600 rounded"
                  title="Edit widget"
                >
                  [E]
                </button>
              )}
              {isEditing && onWidgetDelete && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onWidgetDelete(widget.id);
                  }}
                  className="p-1 text-gray-400 hover:text-red-600 rounded"
                  title="Delete widget"
                >
                  [X]
                </button>
              )}
            </div>
          </div>

          {/* Widget Content */}
          <div className="p-2 h-[calc(100%-40px)]">
            <WidgetRenderer widget={widget} isEditing={isEditing} />
          </div>
        </div>
      ))}
    </GridLayout>
  );
};

export default DashboardGrid;
