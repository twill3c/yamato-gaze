"""スタンス特徴量(F-05)+感度分析(F-12)。

算出規則(docs/stance.md に規範を明記):
- 文分割: 分析層を 。！？ で分割(空文除外)
- comparative(比較参照密度)= 比較標識ヒット数 / 文数(kind=pattern は正規表現)
- religious / sensory = 辞書ヒット数(表層部分一致)/ 形態素数(補助記号・空白除く)
- first_person = 一人称代名詞トークン数 / 形態素数(UniDic 代名詞かつ語彙素が一人称リスト)
- present_tense = 非過去文数 / 文数。近似規則: 文末 3 トークン内に助動詞「た」
  (語彙素 た)があれば過去文、なければ非過去文
- sent_len = 文字数 / 文数、comma_density = 読点「、」数 / 文字数
- 全レコードに lexicon_version(comparative:X|religious:X|sensory:X)を刻む(Q-04)

注意: religious/sensory の分子は表層部分一致・分母は形態素数という混合単位の近似
(v1 規則)。辞書は data/curated/lexicons/(版管理・変更時は感度分析必須, AGENTS §3)。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import fugashi

FIRST_PERSON_LEMMAS = {
    "私-代名詞", "私", "わたくし", "わたし", "僕", "俺", "我-代名詞", "我", "われ", "吾",
}

_TAGGER: fugashi.Tagger | None = None


def _tagger() -> fugashi.Tagger:
    global _TAGGER
    if _TAGGER is None:
        _TAGGER = fugashi.Tagger()
    return _TAGGER


class LexiconVersionError(ValueError):
    """レキシコン先頭行に version ヘッダが無い(Q-04 違反)。"""


@dataclass
class Lexicon:
    name: str
    version: str
    terms: list[tuple[str, str]]  # (term, kind)


LEXICON_NAMES = ("comparative", "religious", "sensory")
CURATED_LEXICONS = Path("data/curated/lexicons")


def load_lexicons(dir_path: str | Path) -> dict[str, Lexicon]:
    lexicons: dict[str, Lexicon] = {}
    for name in LEXICON_NAMES:
        path = Path(dir_path) / f"{name}.csv"
        lines = path.read_text(encoding="utf-8").splitlines()
        if not lines or not lines[0].startswith("# version:"):
            raise LexiconVersionError(f"{path}: 先頭行に `# version:` ヘッダがありません")
        version = lines[0].split(":", 1)[1].strip()
        terms: list[tuple[str, str]] = []
        for line in lines[2:]:  # 2 行目はカラムヘッダ
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            if parts[0]:
                terms.append((parts[0], parts[1] if len(parts) > 1 else ""))
        lexicons[name] = Lexicon(name=name, version=version, terms=terms)
    return lexicons


def lexicon_version_stamp(lexicons: dict[str, Lexicon]) -> str:
    return "|".join(f"{n}:{lexicons[n].version}" for n in LEXICON_NAMES)


@dataclass
class Features:
    values: dict[str, float]
    counts: dict[str, int]
    lexicon_version: str


_RE_SENT_SPLIT = re.compile(r"(?<=[。！？])")


def _sentences(text: str) -> list[str]:
    return [s for s in (x.strip() for x in _RE_SENT_SPLIT.split(text)) if s]


def _count_hits(text: str, lexicon: Lexicon) -> int:
    hits = 0
    for term, kind in lexicon.terms:
        if kind == "pattern":
            hits += len(re.findall(term, text))
        else:
            hits += text.count(term)
    return hits


def compute_features(text: str, lexicons: dict[str, Lexicon]) -> Features:
    sentences = _sentences(text)
    n_sent = len(sentences)
    chars = re.sub(r"\s", "", text)
    n_chars = len(chars)
    n_commas = text.count("、")

    words = [w for w in _tagger()(text) if w.feature.pos1 not in ("補助記号", "空白")]
    n_morph = len(words)
    fp_hits = sum(
        1
        for w in words
        if w.feature.pos1 == "代名詞"
        and (w.feature.lemma in FIRST_PERSON_LEMMAS or w.surface in FIRST_PERSON_LEMMAS)
    )

    past_sents = 0
    for s in sentences:
        tail = [w for w in _tagger()(s) if w.feature.pos1 not in ("補助記号", "空白")][-3:]
        if any(w.feature.pos1 == "助動詞" and (w.feature.lemma or "") == "た" for w in tail):
            past_sents += 1

    comp_hits = _count_hits(text, lexicons["comparative"])
    rel_hits = _count_hits(text, lexicons["religious"])
    sen_hits = _count_hits(text, lexicons["sensory"])

    def _div(a: float, b: float) -> float:
        return a / b if b else 0.0

    values = {
        "comparative": _div(comp_hits, n_sent),
        "religious": _div(rel_hits, n_morph),
        "sensory": _div(sen_hits, n_morph),
        "first_person": _div(fp_hits, n_morph),
        "present_tense": _div(n_sent - past_sents, n_sent),
        "sent_len": _div(n_chars, n_sent),
        "comma_density": _div(n_commas, n_chars),
    }
    counts = {
        "n_sentences": n_sent,
        "n_morphemes": n_morph,
        "n_chars": n_chars,
        "n_commas": n_commas,
        "comparative_hits": comp_hits,
        "religious_hits": rel_hits,
        "sensory_hits": sen_hits,
        "first_person_hits": fp_hits,
        "past_sentences": past_sents,
    }
    return Features(
        values=values, counts=counts, lexicon_version=lexicon_version_stamp(lexicons)
    )


def sensitivity_report(
    texts: dict[str, str],
    lexicons_old: dict[str, Lexicon],
    lexicons_new: dict[str, Lexicon],
) -> dict[str, dict[str, float]]:
    """感度分析(F-12): 新旧レキシコンでの特徴量の変位(new - old)をテキスト別に返す。"""
    report: dict[str, dict[str, float]] = {}
    for key, text in texts.items():
        old = compute_features(text, lexicons_old).values
        new = compute_features(text, lexicons_new).values
        report[key] = {k: new[k] - old[k] for k in old}
    return report


# ---------------------------------------------------------------- ランナー

WORK_AUTHORS = {
    "watsuji_kojijunrei": "watsuji",
    "kamei_yamatokoji": "kamei",
    "hori_yamatoji": "hori",
}


def build_silver(works: list[str] | None = None) -> dict:
    """3 作の整列+特徴量を算出し、silver 構造(dict)を返す。"""
    from extract.aozora import load_bronze, parse
    from transform.align import build_passages, coverage
    from transform.entities import CURATED_ENTITIES, load_entities, tag_paragraphs

    lexicons = load_lexicons(CURATED_LEXICONS)
    entities = load_entities(CURATED_ENTITIES)
    all_passages = []
    records = []
    for wid in works or list(WORK_AUTHORS):
        doc = parse(load_bronze(wid))
        tags = tag_paragraphs([p.base for p in doc.paragraphs], entities).tags
        passages = build_passages(wid, doc, tags)
        all_passages.extend(passages)
        for p in passages:
            f = compute_features(p.analysis, lexicons)
            records.append(
                {
                    "passage_id": p.passage_id,
                    "entity_id": p.entity_id,
                    "author": WORK_AUTHORS.get(p.work_id, p.work_id),
                    "work": p.work_id,
                    "quote": p.quote,
                    "source_note": doc.source_note["raw"].splitlines()[0],
                    "char_start": p.char_start,
                    "char_end": p.char_end,
                    "features": f.values,
                    "lexicon_version": f.lexicon_version,
                }
            )
    cov = coverage(all_passages, WORK_AUTHORS)
    return {"passages": records, "coverage": cov}


def main() -> int:
    import argparse
    import json

    ap = argparse.ArgumentParser(description="整列+特徴量ランナー(silver 生成)")
    ap.add_argument("--out", default="out/silver_passages.json")
    args = ap.parse_args()
    silver = build_silver()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(silver, ensure_ascii=False, indent=1), encoding="utf-8")

    cov = silver["coverage"]
    multi = sum(1 for v in cov.values() if v["authors_count"] >= 2)
    all3 = sum(1 for v in cov.values() if v["authors_count"] >= 3)
    print(f"passages: {len(silver['passages'])} / 実体: {len(cov)}")
    print(f"Q-02: 2名以上 {multi}(基準12) / 3名揃い {all3}(基準5)")
    for eid, v in sorted(cov.items(), key=lambda kv: -kv[1]["authors_count"]):
        print(f"  {eid}: authors={v['authors_count']} passages={v['passage_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
