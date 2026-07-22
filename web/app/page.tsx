"use client";

// 地図 + 三面鏡(F-08)。データは静的バンドル(単一 JSON 群、N-05)
import Link from "next/link";
import { useEffect, useState } from "react";

import Attribution from "@/components/Attribution";
import MapView from "@/components/MapView";
import MirrorPanel from "@/components/MirrorPanel";
import { AUTHORS_COUNT_COLOR, type Passage, type SiteFeature } from "@/lib/types";

export default function Page() {
  const [features, setFeatures] = useState<SiteFeature[]>([]);
  const [passages, setPassages] = useState<Passage[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    const e = new URLSearchParams(window.location.search).get("e");
    if (e) setSelectedId(e);
    fetch("data/sites.geojson")
      .then((r) => r.json())
      .then((fc) => setFeatures(fc.features as SiteFeature[]))
      .catch(() => setFeatures([]));
    fetch("data/passages.json")
      .then((r) => r.json())
      .then((ps) => setPassages(ps as Passage[]))
      .catch(() => setPassages([]));
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
      <Attribution />
    </div>
  );
}
