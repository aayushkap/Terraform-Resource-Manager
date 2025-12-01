import React, { useState, useMemo } from "react";
import {
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import Dropdown from "../components/UI/Dropdown";
import ContainerMetricsChart from "../components/ContainerMetrics/ContainerMetricsChart";
// import "./ContainerMetricsChart.scss";

export default function Observability() {
  return <ContainerMetricsChart />;
}
