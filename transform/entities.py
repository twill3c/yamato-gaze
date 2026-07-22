"""実体タグ付け(F-03)。

規律(AGENTS §2 / GUIDE §3):
- 辞書は data/curated/entities.csv のみ。本モジュールは辞書に追記しない
- 文脈規則: notes の `ctx=語1|語2` に列挙された別名は、親実体(parent)の正式名が
  同一段落または直前 CONTEXT_WINDOW 段落に出現する場合のみ有効
- ctx 別名の親候補が複数(同名別名を持つ実体が複数文脈で有効)なら、タグ付けせず
  needs_review へ保留する(捏造禁止 — 迷ったら保留)
- 辞書外の「寺名らしき語」(〜寺/〜院)は needs_review へ出力し、タグは付けない

マッチは表示層(base)への最長一致。長い表層形が消費した範囲は短い表層形に使わない
(「薬師寺」の中の「薬師」を誤タグしない)。
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path

CONTEXT_WINDOW = 3  # ctx 別名の親寺参照が有効な「直前 N 段落」
CURATED_ENTITIES = Path("data/curated/entities.csv")

_RE_CTX = re.compile(r"ctx=([^\s—]+)")
_RE_TEMPLE_LIKE = re.compile(r"[一-鿿々]{1,6}[寺院]")


@dataclass
class Entity:
    entity_id: str
    type: str
    name: str
    aliases: list[str]
    parent: str | None
    ctx_aliases: set[str]
    notes: str


@dataclass
class Tag:
    entity_id: str
    surface: str
    start: int
    end: int


@dataclass
class Review:
    para_index: int
    surface: str
    reason: str  # unknown_temple | ambiguous_ctx
    snippet: str


@dataclass
class TagResult:
    tags: list[list[Tag]]
    needs_review: list[Review]


def load_entities(path: str | Path) -> list[Entity]:
    entities: list[Entity] = []
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            notes = (row.get("notes") or "").strip()
            m = _RE_CTX.search(notes)
            ctx = set(m.group(1).split("|")) if m else set()
            aliases = [a for a in (row.get("aliases") or "").split("|") if a]
            entities.append(
                Entity(
                    entity_id=row["entity_id"],
                    type=row["type"],
                    name=row["name"],
                    aliases=aliases,
                    parent=(row.get("parent") or "").strip() or None,
                    ctx_aliases=ctx,
                    notes=notes,
                )
            )
    return entities


def _display_name(name: str) -> str:
    """「聖観音(薬師寺)」のような表示名から括弧部を除いた照合不可能判定用の名。"""
    return re.sub(r"[（(].*?[）)]", "", name)


@dataclass
class _Surface:
    text: str
    entity: Entity
    is_ctx: bool


def _build_surfaces(entities: list[Entity]) -> list[_Surface]:
    surfaces: list[_Surface] = []
    for e in entities:
        name = _display_name(e.name)
        if name:
            surfaces.append(_Surface(name, e, name in e.ctx_aliases))
        for a in e.aliases:
            surfaces.append(_Surface(a, e, a in e.ctx_aliases))
    # 最長一致を優先するため長い順に整列
    surfaces.sort(key=lambda s: -len(s.text))
    return surfaces


def _snippet(text: str, start: int, end: int, margin: int = 15) -> str:
    return text[max(0, start - margin) : min(len(text), end + margin)]


def tag_paragraphs(
    paragraphs: list[str],
    entities: list[Entity],
    window: int = CONTEXT_WINDOW,
) -> TagResult:
    by_id = {e.entity_id: e for e in entities}
    surfaces = _build_surfaces(entities)
    # 同一表層形を持つ実体候補をまとめ、表層形は長い順に照合(最長一致)
    by_text: dict[str, list[_Surface]] = {}
    for s in surfaces:
        by_text.setdefault(s.text, []).append(s)
    texts_longest_first = sorted(by_text, key=len, reverse=True)

    all_tags: list[list[Tag]] = []
    reviews: list[Review] = []

    for i, para in enumerate(paragraphs):
        context_text = "".join(paragraphs[max(0, i - window) : i + 1])
        consumed: list[tuple[int, int]] = []
        para_tags: list[Tag] = []

        for txt in texts_longest_first:
            for m in re.finditer(re.escape(txt), para):
                st, en = m.start(), m.end()
                if any(a < en and st < b for a, b in consumed):
                    continue  # より長い表層形が消費済み
                consumed.append((st, en))
                valid_ids: set[str] = set()
                for s in by_text[txt]:
                    if not s.is_ctx:
                        valid_ids.add(s.entity.entity_id)
                        continue
                    parent = by_id.get(s.entity.parent or "")
                    if parent and _display_name(parent.name) in context_text:
                        valid_ids.add(s.entity.entity_id)
                if len(valid_ids) == 1:
                    para_tags.append(Tag(valid_ids.pop(), txt, st, en))
                elif len(valid_ids) > 1:
                    # 複数実体が同時に成立 → 保留(捏造禁止)
                    reviews.append(
                        Review(i, txt, "ambiguous_ctx", _snippet(para, st, en))
                    )
                # valid 0 件(文脈なしの ctx 別名)はタグも保留も出さない

        # 辞書外の寺名らしき語
        for m in _RE_TEMPLE_LIKE.finditer(para):
            if m.group(0) in by_text:
                continue
            if any(a < m.end() and m.start() < b for a, b in consumed):
                continue
            reviews.append(
                Review(i, m.group(0), "unknown_temple", _snippet(para, m.start(), m.end()))
            )

        all_tags.append(para_tags)

    return TagResult(tags=all_tags, needs_review=reviews)


def main() -> int:
    """実三作へのタグ付け実行。needs_review を out/needs_entity_review.csv へ出力。"""
    import argparse
    from collections import Counter

    from extract.aozora import load_bronze, parse

    ap = argparse.ArgumentParser(description="実体タグ付け(F-03)ランナー")
    ap.add_argument("--works", nargs="*", default=["watsuji_kojijunrei", "kamei_yamatokoji", "hori_yamatoji"])
    ap.add_argument("--out", default="out/needs_entity_review.csv")
    args = ap.parse_args()

    entities = load_entities(CURATED_ENTITIES)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rows: list[list[str]] = []
    for wid in args.works:
        doc = parse(load_bronze(wid))
        bases = [p.base for p in doc.paragraphs]
        result = tag_paragraphs(bases, entities)
        n_tagged = sum(1 for tags in result.tags if tags)
        counts = Counter(t.entity_id for tags in result.tags for t in tags)
        print(f"── {wid}: 段落 {len(bases)}, タグ付き段落 {n_tagged}, 保留 {len(result.needs_review)}")
        for eid, c in counts.most_common(10):
            print(f"   {eid}: {c}")
        for v in result.needs_review:
            rows.append([wid, str(v.para_index), v.surface, v.reason, v.snippet])
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        import csv as _csv

        w = _csv.writer(f)
        w.writerow(["work_id", "para_index", "surface", "reason", "snippet"])
        w.writerows(rows)
    print(f"needs_review: {len(rows)} 行 → {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
