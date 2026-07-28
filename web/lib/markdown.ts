// LICENSE-DATA.md 表示用の最小 Markdown パーサ(loop_011)。
// 対応: # / ## 見出し、- 箇条書き、段落(連続行連結)、** の除去、素 URL の linkify。
// 汎用 md ライブラリを足さないのは依存最小の方針(サイト内で必要な記法のみ)

export interface MdBlock {
  type: "h1" | "h2" | "li" | "p";
  text: string;
}

function clean(text: string): string {
  return text.replace(/\*\*/g, "").trim();
}

export function parseMarkdown(md: string): MdBlock[] {
  const blocks: MdBlock[] = [];
  let para: string[] = [];
  const flush = () => {
    if (para.length) {
      blocks.push({ type: "p", text: clean(para.join(" ")) });
      para = [];
    }
  };
  for (const raw of md.split(/\r?\n/)) {
    const line = raw.trimEnd();
    if (!line.trim()) {
      flush();
      continue;
    }
    if (line.startsWith("## ")) {
      flush();
      blocks.push({ type: "h2", text: clean(line.slice(3)) });
    } else if (line.startsWith("# ")) {
      flush();
      blocks.push({ type: "h1", text: clean(line.slice(2)) });
    } else if (line.startsWith("- ")) {
      flush();
      blocks.push({ type: "li", text: clean(line.slice(2)) });
    } else {
      para.push(line.trim());
    }
  }
  flush();
  return blocks;
}

export interface LinkSegment {
  text: string;
  url: string | null;
}

const RE_URL = /https?:\/\/[^\s)、」]+/g;

export function linkifySegments(text: string): LinkSegment[] {
  const segs: LinkSegment[] = [];
  let last = 0;
  for (const m of text.matchAll(RE_URL)) {
    if (m.index! > last) segs.push({ text: text.slice(last, m.index), url: null });
    segs.push({ text: m[0], url: m[0] });
    last = m.index! + m[0].length;
  }
  if (last < text.length) segs.push({ text: text.slice(last), url: null });
  return segs.length ? segs : [{ text, url: null }];
}
