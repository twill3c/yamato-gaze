// T-062: 散布図データ整形 — xy 欠落・単著者実体の扱い
import { describe, expect, it } from "vitest";

import { shapeScatter } from "../scatter";
import type { EntityCounts, Passage } from "../types";

const p = (id: string, eid: string, xy: [number, number] | null): Passage => ({
  passage_id: id,
  entity_id: eid,
  author: "watsuji",
  work: "w",
  quote: "　法隆寺へ。とても長い引用文がここに続くとして先頭だけを表示する。",
  source_note: "s",
  char_start: 0,
  char_end: 1,
  features: {},
  lexicon_version: "v",
  xy,
});

const counts: Record<string, EntityCounts> = {
  multi: { passage_count: 2, authors_count: 3, by_author: {} },
  solo: { passage_count: 1, authors_count: 1, by_author: {} },
};

describe("shapeScatter (T-062)", () => {
  it("xy 欠落は点にせず計数する", () => {
    const d = shapeScatter([p("a", "multi", [1, 2]), p("b", "multi", null)], counts);
    expect(d.points.map((x) => x.passage_id)).toEqual(["a"]);
    expect(d.droppedNoXy).toBe(1);
  });

  it("multiOnly で単著者実体の passage を除く(欠落計数とは別勘定)", () => {
    const d = shapeScatter(
      [p("a", "multi", [1, 2]), p("b", "solo", [3, 4]), p("c", "solo", null)],
      counts,
      { multiOnly: true },
    );
    expect(d.points.map((x) => x.passage_id)).toEqual(["a"]);
    expect(d.droppedNoXy).toBe(1);
  });

  it("quoteHead は空白除去のうえ 40 字まで", () => {
    const d = shapeScatter([p("a", "multi", [0, 0])], counts);
    expect(d.points[0].quoteHead.length).toBeLessThanOrEqual(40);
    expect(d.points[0].quoteHead.startsWith("法隆寺へ。")).toBe(true);
  });
});
