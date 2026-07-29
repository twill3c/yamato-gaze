// loop_014: 全ピンのバウンディングボックス(初期 fitBounds 用の純関数)
import { describe, expect, it } from "vitest";

import { sitesBbox } from "../bbox";

const f = (lon: number, lat: number) => ({
  type: "Feature" as const,
  geometry: { type: "Point" as const, coordinates: [lon, lat] as [number, number] },
  properties: {} as never,
});

describe("sitesBbox", () => {
  it("複数点の最小・最大を返す([[west, south], [east, north]])", () => {
    const b = sitesBbox([f(135.73, 34.61), f(135.87, 34.72), f(135.78, 34.49)]);
    expect(b).toEqual([
      [135.73, 34.49],
      [135.87, 34.72],
    ]);
  });

  it("空配列は null", () => {
    expect(sitesBbox([])).toBeNull();
  });

  it("1 点のみは退化 bbox(fitBounds の maxZoom で吸収)", () => {
    expect(sitesBbox([f(135.76, 34.63)])).toEqual([
      [135.76, 34.63],
      [135.76, 34.63],
    ]);
  });
});
