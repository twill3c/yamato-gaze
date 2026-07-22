# T-01x — extract/aozora.py(青空文庫パーサ)のフィクスチャ駆動テスト
import unicodedata
from pathlib import Path

import pytest

from extract.aozora import AozoraFooterError, parse

FIXTURES = Path(__file__).parent.parent / "data" / "fixtures"


@pytest.fixture(scope="module")
def synthetic_text() -> str:
    return (FIXTURES / "synthetic.txt").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def doc(synthetic_text):
    return parse(synthetic_text)


# ---------------------------------------------------------------- T-011
@pytest.mark.unit
class TestT011Structure:
    def test_header(self, doc):
        assert doc.title == "合成試験文"
        assert doc.author == "試験 太郎"

    def test_paragraph_count_and_kinds(self, doc):
        kinds = [p.kind for p in doc.paragraphs]
        # 見出し1 + 本文2 + 字下げ内1 + 最終1(注記のみの行は段落にしない)
        assert kinds == ["heading", "normal", "normal", "normal", "normal"]

    def test_heading(self, doc):
        h = doc.paragraphs[0]
        assert h.kind == "heading"
        assert h.heading_level == "中"
        assert h.base == "一　斑鳩の空"

    def test_notes_removed_from_base_and_recorded(self, doc):
        p2 = doc.paragraphs[2]
        assert "［＃" not in p2.base
        kinds = sorted(n.kind for n in p2.notes)
        assert kinds == ["emphasis", "gaiji"]

    def test_ruby_separated(self, doc):
        p1 = doc.paragraphs[1]
        assert p1.base == "　大和の斑鳩に法隆寺はある。二上山が遠くに見える。"
        readings = [(p1.base[r.start : r.end], r.reading) for r in p1.ruby]
        assert readings == [
            ("大和", "やまと"),
            ("斑鳩", "いかるが"),
            ("二上山", "ふたかみやま"),
        ]

    def test_indent_block_notes_recorded(self, doc):
        # ［＃ここから2字下げ］等は段落 base から除去され、doc レベルで種別記録される
        assert any(n.kind == "indent" for n in doc.block_notes)
        assert all("字下げ" not in p.base for p in doc.paragraphs)


# ---------------------------------------------------------------- T-012
@pytest.mark.unit
class TestT012Verbatim:
    def test_reconstruct_full_text(self, synthetic_text, doc):
        assert doc.reconstruct() == synthetic_text

    def test_paragraph_raw_is_verbatim_slice(self, synthetic_text, doc):
        for p in doc.paragraphs:
            s, e = p.span
            assert doc.raw_body[s:e] == p.raw
            assert p.raw in synthetic_text


# ---------------------------------------------------------------- T-013
@pytest.mark.unit
class TestT013OffsetMap:
    def test_analysis_layer_normalized(self, doc):
        p_last = doc.paragraphs[-1]
        assert "！" not in p_last.analysis  # NFKC 済み
        assert "!" in p_last.analysis
        assert "ABC" in p_last.analysis

    def test_every_analysis_char_maps_to_raw_range(self, doc):
        for p in doc.paragraphs:
            assert len(p.a2d) == len(p.analysis)
            for s, e in p.a2d:
                assert 0 <= s < e <= len(p.raw)

    def test_offset_across_ruby(self, doc):
        # ルビ跨ぎ: 「大和の斑鳩に」の「の」は raw 上でルビ記法《やまと》の後にある
        p1 = doc.paragraphs[1]
        i = p1.analysis.index("の")
        s, e = p1.a2d[i]
        assert p1.raw[s:e] == "の"
        assert "《やまと》" in p1.raw[: s]

    def test_map_monotonic(self, doc):
        for p in doc.paragraphs:
            starts = [s for s, _ in p.a2d]
            assert starts == sorted(starts)


# ---------------------------------------------------------------- T-014
@pytest.mark.unit
class TestT014Footer:
    def test_source_note_structured(self, doc):
        sn = doc.source_note
        assert sn["底本名"] == "合成試験文集"
        assert sn["底本出版社"] == "試験書房"
        assert sn["入力者"] == "入力花子"
        assert sn["校正者"] == "校正次郎"
        assert sn["raw"].startswith("底本：")

    def test_missing_footer_is_explicit_error(self, synthetic_text):
        body_only = synthetic_text.split("底本：")[0]
        with pytest.raises(AozoraFooterError):
            parse(body_only)


# ---------------------------------------------------------------- T-015
@pytest.mark.unit
class TestT015Gaiji:
    def test_gaiji_note_preserved(self, doc):
        p2 = doc.paragraphs[2]
        gaiji = [n for n in p2.notes if n.kind == "gaiji"]
        assert len(gaiji) == 1
        assert "木＋温のつくり" in gaiji[0].raw
        # ※ プレースホルダは base に残る
        assert p2.base.count("※") == 1
        assert p2.base[gaiji[0].pos - 1] == "※"

    def test_analysis_char_count_consistent(self, doc):
        # 分析層は base と文字単位 NFKC で対応し、対応表の長さが一致する
        for p in doc.paragraphs:
            recomposed = "".join(
                unicodedata.normalize("NFKC", c) for c in p.base
            )
            assert p.analysis == recomposed
