import { useState, useRef, useEffect } from "react";
import "./Box.scss";
import Container from "./container.svg?react";
import StatusDisplay from "@/components/StatusDisplay";
import { useAppSelector, useAppDispatch } from "@/store/hooks";
import { setContainer } from "@/store/slices/containersSlice";

export default function ContainerBoxes() {
  const containers = useAppSelector((s) => s.containers);
  return containers.map((c) => <DraggableBox key={c.id} id={c.id} />);
}

function DraggableBox({ id }) {
  const dispatch = useAppDispatch();
  const config = useAppSelector((state) => state.config);
  const container = useAppSelector((s) =>
    s.containers.find((c) => c.id === id)
  );
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

    const configType = config[type];
    if (container[type] > configType["max"]) {
      return "alert";
    }
    if (container[type] < configType["min"]) {
      return "ok";
    }
    return "warn";
  }

  return (
    <div
      className="box-container"
      onMouseDown={startDrag}
      style={{ left: container.x, top: container.y }}
    >
      <div className="box-title">
        <Container className="box-svg" />
        {container.label}
      </div>

      <div className="box-statuses">
        <StatusDisplay
          label={`${container.cpu}% CPU` || "N/A"}
          size="sm"
          status={compareStatusWithConfig("cpu")}
        />
        <StatusDisplay
          label={`${container.mem}% Mem` || "N/A"}
          size="sm"
          status={compareStatusWithConfig("mem")}
        />
        <StatusDisplay
          label={`${container.rpm} RPM` || "N/A"}
          size="sm"
          status={compareStatusWithConfig("rpm")}
        />
      </div>
    </div>
  );
}
