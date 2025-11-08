import { useControls } from "react-zoom-pan-pinch";
import Observability from "./Observability.svg?react";
import InfraManagerIcon from "./InfraManager.svg?react";
import ConfigurationIcon from "./Configuration.svg?react";
import "./TabSwitcher.scss";

export default function TabSwitcher() {
  function switchTab(tab) {
    console.log(tab);
  }
  return (
    <div className="tab-switcher">
      <button
        className="tab-switcher-btn"
        onClick={() => switchTab()}
        title="Observability"
      >
        <Observability className="tab-switcher-icon" />
      </button>

      <button
        className="tab-switcher-btn"
        onClick={() => switchTab()}
        title="Infrastructure Management"
      >
        <InfraManagerIcon className="tab-switcher-icon" />
      </button>

      <button
        className="tab-switcher-btn"
        onClick={() => switchTab()}
        title="Configuration"
      >
        <ConfigurationIcon className="tab-switcher-icon" />
      </button>
    </div>
  );
}
