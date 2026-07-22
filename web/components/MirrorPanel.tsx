"use client";

// 三面鏡パネル(F-08): 実体を選ぶと著者列を並置。著者チップで列の表示切替、
// 引用は serif、末尾に底本表記。スタンスバーは列ごとの平均値(率系 5 特徴)
import { useMemo, useState } from "react";

import { AUTHOR_ORDER, groupByAuthor, visibleColumns } from "@/lib/mirror";
import {
  AUTHOR_COLOR,
  AUTHOR_LABEL,
  FEATURE_LABEL,
  type Author,
  type Passage,
  type SiteProps,
} from "@/lib/types";

const BAR_FEATURES = ["comparative", "religious", "sensory", "first_person", "present_tense"];

function mean(ps: Passage[], key: string): number {
  if (ps.length === 0) return 0;
  return ps.reduce((s, p) => s + (p.features[key] ?? 0), 0) / ps.length;
}

export default function MirrorPanel({
  site,
  passages,
  onClose,
}: {
  site: SiteProps;
  passages: Passage[];
  onClose: () => void;
}) {
  const [selected, setSelected] = useState<Author[]>([]);
  const groups = useMemo(() => groupByAuthor(passages, site.entity_id), [passages, site]);
  const available = [...groups.keys()];
  const columns = visibleColumns(available, selected);

  // バー正規化: この実体の列平均の最大値を 1 とする(列間比較のため)
  const barMax: Record<string, number> = {};
  for (const f of BAR_FEATURES) {
    barMax[f] = Math.max(...available.map((a) => mean(groups.get(a)!, f)), 1e-9);
  }

  const toggle = (a: Author) =>
    setSelected((cur) => (cur.includes(a) ? cur.filter((x) => x !== a) : [...cur, a]));

  return (
    <section className="mirror" aria-label={`${site.name} の三面鏡`}>
      <header className="mirror-head">
        <h2>
          {site.name}
          <span className="count">
            {site.authors_count} 名 / {site.passage_count} 節
          </span>
        </h2>
        <div className="chips">
          {AUTHOR_ORDER.filter((a) => available.includes(a)).map((a) => (
            <button
              key={a}
              className="chip"
              aria-pressed={selected.length === 0 || selected.includes(a)}
              onClick={() => toggle(a)}
            >
              <span className="swatch" style={{ background: AUTHOR_COLOR[a] }} />
              {AUTHOR_LABEL[a]}
            </button>
          ))}
        </div>
        <button className="close" onClick={onClose} aria-label="閉じる">
          ×
        </button>
      </header>
      <div className="mirror-columns" data-cols={columns.length}>
        {columns.map((a) => {
          const ps = groups.get(a)!;
          return (
            <article key={a} className="mirror-col">
              <h3 style={{ borderColor: AUTHOR_COLOR[a] }}>
                {AUTHOR_LABEL[a]}
                <span className="count">{ps.length} 節</span>
              </h3>
              <div className="stance-bars">
                {BAR_FEATURES.map((f) => (
                  <div key={f} className="bar-row" title={`${FEATURE_LABEL[f]}: ${mean(ps, f).toFixed(4)}`}>
                    <span className="bar-label">{FEATURE_LABEL[f]}</span>
                    <span className="bar-track">
                      <span
                        className="bar-fill"
                        style={{
                          width: `${(mean(ps, f) / barMax[f]) * 100}%`,
                          background: AUTHOR_COLOR[a],
                        }}
                      />
                    </span>
                  </div>
                ))}
              </div>
              {ps.map((p) => (
                <blockquote key={p.passage_id} className="quote">
                  <p>{p.quote}</p>
                  <footer>
                    {p.work} — {p.source_note}
                  </footer>
                </blockquote>
              ))}
            </article>
          );
        })}
      </div>
    </section>
  );
}
