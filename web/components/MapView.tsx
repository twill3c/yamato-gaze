"use client";

// 地図(F-08): MapLibre + 地理院淡色タイル。ピンの大きさ = passage_count、
// 色 = authors_count(明度単調ランプ)。白リング+選択強調+ツールチップ(title)
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { useEffect, useRef } from "react";

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

// 初期表示: 大和盆地(config/route.json の map_init と同値)
const INITIAL_CENTER: [number, number] = [135.76, 34.63];
const INITIAL_ZOOM = 11.5;

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
    return () => {
      mapRef.current?.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    markersRef.current.forEach((m) => m.remove());
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
      return new maplibregl.Marker({ element: el })
        .setLngLat(f.geometry.coordinates)
        .addTo(map);
    });
  }, [features, selectedId, onSelect]);

  return <div ref={containerRef} className="map" />;
}
