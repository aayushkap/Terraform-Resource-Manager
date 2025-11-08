import { useState, useRef, useEffect } from "react";
import { TransformWrapper, TransformComponent } from "react-zoom-pan-pinch";
import StaticBox from "../components/ContainerBox/StaticBox";
import DraggableBox from "../components/ContainerBox/DraggableBox";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { setContainer } from "@/store/slices/containersSlice";
import InfraControls from "../components/InfraControls";

const CANVAS_WIDTH = 4000;
const CANVAS_HEIGHT = 3000;
const CENTER_X = CANVAS_WIDTH / 2;
const CENTER_Y = CANVAS_HEIGHT / 2;

export default function InfraView() {
  const dispatch = useAppDispatch();
  const containers = useAppSelector((state) => state.containers);
  const [viewportSize, setViewportSize] = useState({ width: 0, height: 0 });
  const containerRef = useRef(null);

  useEffect(() => {
    if (containerRef.current) {
      const { clientWidth, clientHeight } = containerRef.current;
      setViewportSize({ width: clientWidth, height: clientHeight });
    }
  }, []);

  useEffect(() => {
    dispatch(
      setContainer({
        id: 1,
        x: CENTER_X,
        y: CENTER_Y,
        cpu: 40,
        mem: 60,
        rpm: 80,
        label: "fastapi-app-1",
      })
    );
    dispatch(
      setContainer({
        id: 2,
        x: CENTER_X,
        y: CENTER_Y + 100,
        cpu: 20,
        mem: 60,
        rpm: 80,
        label: "fastapi-app-2",
      })
    );
  }, []);

  const loadBalancer = { x: CENTER_X - 400, y: CENTER_Y };

  const updatePos = (id, nx, ny) => {
    dispatch(setContainer({ id, x: nx, y: ny }));
  };

  const handleReset = () => {
    const spacing = 100;
    const startX = CENTER_X + 200;
    const startY = CENTER_Y - 200;
    const columns = 1;

    containers.forEach((container, index) => {
      const col = index % columns;
      const row = Math.floor(index / columns);

      dispatch(
        setContainer({
          id: container.id,
          x: startX + col * spacing,
          y: startY + row * spacing,
        })
      );
    });
  };

  // Calculate initial position to center the canvas content
  const initialX = viewportSize.width
    ? -(CENTER_X - viewportSize.width / 2)
    : -1200;
  const initialY = viewportSize.height
    ? -(CENTER_Y - viewportSize.height / 2)
    : -900;

  return (
    <div
      ref={containerRef}
      style={{ width: "100%", height: "100%", overflow: "hidden" }}
    >
      {viewportSize.width > 0 && (
        <TransformWrapper
          initialScale={1}
          initialPositionX={initialX}
          initialPositionY={initialY}
          minScale={0.75} // max zoom out
          maxScale={1.5} // max zoom in
          limitToBounds={true}
          bounds={{
            left: -(CANVAS_WIDTH - viewportSize.width),
            top: -(CANVAS_HEIGHT - viewportSize.height),
            right: 0,
            bottom: 0,
          }}
          centerZoomedOut={false}
          wheel={{ step: 0.1 }}
          panning={{ velocityDisabled: true }}
          doubleClick={{ disabled: false }}
        >
          <InfraControls onReset={handleReset} />

          <TransformComponent
            wrapperStyle={{
              width: "100%",
              height: "100%",
            }}
            // contentStyle={{
            //   width: "100%",
            //   height: "100%",
            // }}
          >
            <div
              style={{
                width: CANVAS_WIDTH,
                height: CANVAS_HEIGHT,
                position: "relative",
                userSelect: "none",
              }}
            >
              {/* Grid background */}
              <div
                style={{
                  position: "absolute",
                  width: "5000px",
                  height: "5000px",
                  backgroundImage: `
                    radial-gradient(#ccc 1px, transparent 1px)
                  `,
                  backgroundSize: "16px 16px",
                  backgroundPosition: "0 0",
                  zIndex: -1,
                }}
              />

              <StaticBox
                label="Load Balancer"
                x={loadBalancer.x}
                y={loadBalancer.y}
              />

              {containers.map((c) => (
                <DraggableBox
                  key={c.id}
                  id={c.id}
                  label={`fastapi-app-${c.id}`}
                  x={c.x}
                  y={c.y}
                  onMove={updatePos}
                />
              ))}

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
                    x2={c.x}
                    y2={c.y + 25}
                    stroke="#a0a0a0"
                    strokeWidth="2"
                    strokeDasharray="4 4"
                  />
                ))}
              </svg>
            </div>
          </TransformComponent>
        </TransformWrapper>
      )}
    </div>
  );
}
