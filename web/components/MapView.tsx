"use client";

// 地図(F-08): MapLibre + 地理院淡色タイル。ピンの大きさ = passage_count、
// 色 = authors_count(明度単調ランプ)。白リング+選択強調+ツールチップ(title)
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { useEffect, useRef } from "react";

import { sitesBbox, type Bbox } from "@/lib/bbox";
import { spiderfyOffsets } from "@/lib/spiderfy";
import { AUTHORS_COUNT_COLOR, type SiteFeature } from "@/lib/types";

const GSI_PALE_STYLE: maplibregl.StyleSpecification = {
  version: 8,
  sources: {
    gsi_pale: {
      type: "raster",
      tiles: ["https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png"],
      tileSize: 256,
      attribution:
        '<a href="https://maps.gsi.go.jp/development/ichiran.html" target="_blank">国土地理院</a>',
    },
  },
  layers: [{ id: "gsi_pale", type: "raster", source: "gsi_pale" }],
};

// データ到着前のフォールバック(実際の初期表示はピン bbox への fitBounds)
const INITIAL_CENTER: [number, number] = [135.76, 34.63];
const INITIAL_ZOOM = 11.5;
const FIT_OPTIONS = { padding: 60, maxZoom: 13, duration: 0 } as const;

function pinSize(passageCount: number): number {
  return Math.min(30, 10 + Math.sqrt(passageCount) * 3.2);
}

export default function MapView({
  features,
  selectedId,
  onSelect,
}: {
  features: SiteFeature[];
  selectedId: string | null;
  onSelect: (entityId: string) => void;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const markersRef = useRef<maplibregl.Marker[]>([]);
  const fittedRef = useRef(false); // 初回のみ fitBounds(以後のユーザ操作を上書きしない)
  const bboxRef = useRef<Bbox | null>(null);

  // コンテナ 0 サイズ時に fitBounds が no-op する環境(レイアウト確定が遅い
  // Chrome/Windows 等)があるため、成功が確認できるまで再試行する
  const tryFit = () => {
    const map = mapRef.current;
    const el = containerRef.current;
    const bbox = bboxRef.current;
    if (fittedRef.current || !map || !el || !bbox) return;
    if (el.clientWidth < 50 || el.clientHeight < 50) return; // レイアウト未確定
    map.resize();
    if (!map.cameraForBounds(bbox, FIT_OPTIONS)) return; // カメラ計算不能なら次の機会に
    map.fitBounds(bbox, FIT_OPTIONS);
    fittedRef.current = true;
  };
  const tryFitRef = useRef(tryFit);
  tryFitRef.current = tryFit;

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    mapRef.current = new maplibregl.Map({
      container: containerRef.current,
      style: GSI_PALE_STYLE,
      center: INITIAL_CENTER,
      zoom: INITIAL_ZOOM,
      attributionControl: { compact: false },
    });
    mapRef.current.addControl(new maplibregl.NavigationControl({ showCompass: false }));
    // コンテナが後からサイズ確定する環境(フレックス計算・dvh 非対応等)での
    // 0 サイズ初期化対策: サイズ変化のたびに再計測し、未フィットなら fit を再試行
    const ro = new ResizeObserver(() => {
      mapRef.current?.resize();
      tryFitRef.current();
    });
    ro.observe(containerRef.current);
    mapRef.current.once("load", () => tryFitRef.current());
    return () => {
      ro.disconnect();
      mapRef.current?.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    // 初期表示: 全ピンの bbox にフィット。成功するまで(データ到着・load・
    // resize の各契機で)再試行し、成功後はユーザ操作を上書きしない
    if (features.length > 0) {
      bboxRef.current = sitesBbox(features);
      tryFitRef.current();
    }
    markersRef.current.forEach((m) => m.remove());
    // 同座標(寺+所蔵仏像)は花弁状のピクセルオフセットで散らす(座標データは不変)
    const offsets = spiderfyOffsets(
      features.map((f) => ({
        entity_id: f.properties.entity_id,
        lat: f.properties.lat,
        lon: f.properties.lon,
        type: f.properties.type,
        size: pinSize(f.properties.passage_count),
      })),
    );
    markersRef.current = features.map((f) => {
      const pr = f.properties;
      const el = document.createElement("button");
      el.className = "marker";
      const size = pinSize(pr.passage_count);
      el.style.width = `${size}px`;
      el.style.height = `${size}px`;
      el.style.background = AUTHORS_COUNT_COLOR[Math.min(pr.authors_count, 3) - 1];
      el.dataset.selected = String(pr.entity_id === selectedId);
      el.setAttribute("aria-label", pr.name);
      el.title = `${pr.name} — ${pr.authors_count} 名 / ${pr.passage_count} 節`;
      el.addEventListener("click", (e) => {
        e.stopPropagation();
        onSelect(pr.entity_id);
      });
      return new maplibregl.Marker({
        element: el,
        offset: offsets.get(pr.entity_id) ?? [0, 0],
      })
        .setLngLat(f.geometry.coordinates)
        .addTo(map);
    });
  }, [features, selectedId, onSelect]);

  return <div ref={containerRef} className="map" />;
}
