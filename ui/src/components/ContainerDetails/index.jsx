import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { setSelectedContainer } from "@/store/slices/containerSlice";
import "./ContainerDetails.scss";
import { useState } from "react";
import { compareStatusWithConfig } from "@/components/utils/index";

export default function ContainerDetailsModal() {
  const dispatch = useAppDispatch();
  const [closing, setClosing] = useState(false);
  const [expandedSection, setExpandedSection] = useState(null);

  const selectedContainerId = useAppSelector((state) => state.container);
  const containers = useAppSelector((state) => state.containers);
  const selectedContainerDetails = containers.find(
    (c) => c.id === selectedContainerId
  );

  function onClose() {
    setClosing(true);
    setTimeout(() => {
      dispatch(setSelectedContainer(null));
    }, 150);
  }

  function toggleSection(section) {
    setExpandedSection(expandedSection === section ? null : section);
  }

  function formatTimestamp(timestamp) {
    const date = new Date(timestamp * 1000);
    return date.toLocaleTimeString();
  }

  function getStatusColor(status) {
    const statusMap = {
      running: "success",
      stopped: "neutral",
      exited: "warning",
      removed: "critical",
      booting: "info",
    };
    return statusMap[status] || "neutral";
  }

  return (
    <div className={`modal-container ${closing ? "closing" : ""}`}>
      {/* Header */}
      <div className="modal-header">
        <div className="modal-title-group">
          <h2>{selectedContainerDetails.name}</h2>
          <span
            className={`status-badge status-${getStatusColor(
              selectedContainerDetails.status
            )}`}
          >
            {selectedContainerDetails.status}
          </span>
        </div>
        <button className="close-btn" onClick={onClose}>
          ✕
        </button>
      </div>

      {/* Metrics Grid */}
      <div className="metrics-grid">
        <div className="metric-card">
          <span className="metric-label">CPU</span>
          <span
            className={`metric-value ${compareStatusWithConfig(
              selectedContainerId,
              "cpu"
            )}`}
          >
            {selectedContainerDetails.cpu}%
          </span>
        </div>
        <div className="metric-card">
          <span className="metric-label">Memory</span>
          <span
            className={`metric-value ${compareStatusWithConfig(
              selectedContainerId,
              "mem"
            )}`}
          >
            {selectedContainerDetails.mem}%
          </span>
        </div>
        <div className="metric-card">
          <span className="metric-label">Requests/Min</span>
          <span
            className={`metric-value ${compareStatusWithConfig(
              selectedContainerId,
              "rpm"
            )}`}
          >
            {selectedContainerDetails.rpm}
          </span>
        </div>
        {/* <div className="metric-card metric-card-wide">
          <span className="metric-label">Container ID</span>
          <span className="metric-value metric-value-sm">
            {selectedContainerDetails.id}
          </span>
        </div> */}
      </div>

      {/* Accordion Sections */}
      <div className="accordion">
        {/* History Section */}
        <div className="accordion-item">
          <button
            className={`accordion-header ${
              expandedSection === "history" ? "active" : ""
            }`}
            onClick={() => toggleSection("history")}
          >
            <span>History</span>
            <span className="accordion-icon">
              {expandedSection === "history" ? "−" : "+"}
            </span>
          </button>
          <div
            className={`accordion-content ${
              expandedSection === "history" ? "expanded" : ""
            }`}
          >
            <div className="history-timeline">
              {selectedContainerDetails.history
                ?.slice(0, 10)
                .map((entry, idx) => (
                  <div key={idx} className="history-entry">
                    <div className="history-time">
                      {formatTimestamp(entry.timestamp)}
                    </div>
                    <div className="history-metrics">
                      <span className="history-metric">CPU: {entry.cpu}%</span>
                      <span className="history-metric">
                        Mem: {entry.memory}%
                      </span>
                      <span className="history-metric">
                        RPM: {entry.rpm}
                      </span>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        </div>

        {/* Logs Section */}
        <div className="accordion-item">
          <button
            className={`accordion-header ${
              expandedSection === "logs" ? "active" : ""
            }`}
            onClick={() => toggleSection("logs")}
          >
            <span>Logs</span>
            <span className="accordion-icon">
              {expandedSection === "logs" ? "−" : "+"}
            </span>
          </button>
          <div
            className={`accordion-content ${
              expandedSection === "logs" ? "expanded" : ""
            }`}
          >
            <pre className="logs-content">
              {selectedContainerDetails.logs || "No logs available"}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}
