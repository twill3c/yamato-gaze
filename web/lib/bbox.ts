// 全ピンのバウンディングボックス(loop_014)。初期表示の fitBounds に使う —
// 固定 center/zoom は画面幅・解像度で写る範囲が変わり、広い画面では大阪湾まで
// 入って被写体を見失う(端末依存の初期表示問題の恒久対処)
import type { SiteFeature } from "./types";

export type Bbox = [[number, number], [number, number]]; // [[west, south], [east, north]]

export function sitesBbox(
  features: Pick<SiteFeature, "geometry">[],
): Bbox | null {
  if (features.length === 0) return null;
  let west = Infinity;
  let south = Infinity;
  let east = -Infinity;
  let north = -Infinity;
  for (const f of features) {
    const [lon, lat] = f.geometry.coordinates;
    west = Math.min(west, lon);
    south = Math.min(south, lat);
    east = Math.max(east, lon);
    north = Math.max(north, lat);
  }
  return [
    [west, south],
    [east, north],
  ];
}
