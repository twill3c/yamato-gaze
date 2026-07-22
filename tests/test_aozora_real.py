# T-012/T-014/T-015 — 実三作の冒頭部フィクスチャによる結合テスト(N-02: ネットワーク不要)
from pathlib import Path

import pytest

from extract.aozora import parse

FIXTURES = Path(__file__).parent.parent / "data" / "fixtures"

REAL_HEADS = {
    "watsuji_kojijunrei_head.txt": {
        "title": "古寺巡礼",
        "author": "和辻哲郎",
        "底本名": "古寺巡礼",
        "底本出版社": "岩波書店",
        "入力者": "門田裕志",
        "校正者": "仙酔ゑびす",
    },
    "kamei_yamatokoji_head.txt": {
        "title": "大和古寺風物誌",
        "author": "亀井勝一郎",
        "底本名": "大和古寺風物誌",
        "底本出版社": "新潮社",
        "入力者": "酒井和郎",
        "校正者": "阿部哲也",
    },
    "hori_yamatoji_head.txt": {
        "title": "大和路・信濃路",
        "author": "堀辰雄",
        "底本名": "昭和文学全集　第6巻",
        "底本出版社": "小学館",
        "入力者": "kompass",
        "校正者": "松永正敏",
    },
}


@pytest.mark.integration
@pytest.mark.parametrize("fname", sorted(REAL_HEADS))
class TestRealHeads:
    def test_verbatim_reconstruction(self, fname):  # T-012
        text = (FIXTURES / fname).read_text(encoding="utf-8", newline="")
        assert parse(text).reconstruct() == text

    def test_source_note(self, fname):  # T-014
        text = (FIXTURES / fname).read_text(encoding="utf-8", newline="")
        doc = parse(text)
        exp = REAL_HEADS[fname]
        assert doc.title == exp["title"]
        assert doc.author == exp["author"]
        for key in ("底本名", "底本出版社", "入力者", "校正者"):
            assert doc.source_note[key] == exp[key]

    def test_offset_maps_valid(self, fname):  # T-013/T-015
        text = (FIXTURES / fname).read_text(encoding="utf-8", newline="")
        doc = parse(text)
        assert doc.paragraphs
        for p in doc.paragraphs:
            assert len(p.a2d) == len(p.analysis)
            for s, e in p.a2d:
                assert 0 <= s < e <= len(p.raw)
