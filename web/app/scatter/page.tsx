"use client";

// スタンス空間の散布図(F-09): 点 = passage、色 = 著者、ホバーで引用先頭、
// クリックで該当実体の地図ページへ。スケールは d3-scale
import { scaleLinear } from "d3-scale";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import Attribution from "@/components/Attribution";
import { loadingsSummary, type SiteMeta } from "@/lib/loadings";
import { shapeScatter, type ScatterPoint } from "@/lib/scatter";
import {
  AUTHOR_COLOR,
  AUTHOR_LABEL,
  FEATURE_LABEL,
  type Author,
  type EntityCounts,
  type Passage,
} from "@/lib/types";

const W = 900;
const H = 600;
const PAD = 40;

export default function ScatterPage() {
  const [passages, setPassages] = useState<Passage[]>([]);
  const [counts, setCounts] = useState<Record<string, EntityCounts>>({});
  const [meta, setMeta] = useState<SiteMeta | null>(null);
  const [multiOnly, setMultiOnly] = useState(false);
  const [hover, setHover] = useState<ScatterPoint | null>(null);

  useEffect(() => {
    fetch("../data/passages.json")
      .then((r) => r.json())
      .then(setPassages)
      .catch(() => setPassages([]));
    fetch("../data/counts.json")
      .then((r) => r.json())
      .then(setCounts)
      .catch(() => setCounts({}));
    fetch("../data/meta.json")
      .then((r) => r.json())
      .then(setMeta)
      .catch(() => setMeta(null));
  }, []);

  // 軸ラベルの「解釈」に負荷量根拠を添える(ラベル自体は人間の読み)
  const pcNote = (i: 0 | 1) =>
    meta
      ? `負荷量上位: ${loadingsSummary(meta.pca.components[i], meta.pca.feature_order, FEATURE_LABEL, 3)}(寄与率 ${(meta.pca.explained[i] * 100).toFixed(1)}%)`
      : "";

  const data = useMemo(
    () => shapeScatter(passages, counts, { multiOnly }),
    [passages, counts, multiOnly],
  );

  const [sx, sy] = useMemo(() => {
    const xs = data.points.map((p) => p.x);
    const ys = data.points.map((p) => p.y);
    const x = scaleLinear()
      .domain([Math.min(...xs, -1), Math.max(...xs, 1)])
      .range([PAD, W - PAD]);
    const y = scaleLinear()
      .domain([Math.min(...ys, -1), Math.max(...ys, 1)])
      .range([H - PAD, PAD]);
    return [x, y] as const;
  }, [data]);

  return (
    <div className="app">
      <header className="header">
        <h1>
          スタンス空間(PC1 × PC2)
          <span className="count">
            {data.points.length} 節{data.droppedNoXy > 0 ? ` / xy欠落 ${data.droppedNoXy}` : ""}
          </span>
          <Link className="nav-link" href="../">
            ← 地図
          </Link>
        </h1>
        <div className="legend">
          {(Object.keys(AUTHOR_LABEL) as Author[]).map((a) => (
            <span key={a} className="legend-item">
              <span className="swatch" style={{ background: AUTHOR_COLOR[a] }} />
              {AUTHOR_LABEL[a]}
            </span>
          ))}
          <button
            className="chip"
            aria-pressed={multiOnly}
            onClick={() => setMultiOnly((v) => !v)}
          >
            2 名以上の実体のみ
          </button>
        </div>
      </header>
      <main className="scatter-main">
        <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="スタンス空間散布図">
          <line x1={PAD} y1={sy(0)} x2={W - PAD} y2={sy(0)} className="axis" />
          <line x1={sx(0)} y1={PAD} x2={sx(0)} y2={H - PAD} className="axis" />
          <text x={W - PAD} y={sy(0) - 6} className="axis-label" textAnchor="end">
            <title>{pcNote(0)}</title>
            PC1(解釈: 内省 ⇔ スケッチ)
          </text>
          <text x={sx(0) + 6} y={PAD + 4} className="axis-label">
            <title>{pcNote(1)}</title>
            PC2(解釈: 美術史比較)
          </text>
          {data.points.map((p) => (
            <Link key={p.passage_id} href={`../?e=${p.entity_id}`}>
              <circle
                cx={sx(p.x)}
                cy={sy(p.y)}
                r={hover?.passage_id === p.passage_id ? 7 : 4.5}
                fill={AUTHOR_COLOR[p.author]}
                className="dot"
                onMouseEnter={() => setHover(p)}
                onMouseLeave={() => setHover(null)}
              />
            </Link>
          ))}
        </svg>
        {meta && (
          <p className="pc-note">
            軸ラベルは負荷量からの解釈。PC1 {pcNote(0)} / PC2 {pcNote(1)}
          </p>
        )}
        {hover && (
          <div className="tooltip" role="status">
            <strong>{AUTHOR_LABEL[hover.author]}</strong> — {hover.quoteHead}…
          </div>
        )}
      </main>
      <Attribution meta={meta} dataPrefix="../data" basePrefix="../" />
    </div>
  );
}
