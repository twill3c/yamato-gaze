"use client";

// 地図 + 三面鏡(F-08)。データは静的バンドル(単一 JSON 群、N-05)
import Link from "next/link";
import { useEffect, useState } from "react";

import Attribution from "@/components/Attribution";
import MapView from "@/components/MapView";
import MirrorPanel from "@/components/MirrorPanel";
import type { SiteMeta } from "@/lib/loadings";
import { AUTHORS_COUNT_COLOR, type Passage, type SiteFeature } from "@/lib/types";

export default function Page() {
  const [features, setFeatures] = useState<SiteFeature[]>([]);
  const [passages, setPassages] = useState<Passage[]>([]);
  const [meta, setMeta] = useState<SiteMeta | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [dataError, setDataError] = useState<string | null>(null);

  useEffect(() => {
    const e = new URLSearchParams(window.location.search).get("e");
    if (e) setSelectedId(e);
    // データ読込失敗を黙って空地図にしない(端末依存問題の診断可能性)
    const fail = (name: string) => (err: unknown) => {
      setDataError(`${name} の読み込みに失敗しました(${String(err)})。再読み込みをお試しください`);
    };
    fetch("data/sites.geojson")
      .then((r) => (r.ok ? r.json() : Promise.reject(`HTTP ${r.status}`)))
      .then((fc) => setFeatures(fc.features as SiteFeature[]))
      .catch(fail("sites.geojson"));
    fetch("data/passages.json")
      .then((r) => (r.ok ? r.json() : Promise.reject(`HTTP ${r.status}`)))
      .then((ps) => setPassages(ps as Passage[]))
      .catch(fail("passages.json"));
    fetch("data/meta.json")
      .then((r) => r.json())
      .then(setMeta)
      .catch(() => setMeta(null));
  }, []);

  const selected = features.find((f) => f.properties.entity_id === selectedId) ?? null;

  return (
    <div className="app">
      <header className="header">
        <h1>
          大和路の三面鏡
          <span className="count">{features.length} 実体 / {passages.length} 節</span>
          <Link className="nav-link" href="scatter/">
            散布図 →
          </Link>
        </h1>
        <div className="legend">
          <span className="group-label">記述した著者数:</span>
          {AUTHORS_COUNT_COLOR.map((c, i) => (
            <span key={c} className="legend-item">
              <span className="swatch" style={{ background: c }} />
              {i + 1} 名
            </span>
          ))}
          <span className="group-label">ピンの大きさ = 節の数</span>
        </div>
      </header>
      <main className="main">
        {dataError && (
          <div className="data-error" role="alert">
            {dataError}
          </div>
        )}
        <MapView
          features={features}
          selectedId={selectedId}
          onSelect={(id) => setSelectedId(id)}
        />
        {selected && (
          <MirrorPanel
            site={selected.properties}
            passages={passages}
            onClose={() => setSelectedId(null)}
          />
        )}
      </main>
      <Attribution meta={meta} />
    </div>
  );
}
