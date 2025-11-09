import { useAppSelector } from "@/store/hooks";

export function compareStatusWithConfig(id, type) {
  const config = useAppSelector((state) => state.config);
  const container = useAppSelector((s) =>
    s.containers.find((c) => c.id === id)
  );

  if (!config || !container) return "na";

  const cfg = config[type];

  if (container[type] > cfg.max) return "alert";
  if (container[type] < cfg.min) return "ok";

  return "warn";
}
