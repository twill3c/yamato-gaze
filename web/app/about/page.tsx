"use client";

// ライセンスとデータについて(loop_011)。LICENSE-DATA.md(ビルド時同期)が正 —
// 手書き複製をしないことで文書乖離を防ぐ。オフラインでも読める(N-05)
import Link from "next/link";
import { useEffect, useState } from "react";

import Attribution from "@/components/Attribution";
import { linkifySegments, parseMarkdown, type MdBlock } from "@/lib/markdown";

const GITHUB_URL = "https://github.com/twill3c/yamato-gaze";

function Line({ text }: { text: string }) {
  return (
    <>
      {linkifySegments(text).map((s, i) =>
        s.url ? (
          <a key={i} href={s.url} target="_blank" rel="noreferrer">
            {s.text}
          </a>
        ) : (
          <span key={i}>{s.text}</span>
        ),
      )}
    </>
  );
}

export default function AboutPage() {
  const [blocks, setBlocks] = useState<MdBlock[] | null>(null);

  useEffect(() => {
    fetch("../LICENSE-DATA.md")
      .then((r) => (r.ok ? r.text() : Promise.reject(r.status)))
      .then((md) => setBlocks(parseMarkdown(md)))
      .catch(() => setBlocks(null));
  }, []);

  return (
    <div className="app">
      <header className="header">
        <h1>
          ライセンスとデータについて
          <Link className="nav-link" href="../">
            ← 地図
          </Link>
        </h1>
      </header>
      <main className="about-main">
        <section className="about-code">
          <h2>コード</h2>
          <p>
            本サイトと分析パイプラインのソースコードは MIT License で公開しています:{" "}
            <a href={GITHUB_URL} target="_blank" rel="noreferrer">
              {GITHUB_URL}
            </a>
          </p>
        </section>
        {blocks ? (
          <section className="about-data">
            {blocks.map((b, i) =>
              b.type === "h1" ? (
                <h2 key={i}>{b.text}</h2>
              ) : b.type === "h2" ? (
                <h3 key={i}>
                  <Line text={b.text} />
                </h3>
              ) : b.type === "li" ? (
                <ul key={i}>
                  <li>
                    <Line text={b.text} />
                  </li>
                </ul>
              ) : (
                <p key={i}>
                  <Line text={b.text} />
                </p>
              ),
            )}
          </section>
        ) : (
          <p className="about-fallback">
            ライセンス文書を読み込めませんでした。
            <a href={`${GITHUB_URL}/blob/main/LICENSE-DATA.md`} target="_blank" rel="noreferrer">
              GitHub 上の LICENSE-DATA.md
            </a>
            を参照してください。
          </p>
        )}
      </main>
      <Attribution dataPrefix="../data" basePrefix="../" />
    </div>
  );
}
