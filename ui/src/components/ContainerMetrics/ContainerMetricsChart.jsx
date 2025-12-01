import React, { useState, useMemo } from "react";
import {
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import Dropdown from "../UI/Dropdown";
import "./ContainerMetricsChart.scss";
import { useGetMetricsQuery } from "@/api/containerMetrics";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { compareStatusWithConfig } from "../utils";

export default function ContainerMetricsChart() {
  const data = useAppSelector((state) => state.containerMetrics)[0];

  useGetMetricsQuery(undefined, {
    pollingInterval: 5000,
  });

  const [metricFilter, setMetricFilter] = useState({
    value: "all",
    label: "All",
  });
  const [aggregationFilter, setAggregationFilter] = useState({
    value: "avg",
    label: "Average",
  });

  const metricOptions = [
    { value: "all", label: "All" },
    { value: "cpu", label: "CPU" },
    { value: "memory", label: "Memory" },
    { value: "rpm", label: "RPM" },
  ];

  const aggregationOptions = [
    { value: "avg", label: "Average" },
    { value: "min", label: "Minimum" },
    { value: "max", label: "Maximum" },
  ];

  const chartData = useMemo(() => {
    // group data by minute, showing latest for that minute, for each row
    if (!data?.history) return [];

    const groupedByMinute = data.history.reduce((acc, item) => {
      const date = new Date(item.timestamp * 1000);

      const minuteKey = date.toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
      });

      if (!acc[minuteKey]) {
        acc[minuteKey] = {
          time: minuteKey,
          timestamp: item.timestamp,
          items: [],
        };
      }

      acc[minuteKey].items.push(item);
      return acc;
    }, {});

    return Object.values(groupedByMinute)
      .sort((a, b) => a.timestamp - b.timestamp)
      .map((minuteGroup) => {
        const items = minuteGroup.items;

        const latestItem = items.sort((a, b) => b.timestamp - a.timestamp)[0];

        return {
          time: minuteGroup.time,
          timestamp: latestItem.timestamp,

          running: latestItem.running_containers,
          stopped: latestItem.stopped_containers,
          booting: latestItem.booting_containers,
          removed: latestItem.removed_containers,

          cpu: latestItem[`${aggregationFilter.value}_cpu`] || 0,
          memory: latestItem[`${aggregationFilter.value}_memory`] || 0,
          rpm: latestItem[`${aggregationFilter.value}_rpm`] || 0,
        };
      });
  }, [data, aggregationFilter]);

  const showMetric = (metric) => {
    return metricFilter.value === "all" || metricFilter.value === metric;
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;

    const metrics = [];
    const containers = [];

    payload.forEach((item) => {
      if (["RPM", "CPU %", "Memory GB"].includes(item.name)) {
        metrics.push(item);
      } else {
        containers.push(item);
      }
    });

    return (
      <div className="chart-tooltip">
        <p className="tooltip-label">{label}</p>

        {containers.length > 0 && (
          <div className="tooltip-section">
            <p className="tooltip-section-title">Containers:</p>
            <div className="tooltip-content">
              {containers.map((entry, index) => (
                <div key={index} className="tooltip-item">
                  <span
                    className="tooltip-indicator"
                    style={{ backgroundColor: entry.color }}
                  />
                  <span className="tooltip-name">{entry.name}:</span>
                  <span className="tooltip-value">{entry.value}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {metrics.length > 0 && (
          <div className="tooltip-section">
            <p className="tooltip-section-title">Metrics:</p>
            <div className="tooltip-content">
              {metrics.map((entry, index) => (
                <div key={index} className="tooltip-item">
                  <span
                    className="tooltip-indicator"
                    style={{ backgroundColor: entry.color }}
                  />
                  <span className="tooltip-name">{entry.name}:</span>
                  <span className="tooltip-value">
                    {typeof entry.value === "number"
                      ? entry.value.toFixed(2)
                      : entry.value}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  const CustomLegend = (props) => {
    const { payload } = props;

    const desiredOrder = [
      "Running",
      // "Booting",
      "Stopped",
      "Removed",
      "CPU %",
      "Memory GB",
      "RPM",
    ];

    const sortedPayload = [...payload].sort((a, b) => {
      const indexA = desiredOrder.indexOf(a.value);
      const indexB = desiredOrder.indexOf(b.value);
      return indexA - indexB;
    });

    return (
      <ul
        style={{
          listStyle: "none",
          padding: 0,
          margin: 0,
          display: "flex",
          flexWrap: "wrap",
          gap: "16px",
          justifyContent: "center",
          fontFamily: "var(--font-primary)",
          fontSize: "var(--size-body-sm)",
        }}
      >
        {sortedPayload.map((entry, index) => (
          <li
            key={`item-${index}`}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            <span
              style={{
                display: "inline-block",
                width: "12px",
                height: "12px",
                backgroundColor: entry.color,
                borderRadius: "2px",
              }}
            />
            <span style={{ color: "var(--color-text-primary)" }}>
              {entry.value}
            </span>
          </li>
        ))}
      </ul>
    );
  };

  return (
    <div className="metrics-chart-container">
      <div className="chart-header">
        <h2 className="chart-title"></h2>
        <div className="chart-filters">
          <Dropdown
            options={metricOptions}
            value={metricFilter}
            onChange={setMetricFilter}
            placeholder="Metric"
            className="filter-dropdown"
          />
          <Dropdown
            options={aggregationOptions}
            value={aggregationFilter}
            onChange={setAggregationFilter}
            placeholder="Aggregation"
            className="filter-dropdown"
          />
        </div>
      </div>

      <div className="chart-wrapper">
        <ResponsiveContainer width="100%" height={"100%"}>
          <ComposedChart
            data={chartData}
            margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="var(--color-border)"
              strokeOpacity={0.5}
            />

            <XAxis
              dataKey="time"
              stroke="var(--color-text-secondary)"
              style={{
                fontSize: "var(--size-body-sm)",
                fontFamily: "var(--font-primary)",
              }}
              tick={{ fill: "var(--color-text-secondary)" }}
            />
            <YAxis
              yAxisId="left"
              orientation="left"
              stroke="var(--color-text-secondary)"
              style={{
                fontSize: "var(--size-body-sm)",
                fontFamily: "var(--font-primary)",
              }}
              tick={{ fill: "var(--color-text-secondary)" }}
              label={{
                value: "Num Containers",
                angle: -90,
                position: "insideLeft",
              }}
            />

            <YAxis
              yAxisId="right"
              orientation="right"
              stroke="var(--color-text-secondary)"
              style={{
                fontSize: "var(--size-body-sm)",
                fontFamily: "var(--font-primary)",
              }}
              tick={{ fill: "var(--color-text-secondary)" }}
              label={{
                value: "Metrics",
                angle: 90,
                position: "insideRight",
              }}
            />

            <Tooltip content={<CustomTooltip />} />

            <Legend content={CustomLegend} />

            <Bar
              yAxisId="left"
              dataKey="running"
              stackId="containers"
              fill="var(--color-status-success)"
              name="Running"
            />
            {/* <Bar
              yAxisId="left"
              dataKey="booting"
              stackId="containers"
              fill="var(--color-status-neutral)"
              name="Booting"
            /> */}
            <Bar
              yAxisId="left"
              dataKey="stopped"
              stackId="containers"
              fill="var(--color-status-critical)"
              name="Stopped"
            />
            <Bar
              yAxisId="left"
              dataKey="removed"
              stackId="containers"
              fill="var(--color-status-warning)"
              name="Removed"
            />

            {showMetric("cpu") && (
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="cpu"
                stroke="var(--color-accent)"
                strokeWidth={2.5}
                dot={{ fill: "var(--color-accent)", r: 4 }}
                activeDot={{ r: 6 }}
                name="CPU %"
              />
            )}

            {showMetric("memory") && (
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="memory"
                stroke="var(--color-status-info)"
                strokeWidth={2.5}
                dot={{ fill: "var(--color-status-info)", r: 4 }}
                activeDot={{ r: 6 }}
                name="Memory GB"
              />
            )}

            {showMetric("rpm") && (
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="rpm"
                stroke="var(--color-accent-dark)"
                strokeWidth={2.5}
                dot={{ fill: "var(--color-accent-dark)", r: 4 }}
                activeDot={{ r: 6 }}
                name="RPM"
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
