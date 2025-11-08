import { useState, useRef, useEffect } from "react";
import { TransformWrapper, TransformComponent } from "react-zoom-pan-pinch";

export default function InfraView() {
  // const [containers, setContainers] = useState([
  //   { id: 1, x: 200, y: window.innerHeight / 2 + 100 },
  //   { id: 2, x: 200, y: window.innerHeight / 2 - 100 },
  // ]);

  const containers = useAppSelector((state) => state.containers);

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
