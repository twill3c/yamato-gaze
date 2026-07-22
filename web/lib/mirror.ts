// 三面鏡(F-08)の純関数層 — T-061: 著者チップの選択集合 → 表示列の写像
import type { Author, Passage } from "./types";

export const AUTHOR_ORDER: Author[] = ["watsuji", "kamei", "hori"];

/**
 * チップ選択集合と実体の所持著者から、表示すべき著者列を固定順で返す。
 * - selected が空 = 全著者表示(所持著者のみ)
 * - selected に指定があれば、その積集合(所持著者 ∩ 選択)
 */
export function visibleColumns(
  available: Author[],
  selected: Author[],
): Author[] {
  const avail = new Set(available);
  const base = AUTHOR_ORDER.filter((a) => avail.has(a));
  if (selected.length === 0) return base;
  const sel = new Set(selected);
  return base.filter((a) => sel.has(a));
}

/** 実体の passages を著者別に固定順でグループ化する */
export function groupByAuthor(
  passages: Passage[],
  entityId: string,
): Map<Author, Passage[]> {
  const m = new Map<Author, Passage[]>();
  for (const a of AUTHOR_ORDER) m.set(a, []);
  for (const p of passages) {
    if (p.entity_id === entityId) m.get(p.author)!.push(p);
  }
  for (const a of AUTHOR_ORDER) {
    if (m.get(a)!.length === 0) m.delete(a);
  }
  return m;
}
