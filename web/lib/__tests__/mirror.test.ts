// T-061: 著者チップの選択集合 → 表示列の写像(純関数)
import { describe, expect, it } from "vitest";

import { groupByAuthor, visibleColumns } from "../mirror";
import type { Passage } from "../types";

const p = (id: string, author: Passage["author"], eid = "e1"): Passage => ({
  passage_id: id,
  entity_id: eid,
  author,
  work: "w",
  quote: "q",
  source_note: "s",
  char_start: 0,
  char_end: 1,
  features: {},
  lexicon_version: "v",
  xy: [0, 0],
});

describe("visibleColumns (T-061)", () => {
  it("選択なし = 所持著者を固定順で全表示", () => {
    expect(visibleColumns(["hori", "watsuji"], [])).toEqual(["watsuji", "hori"]);
  });
  it("選択ありは積集合(固定順を保つ)", () => {
    expect(visibleColumns(["watsuji", "kamei", "hori"], ["hori", "kamei"])).toEqual([
      "kamei",
      "hori",
    ]);
  });
  it("所持しない著者を選択しても列は出ない", () => {
    expect(visibleColumns(["watsuji"], ["kamei"])).toEqual([]);
  });
});

describe("groupByAuthor", () => {
  it("実体の passage を著者別固定順にグループ化し、空著者は含めない", () => {
    const g = groupByAuthor(
      [p("1", "hori"), p("2", "watsuji"), p("3", "hori"), p("4", "kamei", "other")],
      "e1",
    );
    expect([...g.keys()]).toEqual(["watsuji", "hori"]);
    expect(g.get("hori")!.map((x) => x.passage_id)).toEqual(["1", "3"]);
  });
});
