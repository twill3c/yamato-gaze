"""青空文庫テキスト版のパーサ(F-01, F-02)。

二層原則(AGENTS §1)の実装:
- 表示層 = 原文逐語。ヘッダ/本文/フッタは入力の逐語スライスであり、
  reconstruct() で入力全文を完全復元できる(T-012)
- 分析層 = 段落 base(ルビ記法・注記除去後の親文字列)への文字単位 NFKC。
  文字単位で適用するため合成済み濁点等の複数文字合成は扱わない(近似規則)。
  a2d が分析層各文字 → 段落 raw の文字範囲を与える(T-013)

実体照合・スタンスに依存しない純パーサに保つ(詩案・捕物帳案へ持ち回る共通資産)。
標準ライブラリのみ使用(N-01 の範囲内)。
"""

from __future__ import annotations

import argparse
import json
import re
import time
import unicodedata
import urllib.request
import zipfile
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path


class AozoraError(ValueError):
    pass


class AozoraFooterError(AozoraError):
    """底本フッタが見つからない・構造化できない(T-014)。"""


# ---------------------------------------------------------------- データ構造


@dataclass
class Ruby:
    start: int  # base 上の親文字範囲
    end: int
    reading: str


@dataclass
class Note:
    pos: int  # base 上の挿入位置(段落注記)/ raw_body オフセット(ブロック注記)
    raw: str  # ［＃...］の原文
    kind: str  # heading | gaiji | emphasis | indent | other


@dataclass
class Paragraph:
    raw: str  # 表示層(原文逐語、改行なし 1 行)
    span: tuple[int, int]  # raw_body 内の範囲
    base: str  # 親文字のみ(ルビ記法・｜・注記を除去)
    ruby: list[Ruby]
    notes: list[Note]
    kind: str = "normal"  # normal | heading
    heading_level: str | None = None  # 大 | 中 | 小
    analysis: str = ""  # 文字単位 NFKC(base)
    a2d: list[tuple[int, int]] = field(default_factory=list)  # 分析層 i → raw 範囲


@dataclass
class AozoraDoc:
    title: str
    author: str
    header_raw: str
    raw_body: str
    footer_raw: str
    source_note: dict
    paragraphs: list[Paragraph]
    block_notes: list[Note]  # 注記のみの行(字下げ指示等)

    def reconstruct(self) -> str:
        """入力全文の逐語復元(T-012 の保証)。"""
        return self.header_raw + self.raw_body + self.footer_raw


# ---------------------------------------------------------------- 注記の種別

_RE_NOTE = re.compile(r"［＃[^］]*］")
_RE_HEADING = re.compile(r"「(?P<t>.+?)」は(?P<lv>大|中|小)見出し")

# CJK 統合漢字+繰返し記号など: ｜なしルビの親文字列の判定に使う
_KANJI = re.compile(r"[々〆一-鿿豈-﫿㐀-䶿々〆ヶ]")


def _note_kind(note_raw: str, prev_char: str) -> str:
    inner = note_raw[2:-1]  # ［＃ と ］ を除く
    if _RE_HEADING.search(inner):
        return "heading"
    if "傍点" in inner or "傍線" in inner:
        return "emphasis"
    if "字下げ" in inner:
        return "indent"
    if prev_char == "※" or "水準" in inner or "U+" in inner or "＋" in inner:
        return "gaiji"
    return "other"


# ---------------------------------------------------------------- 段落パース


def _parse_paragraph(raw: str, span: tuple[int, int]) -> Paragraph:
    base_chars: list[str] = []
    b2r: list[tuple[int, int]] = []  # base i → raw 範囲
    ruby: list[Ruby] = []
    notes: list[Note] = []
    kind = "normal"
    heading_level: str | None = None

    pending_ruby_start: int | None = None  # ｜ で予約された親文字開始(base 位置)
    i = 0
    n = len(raw)
    while i < n:
        c = raw[i]
        if c == "｜":
            pending_ruby_start = len(base_chars)
            i += 1
            continue
        if c == "《":
            j = raw.find("》", i + 1)
            if j < 0:
                raise AozoraError(f"閉じられていないルビ記法: {raw[i:i+20]!r}")
            reading = raw[i + 1 : j]
            end = len(base_chars)
            if pending_ruby_start is not None:
                start = pending_ruby_start
                pending_ruby_start = None
            else:
                # ｜なし: 直前の漢字連続を親文字列とする(近似規則)
                start = end
                while start > 0 and _KANJI.match(base_chars[start - 1]):
                    start -= 1
            ruby.append(Ruby(start=start, end=end, reading=reading))
            i = j + 1
            continue
        if raw.startswith("［＃", i):
            m = _RE_NOTE.match(raw, i)
            if not m:
                raise AozoraError(f"閉じられていない注記: {raw[i:i+20]!r}")
            note_raw = m.group(0)
            prev = base_chars[-1] if base_chars else ""
            k = _note_kind(note_raw, prev)
            notes.append(Note(pos=len(base_chars), raw=note_raw, kind=k))
            if k == "heading":
                hm = _RE_HEADING.search(note_raw)
                assert hm is not None
                kind = "heading"
                heading_level = hm.group("lv")
            i = m.end()
            continue
        base_chars.append(c)
        b2r.append((i, i + 1))
        i += 1

    base = "".join(base_chars)

    # 分析層: 文字単位 NFKC。a2d は b2r を経由して raw 範囲へ
    analysis_chars: list[str] = []
    a2d: list[tuple[int, int]] = []
    for bi, bc in enumerate(base):
        for nc in unicodedata.normalize("NFKC", bc):
            analysis_chars.append(nc)
            a2d.append(b2r[bi])

    return Paragraph(
        raw=raw,
        span=span,
        base=base,
        ruby=ruby,
        notes=notes,
        kind=kind,
        heading_level=heading_level,
        analysis="".join(analysis_chars),
        a2d=a2d,
    )


# ---------------------------------------------------------------- フッタ


_RE_TEIHON = re.compile(r"^底本：「(?P<name>[^」]+)」(?P<rest>.*)$", re.M)


def _parse_footer(footer_raw: str) -> dict:
    m = _RE_TEIHON.search(footer_raw)
    if not m:
        raise AozoraFooterError("底本行(底本：「…」)が構造化できません")
    rest = m.group("rest").strip()
    series = publisher = None
    if rest:
        parts = [p.strip() for p in rest.split("、") if p.strip()]
        if len(parts) >= 2:
            series, publisher = "、".join(parts[:-1]), parts[-1]
        elif parts:
            publisher = parts[0]

    def _find(label: str) -> str | None:
        fm = re.search(rf"^{label}：(.+)$", footer_raw, re.M)
        return fm.group(1).strip() if fm else None

    parent = re.search(r"^底本の親本：「(?P<name>[^」]+)」(?P<rest>.*)$", footer_raw, re.M)
    return {
        "raw": footer_raw,
        "底本名": m.group("name"),
        "底本レーベル": series,
        "底本出版社": publisher,
        "親本": parent.group("name") if parent else None,
        "入力者": _find("入力"),
        "校正者": _find("校正"),
    }


# ---------------------------------------------------------------- 全体パース


_RE_DASH_LINE = re.compile(r"^-{10,}\s*$", re.M)


def parse(text: str) -> AozoraDoc:
    # 1. フッタ境界: 行頭「底本：」から末尾まで
    fm = re.search(r"^底本：", text, re.M)
    if not fm:
        raise AozoraFooterError("底本フッタが見つかりません(T-014)")
    footer_raw = text[fm.start() :]
    head_and_body = text[: fm.start()]

    # 2. ヘッダ境界: 凡例ブロック(-----)があれば閉じ線まで、なければ 2 行
    dashes = list(_RE_DASH_LINE.finditer(head_and_body))
    lines = head_and_body.splitlines(keepends=True)
    if len(lines) < 2:
        raise AozoraError("ヘッダ(表題・著者)が不足しています")
    if len(dashes) >= 2:
        header_end = dashes[1].end()
        # 閉じ線直後の改行までをヘッダに含める
        nl = head_and_body.find("\n", header_end)
        header_end = nl + 1 if nl >= 0 else len(head_and_body)
    else:
        header_end = len(lines[0]) + len(lines[1])
    header_raw = head_and_body[:header_end]
    raw_body = head_and_body[header_end:]

    title = lines[0].rstrip("\r\n")
    author = lines[1].rstrip("\r\n")

    # 3. 本文: 1 行 = 1 段落(青空文庫の散文規則)。注記のみの行はブロック注記
    paragraphs: list[Paragraph] = []
    block_notes: list[Note] = []
    offset = 0
    for line in raw_body.splitlines(keepends=True):
        content = line.rstrip("\r\n")
        stripped = content.strip()
        if stripped:
            only_notes = _RE_NOTE.sub("", stripped).strip() == ""
            if only_notes:
                for nm in _RE_NOTE.finditer(content):
                    block_notes.append(
                        Note(
                            pos=offset + nm.start(),
                            raw=nm.group(0),
                            kind=_note_kind(nm.group(0), ""),
                        )
                    )
            else:
                span = (offset, offset + len(content))
                paragraphs.append(_parse_paragraph(content, span))
        offset += len(line)

    return AozoraDoc(
        title=title,
        author=author,
        header_raw=header_raw,
        raw_body=raw_body,
        footer_raw=footer_raw,
        source_note=_parse_footer(footer_raw),
        paragraphs=paragraphs,
        block_notes=block_notes,
    )


# ---------------------------------------------------------------- 取得(bronze)


UA = "yamato-gaze/0.1 (Aozora Bunko corpus fetch; contact: https://github.com/twill3c)"
BRONZE_DIR = Path("data/bronze")
CORPUS_CONFIG = Path("config/corpus.json")


def _http_get(url: str, retries: int = 3, wait: float = 2.0) -> bytes:
    last: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read()
        except Exception as e:  # ネットワーク層のみ広めに捕捉
            last = e
            time.sleep(wait * (attempt + 1))
    raise AozoraError(f"取得失敗({retries} 回): {url}: {last}")


def fetch_bronze(work_ids: list[str] | None = None) -> list[Path]:
    """corpus.json に従い zip を取得・展開して data/bronze/ に保存する。

    N-02: 本関数の実行は手動(make bronze)に限る。テストから呼んではならない。
    """
    config = json.loads(CORPUS_CONFIG.read_text(encoding="utf-8"))
    BRONZE_DIR.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    for work in config["works"]:
        if work_ids and work["id"] not in work_ids:
            continue
        dest = BRONZE_DIR / f"{work['id']}.txt"
        data = _http_get(work["zip_url"])
        with zipfile.ZipFile(BytesIO(data)) as zf:
            txt_names = [n for n in zf.namelist() if n.lower().endswith(".txt")]
            if len(txt_names) != 1:
                raise AozoraError(f"{work['id']}: zip 内の txt が一意でない: {txt_names}")
            dest.write_bytes(zf.read(txt_names[0]))
        saved.append(dest)
        print(f"bronze: {work['id']} ← {work['zip_url']} → {dest}")
        time.sleep(1.0)  # 連続アクセスの抑制
    return saved


def load_bronze(work_id: str) -> str:
    """bronze の txt(cp932)を復号して返す。"""
    return (BRONZE_DIR / f"{work_id}.txt").read_bytes().decode("cp932")


def main() -> int:
    ap = argparse.ArgumentParser(description="青空文庫パーサ/取得 CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_fetch = sub.add_parser("fetch", help="corpus.json の作品を data/bronze/ へ取得(手動限定)")
    p_fetch.add_argument("--only", nargs="*", help="取得する work id(省略時は全件)")
    p_parse = sub.add_parser("parse", help="bronze の作品をパースして要約を表示")
    p_parse.add_argument("work_id")
    args = ap.parse_args()
    if args.cmd == "fetch":
        fetch_bronze(args.only)
        return 0
    doc = parse(load_bronze(args.work_id))
    print(f"{doc.title} / {doc.author}")
    print(f"段落数: {len(doc.paragraphs)} (見出し {sum(1 for p in doc.paragraphs if p.kind == 'heading')})")
    print(f"底本: {doc.source_note['底本名']} / 入力: {doc.source_note['入力者']} / 校正: {doc.source_note['校正者']}")
    print(f"逐語復元: {'OK' if doc.reconstruct() == load_bronze(args.work_id) else 'NG'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
