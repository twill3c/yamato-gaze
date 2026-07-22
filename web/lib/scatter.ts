// 散布図(F-09)の純関数層 — T-062: xy 欠落・単著者実体の扱い
import type { EntityCounts, Passage } from "./types";

export interface ScatterPoint {
  passage_id: string;
  entity_id: string;
  author: Passage["author"];
  x: number;
  y: number;
  quoteHead: string;
}

export interface ScatterData {
  points: ScatterPoint[];
  droppedNoXy: number; // xy 欠落で落とした件数(暗黙に消さず計数する)
}

/**
 * passages を散布図点列に整形する。
 * - xy が欠落・不正な passage は点にせず droppedNoXy に計数(T-062)
 * - multiOnly=true のとき、単著者実体(counts.authors_count < 2)の passage を除く
 */
export function shapeScatter(
  passages: Passage[],
  counts: Record<string, EntityCounts>,
  opts: { multiOnly?: boolean } = {},
): ScatterData {
  const points: ScatterPoint[] = [];
  let dropped = 0;
  for (const p of passages) {
    if (!p.xy || p.xy.length !== 2 || p.xy.some((v) => !Number.isFinite(v))) {
      dropped += 1;
      continue;
    }
    if (opts.multiOnly && (counts[p.entity_id]?.authors_count ?? 0) < 2) {
      continue;
    }
    points.push({
      passage_id: p.passage_id,
      entity_id: p.entity_id,
      author: p.author,
      x: p.xy[0],
      y: p.xy[1],
      quoteHead: p.quote.replace(/\s+/g, "").slice(0, 40),
    });
  }
  return { points, droppedNoXy: dropped };
}
