"""整列(F-04): entity_id ごとに著者別の段落束を作り、連続段落を 1 passage に併合する。

併合規則(GUIDE §3、loop_007 で精緻化): 同一実体タグが連続する段落範囲を 1 passage
とする。ただし**物理的に単一改行で隣接する場合のみ**併合する(空行・注記のみの行が
介在する場合は別 passage)。これにより quote = raw_body スライスの逐語性(Q-03)が
構成的に保証される。複数実体を持つ段落は、各実体の passage に重複して属してよい。

quote は表示層(Paragraph.raw)の逐語連結であり、正規化を一切加えない(AGENTS §1, Q-03)。
"""

from __future__ import annotations

from dataclasses import dataclass

from extract.aozora import AozoraDoc
from transform.entities import Tag


@dataclass
class Passage:
    passage_id: str
    work_id: str
    entity_id: str
    para_start: int  # 段落 index(両端含む)
    para_end: int
    quote: str  # 表示層逐語(段落 raw を \n 連結)
    char_start: int  # raw_body 内オフセット
    char_end: int
    analysis: str  # 分析層連結(特徴量算出用)


def build_passages(
    work_id: str, doc: AozoraDoc, tags: list[list[Tag]]
) -> list[Passage]:
    entity_paras: dict[str, list[int]] = {}
    for i, para_tags in enumerate(tags):
        for t in para_tags:
            entity_paras.setdefault(t.entity_id, [])
            if not entity_paras[t.entity_id] or entity_paras[t.entity_id][-1] != i:
                entity_paras[t.entity_id].append(i)

    def physically_adjacent(a: int, b: int) -> bool:
        """段落 a の直後に段落 b が単一改行のみを挟んで続くか(空行・注記行なし)。"""
        gap = doc.raw_body[doc.paragraphs[a].span[1] : doc.paragraphs[b].span[0]]
        return gap in ("\n", "\r\n")

    passages: list[Passage] = []
    for eid, indices in sorted(entity_paras.items()):
        run_start = prev = indices[0]
        runs: list[tuple[int, int]] = []
        for i in indices[1:]:
            if i == prev + 1 and physically_adjacent(prev, i):
                prev = i
                continue
            runs.append((run_start, prev))
            run_start = prev = i
        runs.append((run_start, prev))

        for s, e in runs:
            paras = doc.paragraphs[s : e + 1]
            passages.append(
                Passage(
                    passage_id=f"{work_id}-{eid}-p{s:04d}",
                    work_id=work_id,
                    entity_id=eid,
                    para_start=s,
                    para_end=e,
                    quote="\n".join(p.raw for p in paras),
                    char_start=paras[0].span[0],
                    char_end=paras[-1].span[1],
                    analysis="\n".join(p.analysis for p in paras),
                )
            )
    return passages


def coverage(passages: list[Passage], work_authors: dict[str, str]) -> dict:
    """Q-02 検査用: 実体ごとの著者数・passage 数を集計する。"""
    by_entity: dict[str, dict] = {}
    for p in passages:
        d = by_entity.setdefault(p.entity_id, {"authors": set(), "passages": 0})
        d["authors"].add(work_authors.get(p.work_id, p.work_id))
        d["passages"] += 1
    return {
        eid: {"authors_count": len(d["authors"]), "passage_count": d["passages"]}
        for eid, d in by_entity.items()
    }
