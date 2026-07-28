// 同座標グループの花弁状オフセット(loop_013)。
// 座標データは動かさず、MapLibre Marker のピクセルオフセットで表示だけ散らす
// (ズーム非依存)。寺を中心(オフセットなし)、仏像を周囲に等角配置する。

export interface SpiderInput {
  entity_id: string;
  lat: number;
  lon: number;
  type: "temple" | "statue";
  size: number; // ピン直径(px)
}

const MARGIN = 4; // 中心ピンと花弁ピンの縁の隙間(px)

/** entity_id → [dx, dy](px)。単独座標・中心は [0, 0] */
export function spiderfyOffsets(rows: SpiderInput[]): Map<string, [number, number]> {
  const groups = new Map<string, SpiderInput[]>();
  for (const r of rows) {
    const key = `${r.lat},${r.lon}`;
    groups.set(key, [...(groups.get(key) ?? []), r]);
  }

  const out = new Map<string, [number, number]>();
  for (const members of groups.values()) {
    const sorted = [...members].sort((a, b) => a.entity_id.localeCompare(b.entity_id));
    const anchor = sorted.find((m) => m.type === "temple") ?? sorted[0];
    out.set(anchor.entity_id, [0, 0]);
    const petals = sorted.filter((m) => m !== anchor);
    petals.forEach((p, i) => {
      const angle = -Math.PI / 2 + (2 * Math.PI * i) / petals.length;
      const radius = (anchor.size + p.size) / 2 + MARGIN;
      out.set(p.entity_id, [
        Math.cos(angle) * radius,
        Math.sin(angle) * radius,
      ]);
    });
  }
  return out;
}
