// loop_013: 同座標グループの花弁状オフセット(純関数)
import { describe, expect, it } from "vitest";

import { spiderfyOffsets, type SpiderInput } from "../spiderfy";

const t = (id: string, lat: number, lon: number, type: "temple" | "statue", size = 20): SpiderInput => ({
  entity_id: id,
  lat,
  lon,
  type,
  size,
});

describe("spiderfyOffsets", () => {
  it("単独座標はオフセットなし", () => {
    const m = spiderfyOffsets([t("a", 34.6, 135.7, "temple")]);
    expect(m.get("a")).toEqual([0, 0]);
  });

  it("同座標グループ: 寺が中心、仏像が周囲に等角配置", () => {
    const m = spiderfyOffsets([
      t("statue1", 34.6, 135.7, "statue", 16),
      t("temple1", 34.6, 135.7, "temple", 30),
      t("statue2", 34.6, 135.7, "statue", 16),
    ]);
    expect(m.get("temple1")).toEqual([0, 0]);
    const p1 = m.get("statue1")!;
    const p2 = m.get("statue2")!;
    const r1 = Math.hypot(p1[0], p1[1]);
    const r2 = Math.hypot(p2[0], p2[1]);
    // 半径 = (中心サイズ+花弁サイズ)/2+4 = (30+16)/2+4 = 27
    expect(r1).toBeCloseTo(27, 5);
    expect(r2).toBeCloseTo(27, 5);
    // 2 花弁は 180° 離れる
    const angleDiff = Math.abs(Math.atan2(p1[1], p1[0]) - Math.atan2(p2[1], p2[0]));
    expect(angleDiff).toBeCloseTo(Math.PI, 5);
  });

  it("寺が無いグループは最初の要素(entity_id 順)が中心になる", () => {
    const m = spiderfyOffsets([
      t("s2", 34.6, 135.7, "statue"),
      t("s1", 34.6, 135.7, "statue"),
    ]);
    expect(m.get("s1")).toEqual([0, 0]);
    expect(m.get("s2")).not.toEqual([0, 0]);
  });

  it("決定論: 同じ入力順序の入れ替えでも同じ結果", () => {
    const rows = [
      t("b", 34.6, 135.7, "statue"),
      t("a", 34.6, 135.7, "temple"),
      t("c", 34.6, 135.7, "statue"),
    ];
    const m1 = spiderfyOffsets(rows);
    const m2 = spiderfyOffsets([...rows].reverse());
    expect(m1.get("b")).toEqual(m2.get("b"));
    expect(m1.get("c")).toEqual(m2.get("c"));
  });

  it("異なる座標は別グループ", () => {
    const m = spiderfyOffsets([
      t("a", 34.6, 135.7, "temple"),
      t("b", 34.7, 135.8, "temple"),
    ]);
    expect(m.get("a")).toEqual([0, 0]);
    expect(m.get("b")).toEqual([0, 0]);
  });
});
