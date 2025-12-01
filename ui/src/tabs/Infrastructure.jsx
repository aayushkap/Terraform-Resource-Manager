import { useState, useRef, useEffect } from "react";
import { TransformWrapper, TransformComponent } from "react-zoom-pan-pinch";
import StaticBox from "../components/ContainerBox/StaticBox";
import DraggableBox from "../components/ContainerBox/DraggableBox";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { setContainer } from "@/store/slices/containersSlice";
import { setSelectedContainer } from "@/store/slices/containerSlice";
import { setConfig } from "@/store/slices/configSlice";
import ContainerDetailsModal from "@/components/ContainerDetails";
import { useGetContainersQuery } from "@/api/containersApi";

import InfraControls from "../components/InfraControls";
import Dropdown from "../components/UI/Dropdown";

const CANVAS_WIDTH = 4000;
const CANVAS_HEIGHT = 3000;
const CENTER_X = CANVAS_WIDTH / 2;
const CENTER_Y = CANVAS_HEIGHT / 2;

export default function InfraView() {
  const dispatch = useAppDispatch();
  const containers = useAppSelector((state) => state.containers);
  const config = useAppSelector((state) => state.config);
  const selectedContainer = useAppSelector((state) => state.container);

  const [viewportSize, setViewportSize] = useState({ width: 0, height: 0 });
  const containerRef = useRef(null);
  const transformRef = useRef(null);

  useEffect(() => {
    if (containerRef.current) {
      const { clientWidth, clientHeight } = containerRef.current;
      setViewportSize({ width: clientWidth, height: clientHeight });
    }
  }, []);

  useGetContainersQuery(undefined, {
    pollingInterval: 5000,
    skip: viewportSize.width === 0,
  }); // This will set containers but we read from state, not here

  const loadBalancer = { x: CENTER_X - 400, y: CENTER_Y };

  const updatePos = (id, nx, ny) => {
    dispatch(setContainer({ id, x: nx, y: ny }));
  };

  const handleReset = () => {
    const numContainers = containers.length;

    const startX = CENTER_X + 200;

    const dynamicOffset = numContainers > 4 ? 280 : 240;
    const startYRange = CENTER_Y - dynamicOffset;

    const endYRange = CENTER_Y + dynamicOffset * 2;
    const range = endYRange - startYRange;
    const spacing = range / numContainers;

    containers.forEach((container, index) => {
      dispatch(
        setContainer({
          id: container.id,
          x: startX,
          y: startYRange + index * spacing,
        })
      );
    });
  };

  // initial position to center the canvas content
  const initialX = viewportSize.width
    ? -(CENTER_X - viewportSize.width / 2)
    : -1200;
  const initialY = viewportSize.height
    ? -(CENTER_Y - viewportSize.height / 2)
    : -900;

  const doubleClickContainer = (containerId) => {
    if (selectedContainer) {
      dispatch(setSelectedContainer(null));
      return;
    }
    const container = containers.find((c) => c.id === containerId);
    if (!container || !transformRef.current) return;

    const { setTransform } = transformRef.current;

    const offsetX = viewportSize.width / 4 - container.x;
    const offsetY = viewportSize.height / 2 - container.y;

    setTransform(offsetX, offsetY, 1, 300); // 300ms animation
    dispatch(setSelectedContainer(containerId));
  };

  return (
    <div
      ref={containerRef}
      style={{ width: "100%", height: "100%", overflow: "hidden" }}
    >
      {viewportSize.width > 0 && (
        <>
          {selectedContainer && <ContainerDetailsModal />}
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
            doubleClick={{ disabled: true }}
            ref={transformRef}
          >
            <InfraControls onReset={handleReset} />
            <div
              style={{
                position: "absolute",
                top: "16px",
                right: "16px",
                zIndex: 100,
              }}
            >
              <Dropdown
                options={[
                  { label: "Auto - CPU", value: "auto-cpu" },
                  { label: "Auto - Memory", value: "auto-memory" },
                  { label: "Auto - RPM", value: "auto-rpm" },
                  { label: "Auto - Cumulative", value: "auto-cumulative" },
                  { label: "Manual", value: "manual" },
                ]}
                value={config.mode}
                onChange={(option) => dispatch(setConfig({ mode: option }))}
              />
            </div>

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
                    radial-gradient(#e0e0e0 1px, transparent 1px)
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
                    onDoubleClick={() => doubleClickContainer(c.id)}
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
                      y1={loadBalancer.y + 30}
                      x2={c.x}
                      y2={c.y + 30}
                      stroke="#a0a0a0"
                      strokeWidth="2"
                      strokeDasharray="4 4"
                    />
                  ))}
                </svg>
              </div>
            </TransformComponent>
          </TransformWrapper>
        </>
      )}
    </div>
  );
}
