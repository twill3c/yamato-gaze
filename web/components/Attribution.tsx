// N-03/N-04: 青空文庫・地理院タイルの帰属を常時表示。
// loop_009: 再現性情報(lexicon_version・生成日時)とデータ直リンク(CC BY の実利化)
import type { SiteMeta } from "@/lib/loadings";

const GITHUB_URL = "https://github.com/twill3c/yamato-gaze";

export default function Attribution({
  meta,
  dataPrefix = "data",
  basePrefix = "",
}: {
  meta?: SiteMeta | null;
  dataPrefix?: string;
  basePrefix?: string;
}) {
  return (
    <footer className="attribution">
      <div>
        地図タイル:{" "}
        <a href="https://maps.gsi.go.jp/development/ichiran.html" target="_blank" rel="noreferrer">
          国土地理院
        </a>
        {" ｜ 本文: "}
        <a href="https://www.aozora.gr.jp/" target="_blank" rel="noreferrer">
          青空文庫
        </a>
        (PD・底本表記は各引用末尾)｜ 特徴量・整列データ: CC BY 4.0(yamato-gaze)｜ DL:{" "}
        <a href={`${dataPrefix}/sites.geojson`} download>
          sites.geojson
        </a>
        ・
        <a href={`${dataPrefix}/passages.json`} download>
          passages.json
        </a>
        ・
        <a href={`${dataPrefix}/counts.json`} download>
          counts.json
        </a>
        ・
        <a href={`${dataPrefix}/meta.json`} download>
          meta.json
        </a>
        {" ｜ コード: "}
        <a href={`${GITHUB_URL}/blob/main/LICENSE`} target="_blank" rel="noreferrer">
          MIT License
        </a>
        {" © 2026 坂田哲朗 ・ "}
        <a href={GITHUB_URL} target="_blank" rel="noreferrer">
          GitHub
        </a>
        {" ｜ "}
        <a href={`${basePrefix}about/`}>ライセンス詳細</a>
        {" ・ "}
        <a
          href="https://claude.ai/code/artifact/1159c1df-af03-4361-9628-b897bcf6b5e8"
          target="_blank"
          rel="noreferrer"
        >
          大和路の三面鏡の読み方
        </a>
        {" ・ "}
        <a
          href="https://claude.ai/code/artifact/80fded79-8147-46ef-a04b-58f38a7026fa"
          target="_blank"
          rel="noreferrer"
        >
          大和路の視線設計図
        </a>
        {" ・ "}
        <a href="https://app-menu-amber.vercel.app" target="_blank" rel="noopener">
          App Menu
        </a>
      </div>
      {meta && (
        <div className="repro">
          {/* 表示は日付まで。完全なタイムスタンプは meta.json(DL 可)に保持 */}
          再現性: 辞書 {meta.lexicon_version} ／ 生成 {meta.generated_at.slice(0, 10)} ／{" "}
          {meta.n_passages} 節
        </div>
      )}
    </footer>
  );
}
