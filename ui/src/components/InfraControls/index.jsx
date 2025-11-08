import { useControls } from "react-zoom-pan-pinch";
import ZoomInIcon from "./ZoomIn.svg?react";
import ZoomOutIcon from "./ZoomOut.svg?react";
import ResetIcon from "./Reset.svg?react";
import "./InfraControls.scss";

export default function InfraControls({ onReset }) {
  const { zoomIn, zoomOut, resetTransform } = useControls();

  const handleReset = () => {
    resetTransform();
    onReset();
  };

  return (
    <div className="infra-controls">
      <button
        className="infra-controls__btn"
        onClick={() => zoomIn()}
        title="Zoom In"
      >
        <ZoomInIcon className="infra-controls__icon" />
      </button>

      <button
        className="infra-controls__btn"
        onClick={() => zoomOut()}
        title="Zoom Out"
      >
        <ZoomOutIcon className="infra-controls__icon" />
      </button>

      <button
        className="infra-controls__btn"
        onClick={handleReset}
        title="Reset Canvas"
      >
        <ResetIcon className="infra-controls__icon" />
      </button>
    </div>
  );
}
