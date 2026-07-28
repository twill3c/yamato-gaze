// loop_011: LICENSE-DATA.md 表示用の最小 Markdown パーサ(純関数)
import { describe, expect, it } from "vitest";

import { linkifySegments, parseMarkdown } from "../markdown";

describe("parseMarkdown", () => {
  it("見出し・箇条書き・段落をブロック化する", () => {
    const md = "# 題\n\n本文の段落。\n\n## 小見出し\n\n- 項目A\n- 項目B\n";
    expect(parseMarkdown(md)).toEqual([
      { type: "h1", text: "題" },
      { type: "p", text: "本文の段落。" },
      { type: "h2", text: "小見出し" },
      { type: "li", text: "項目A" },
      { type: "li", text: "項目B" },
    ]);
  });

  it("連続行の段落は連結し、空行で区切る", () => {
    const md = "一行目\n二行目\n\n次の段落\n";
    expect(parseMarkdown(md)).toEqual([
      { type: "p", text: "一行目 二行目" },
      { type: "p", text: "次の段落" },
    ]);
  });

  it("太字記法 ** は除去して素の文字列にする", () => {
    expect(parseMarkdown("**強調** を含む\n")).toEqual([
      { type: "p", text: "強調 を含む" },
    ]);
  });
});

describe("linkifySegments", () => {
  it("素の URL をリンクセグメントに分離する", () => {
    const segs = linkifySegments("青空文庫(https://www.aozora.gr.jp/)に従う");
    expect(segs).toEqual([
      { text: "青空文庫(", url: null },
      { text: "https://www.aozora.gr.jp/", url: "https://www.aozora.gr.jp/" },
      { text: ")に従う", url: null },
    ]);
  });

  it("URL が無ければ 1 セグメント", () => {
    expect(linkifySegments("テキストのみ")).toEqual([{ text: "テキストのみ", url: null }]);
  });
});
