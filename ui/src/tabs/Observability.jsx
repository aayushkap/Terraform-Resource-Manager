import { useState, useRef, useEffect } from "react";
import { TransformWrapper, TransformComponent } from "react-zoom-pan-pinch";

export default function InfraView() {
  const [centerOffset, setCenterOffset] = useState({ x: 0, y: 0 });
  const [containers, setContainers] = useState([
    { id: 1, x: 200, y: window.innerHeight / 2 + 100 },
    { id: 2, x: 200, y: window.innerHeight / 2 - 100 },
  ]);

  useEffect(() => {
    const gridSize = 2000; // your TransformComponent content size
    setCenterOffset({
      x: window.innerWidth / 2 - gridSize / 2,
      y: window.innerHeight / 2 - gridSize / 2,
    });
  }, []);

  const loadBalancer = { x: 50, y: window.innerHeight / 2 };

  const addContainer = () => {
    const id = Date.now();
    setContainers((prev) => [
      ...prev,
      { id, x: 400 + prev.length * 150, y: 200 },
    ]);
  };

  const updatePos = (id, nx, ny) => {
    setContainers((prev) =>
      prev.map((c) => (c.id === id ? { ...c, x: nx, y: ny } : c))
    );
  };

  return (
    <div style={{ width: "100%", height: "100%", overflow: "hidden" }}>
      <TransformWrapper
        defaultScale={0.1}
        minScale={0.1}
        maxScale={2}
        wheel={{ disabled: true }}
        panning={{ velocityDisabled: true }}
        doubleClick={{ disabled: true }}
        initialPositionX={centerOffset.x}
        initialPositionY={centerOffset.y}
        style={{ width: "100%", height: "100%" }}
      >
        <TransformComponent>
          <div
            style={{
              width: 2000,
              height: 2000,
              position: "relative",
              userSelect: "none",
            }}
          >
            {/* Grid background */}
            <div
              style={{
                position: "absolute",
                width: "100%",
                height: "100%",
                backgroundImage: `
                  linear-gradient(to right, #e1e1e1ff 1px, transparent 1px),
                  linear-gradient(to bottom, #e1e1e1ff 1px, transparent 1px)
                `,
                backgroundSize: "16px 16px",
                zIndex: -1,
              }}
            />

            {/* Load Balancer */}
            <Box label="Load Balancer" x={loadBalancer.x} y={loadBalancer.y} />

            {/* Draggable containers */}
            {containers.map((c) => (
              <DraggableBox
                key={c.id}
                id={c.id}
                label={`Container ${c.id}`}
                x={c.x}
                y={c.y}
                onMove={updatePos}
              />
            ))}

            {/* Add new container */}
            <AddBox
              x={loadBalancer.x}
              y={loadBalancer.y + 150}
              onAdd={addContainer}
            />

            {/* Lines */}
            <svg
              width="100%"
              height="100%"
              style={{
                position: "absolute",
                left: 0,
                top: 0,
                pointerEvents: "none",
              }}
            >
              {containers.map((c) => (
                <line
                  key={c.id}
                  x1={loadBalancer.x + 120}
                  y1={loadBalancer.y + 25}
                  x2={c.x + 0} // right edge dot
                  y2={c.y + 25} // vertical center
                  stroke="gray"
                  strokeDasharray="4 4"
                />
              ))}
            </svg>
          </div>
        </TransformComponent>
      </TransformWrapper>
    </div>
  );
}

// Static box
function Box({ label, x, y }) {
  return (
    <div
      className="box"
      style={{
        position: "absolute",
        left: x,
        top: y,
        width: 120,
        height: 50,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      {label}
    </div>
  );
}

// Draggable container
function DraggableBox({ id, x, y, label, onMove }) {
  const [pos, setPos] = useState({ x, y });
  const dragRef = useRef(null);

  useEffect(() => {
    const handleMove = (e) => {
      if (!dragRef.current) return;
      const { offsetX, offsetY } = dragRef.current;
      const nx = e.clientX - offsetX;
      const ny = e.clientY - offsetY;
      onMove(id, nx, ny);
      setPos({ x: nx, y: ny });
    };
    const handleUp = () => {
      dragRef.current = null;
    };
    window.addEventListener("mousemove", handleMove);
    window.addEventListener("mouseup", handleUp);
    return () => {
      window.removeEventListener("mousemove", handleMove);
      window.removeEventListener("mouseup", handleUp);
    };
  }, [id, onMove]);

  const startDrag = (e) => {
    e.stopPropagation();
    dragRef.current = {
      offsetX: e.clientX - pos.x,
      offsetY: e.clientY - pos.y,
    };
  };

  return (
    <>
      <div
        className="box"
        onMouseDown={startDrag}
        style={{
          position: "absolute",
          left: pos.x,
          top: pos.y,
          width: 120,
          height: 50,
          cursor: "grab",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {label}
      </div>
      <div
        className="status-indicator status-info"
        style={{
          position: "absolute",
          left: pos.x + 0 - 5,
          top: pos.y + 25 - 5,
          pointerEvents: "none",
        }}
      />
    </>
  );
}

// Add container button
function AddBox({ x, y, onAdd }) {
  return (
    <div
      onClick={onAdd}
      style={{
        position: "absolute",
        left: x,
        top: y,
        width: 50,
        height: 50,
        border: "2px dashed #333",
        borderRadius: 6,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        cursor: "pointer",
        fontSize: 24,
        fontWeight: "bold",
        userSelect: "none",
      }}
    >
      +
    </div>
  );
}
