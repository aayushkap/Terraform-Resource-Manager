import { useState, useRef, useEffect } from "react";
import "./Box.scss";
import Container from "./container.svg?react";
import StatusDisplay from "@/components/StatusDisplay";
import { useAppSelector, useAppDispatch } from "@/store/hooks";
import { setContainer } from "@/store/slices/containersSlice";
import { setSelectedContainer } from "@/store/slices/containerSlice";

export default function DraggableBox({ id, onDoubleClick }) {
  const dispatch = useAppDispatch();
  const config = useAppSelector((state) => state.config);
  const container = useAppSelector((s) =>
    s.containers.find((c) => c.id === id)
  );
  const selectedContainer = useAppSelector((state) => state.container);

  if (!container) return null;

  const dragRef = useRef(null);

  const startDrag = (e) => {
    e.stopPropagation();
    dragRef.current = {
      offsetX: e.clientX - container.x,
      offsetY: e.clientY - container.y,
    };
  };

  const handleMove = (e) => {
    if (!dragRef.current) return;
    const { offsetX, offsetY } = dragRef.current;
    const nx = e.clientX - offsetX;
    const ny = e.clientY - offsetY;
    dispatch(setContainer({ id, x: nx, y: ny }));
  };

  const handleUp = () => {
    dragRef.current = null;
  };

  useEffect(() => {
    window.addEventListener("mousemove", handleMove);
    window.addEventListener("mouseup", handleUp);
    return () => {
      window.removeEventListener("mousemove", handleMove);
      window.removeEventListener("mouseup", handleUp);
    };
  }, []);

  function compareStatusWithConfig(type) {
    if (!config) return "na";
    if (container[type] === 0) {
      return "na";
    }

    const configType = config[type];

    if (container[type] > configType.max) {
      return "alert";
    }
    if (container[type] < configType.min) {
      return "ok";
    }
    return "warn";
  }

  const [clickCount, setClickCount] = useState(0);
  const clickTimer = useRef(null);

  const handleMouseDown = (e) => {
    e.stopPropagation();

    setClickCount((prev) => prev + 1);

    if (clickTimer.current) clearTimeout(clickTimer.current);

    clickTimer.current = setTimeout(() => {
      if (clickCount === 1) {
        // Single click - start drag
        startDrag(e);
      }
      setClickCount(0);
    }, 200);
  };

  const handleDoubleClick = (e) => {
    e.stopPropagation();
    if (clickTimer.current) clearTimeout(clickTimer.current);
    setClickCount(0);
    dragRef.current = null; // Cancel any drag
    onDoubleClick?.();
  };

  const handleSingleClick = (e) => {
    e.stopPropagation();

    if (selectedContainer) {
      if (selectedContainer === id) {
        dispatch(setSelectedContainer(null));
      } else {
        dispatch(setSelectedContainer(id));
      }
      return;
    }
  };

  return (
    <div
      className={`box-container ${
        selectedContainer == container.id && "selected"
      } ${container.status.toLowerCase() == "removed" && "removed"}`}
      onMouseDown={startDrag}
      onClick={handleSingleClick}
      onDoubleClick={handleDoubleClick}
      style={{ left: container.x, top: container.y }}
    >
      <div
        className={`box-title ${
          container.status.toLowerCase() == "removed" && "removed"
        }`}
      >
        <Container
          className={`box-svg ${
            container.status.toLowerCase() == "removed" && "removed"
          }`}
        />
        {container.label}
      </div>

      <div className="box-statuses">
        <StatusDisplay
          label={`${container.cpu}% CPU` || "na"}
          size="sm"
          status={compareStatusWithConfig("cpu")}
        />
        <StatusDisplay
          label={`${container.mem}% Mem` || "na"}
          size="sm"
          status={compareStatusWithConfig("mem")}
        />
        <StatusDisplay
          label={`${container.rpm} RPM` || "na"}
          size="sm"
          status={compareStatusWithConfig("rpm")}
        />
      </div>
    </div>
  );
}
