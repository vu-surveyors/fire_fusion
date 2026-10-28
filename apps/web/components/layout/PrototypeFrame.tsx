type PrototypeScreen = "overview" | "map" | "calendar" | "cluster" | "validation" | "methods";

type PrototypeFrameProps = {
  screen: PrototypeScreen;
  clusterId?: string;
};

export function PrototypeFrame({ screen, clusterId }: PrototypeFrameProps) {
  const view = screen === "cluster" ? "records" : screen;
  const route = new URLSearchParams({ view });
  if (clusterId) route.set("cluster", clusterId);

  return (
    <iframe
      className="prototype-frame"
      src={`/resources/FireFusion_Desktop_Prototype.html#${route.toString()}`}
      title="FireFusion sensor-harmonized wildfire intelligence"
    />
  );
}
