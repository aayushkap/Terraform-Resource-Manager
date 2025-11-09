import Observability from "./Observability.svg?react";
import InfraManagerIcon from "./InfraManager.svg?react";
import ConfigurationIcon from "./Configuration.svg?react";
import "./TabSwitcher.scss";
import { useAppSelector, useAppDispatch } from "@/store/hooks";
import { setTab } from "@/store/slices/tabSlice";

export default function TabSwitcher() {
  const dispatch = useAppDispatch();
  function switchTab(tab) {
    dispatch(setTab(tab));
  }
  const tab = useAppSelector((s) => s.tab);

  return (
    <div className="tab-switcher">
      <button
        className={`tab-switcher-btn ${
          tab === "observability" ? "active" : ""
        }`}
        onClick={() => switchTab("observability")}
        title="Observability"
      >
        <Observability className="tab-switcher-icon" />
      </button>

      <button
        className={`tab-switcher-btn ${
          tab === "infrastructure_management" ? "active" : ""
        }`}
        onClick={() => switchTab("infrastructure_management")}
        title="Infrastructure Management"
      >
        <InfraManagerIcon className="tab-switcher-icon" />
      </button>

      <button
        className={`tab-switcher-btn ${
          tab === "configuration" ? "active" : ""
        }`}
        onClick={() => switchTab("configuration")}
        title="Configuration"
      >
        <ConfigurationIcon className="tab-switcher-icon" />
      </button>
    </div>
  );
}
