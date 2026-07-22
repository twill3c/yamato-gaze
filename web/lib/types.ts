export type Author = "watsuji" | "kamei" | "hori";

export const AUTHOR_LABEL: Record<Author, string> = {
  watsuji: "和辻哲郎",
  kamei: "亀井勝一郎",
  hori: "堀辰雄",
};

// 著者カテゴリ配色(dataviz validator 全チェック PASS: #0072B2/#D55E00/#009E73)
export const AUTHOR_COLOR: Record<Author, string> = {
  watsuji: "#0072B2",
  kamei: "#D55E00",
  hori: "#009E73",
};

// 著者数(1..3)は順序量 → 単色ブルーの明度単調ランプ(sequential)。
// 白リング・サイズ・凡例・ツールチップの副次符号化と併用する
export const AUTHORS_COUNT_COLOR = ["#87a5dd", "#4a6fb8", "#1f3f78"];

export interface SiteProps {
  entity_id: string;
  name: string;
  type: "temple" | "statue";
  parent: string | null;
  authors_count: number;
  passage_count: number;
  lat: number;
  lon: number;
  verified: string;
  license: string;
}

export interface SiteFeature {
  type: "Feature";
  geometry: { type: "Point"; coordinates: [number, number] };
  properties: SiteProps;
}

export interface Passage {
  passage_id: string;
  entity_id: string;
  author: Author;
  work: string;
  quote: string;
  source_note: string;
  char_start: number;
  char_end: number;
  features: Record<string, number>;
  lexicon_version: string;
  xy: [number, number] | null;
}

export interface EntityCounts {
  passage_count: number;
  authors_count: number;
  by_author: Partial<Record<Author, number>>;
}

export const FEATURE_LABEL: Record<string, string> = {
  comparative: "比較参照",
  religious: "宗教語彙",
  sensory: "感覚描写",
  first_person: "一人称",
  present_tense: "現在形",
  sent_len: "平均文長",
  comma_density: "読点密度",
};
