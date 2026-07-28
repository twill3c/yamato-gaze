// loop_009: PC 軸の解釈ラベルに負荷量根拠を付ける純関数
import { describe, expect, it } from "vitest";

import { loadingsSummary } from "../loadings";

const ORDER = ["comparative", "religious", "sensory", "first_person"];
const LABELS: Record<string, string> = {
  comparative: "比較参照",
  religious: "宗教語彙",
  sensory: "感覚描写",
  first_person: "一人称",
};

describe("loadingsSummary", () => {
  it("負荷量の絶対値上位 n 件を符号付きで返す", () => {
    const s = loadingsSummary([0.1, -0.6, 0.5, -0.05], ORDER, LABELS, 2);
    expect(s).toBe("宗教語彙−0.60 ・感覚描写+0.50");
  });

  it("n が特徴数を超えても安全", () => {
    const s = loadingsSummary([0.3, 0.2], ["a", "b"], { a: "A", b: "B" }, 5);
    expect(s).toBe("A+0.30 ・B+0.20");
  });

  it("ラベル未定義の特徴はキー名で出す", () => {
    const s = loadingsSummary([0.9], ["mystery"], {}, 1);
    expect(s).toBe("mystery+0.90");
  });
});
