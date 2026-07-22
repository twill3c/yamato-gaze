# T-05x — gold/export.py・gold/validate.py(Gold 契約と品質検査)
import pytest

from gold.export import build_counts, build_sites
from gold.validate import (
    check_contract,
    check_coverage,
    check_quotes,
    check_triangulation,
)


def make_passage(pid="p1", eid="e1", author="watsuji", quote="　法隆寺へ。", **over):
    rec = {
        "passage_id": pid,
        "entity_id": eid,
        "author": author,
        "work": "watsuji_kojijunrei",
        "quote": quote,
        "source_note": "底本:「古寺巡礼」岩波文庫、岩波書店 / 入力:門田裕志 / 校正:仙酔ゑびす",
        "char_start": 0,
        "char_end": len(quote),
        "features": {"comparative": 0.0},
        "lexicon_version": "comparative:1.0|religious:1.0|sensory:1.0",
        "xy": [0.1, -0.2],
    }
    rec.update(over)
    return rec


ENTITIES_ROWS = [
    {"entity_id": "e1", "type": "temple", "name": "法隆寺", "parent": "",
     "lat": "34.6142", "lon": "135.7346", "verified": "desk", "notes": ""},
    {"entity_id": "e2", "type": "temple", "name": "中宮寺", "parent": "",
     "lat": "", "lon": "", "verified": "false", "notes": ""},
    {"entity_id": "e3", "type": "statue", "name": "百済観音", "parent": "e1",
     "lat": "", "lon": "", "verified": "false", "notes": ""},
]


# ---------------------------------------------------------------- T-053
@pytest.mark.validation
class TestT053VerifiedExclusion:
    def test_unverified_excluded_and_counted(self):
        counts = {"e1": {"passage_count": 2, "authors_count": 1, "by_author": {"watsuji": 2}},
                  "e2": {"passage_count": 1, "authors_count": 1, "by_author": {"kamei": 1}},
                  "e3": {"passage_count": 1, "authors_count": 1, "by_author": {"hori": 1}}}
        fc, excluded = build_sites(ENTITIES_ROWS, counts)
        ids = [f["properties"]["entity_id"] for f in fc["features"]]
        assert "e1" in ids
        assert "e2" not in ids  # verified=false → 除外
        assert "e2" in excluded

    def test_statue_inherits_parent_coords(self):
        counts = {"e1": {"passage_count": 1, "authors_count": 1, "by_author": {"watsuji": 1}},
                  "e3": {"passage_count": 1, "authors_count": 1, "by_author": {"watsuji": 1}}}
        fc, excluded = build_sites(ENTITIES_ROWS, counts)
        st = next(f for f in fc["features"] if f["properties"]["entity_id"] == "e3")
        assert st["geometry"]["coordinates"] == [135.7346, 34.6142]
        assert st["properties"]["verified"] == "desk"
        assert st["properties"]["parent"] == "e1"

    def test_entity_without_passages_not_exported(self):
        fc, _ = build_sites(ENTITIES_ROWS, {})
        assert fc["features"] == []


# ---------------------------------------------------------------- T-051
@pytest.mark.validation
class TestT051QuoteVerbatim:
    RAW = "　法隆寺へ。\r\n　次の段落。\r\n"

    def test_verbatim_pass(self):
        p = make_passage(quote="　法隆寺へ。", char_start=0, char_end=6)
        assert check_quotes([p], {"watsuji_kojijunrei": self.RAW}) == []

    def test_single_char_difference_fails(self):
        p = make_passage(quote="　法隆寺ヘ。", char_start=0, char_end=6)  # へ→ヘ
        errs = check_quotes([p], {"watsuji_kojijunrei": self.RAW})
        assert len(errs) == 1

    def test_multi_paragraph_quote(self):
        q = "　法隆寺へ。\n　次の段落。"
        # RAW は CRLF。char_end は raw オフセット: 6(段落1)+2(\r\n)+6(段落2)=14
        assert self.RAW[8:14] == "　次の段落。"  # 前提検算(HC-004 規範)
        p = make_passage(quote=q, char_start=0, char_end=14)
        assert check_quotes([p], {"watsuji_kojijunrei": self.RAW}) == []


# ---------------------------------------------------------------- T-052
@pytest.mark.validation
class TestT052Coverage:
    def counts(self, multi, all3):
        c = {}
        for i in range(all3):
            c[f"a{i}"] = {"authors_count": 3, "passage_count": 1, "by_author": {}}
        for i in range(multi - all3):
            c[f"b{i}"] = {"authors_count": 2, "passage_count": 1, "by_author": {}}
        return c

    def test_boundary_pass(self):
        assert check_coverage(self.counts(12, 5), 12, 5) == []

    def test_below_multi_fails(self):
        assert check_coverage(self.counts(11, 5), 12, 5)

    def test_below_all3_fails(self):
        assert check_coverage(self.counts(12, 4), 12, 5)


# ---------------------------------------------------------------- T-054
@pytest.mark.validation
class TestT054Triangulation:
    def test_consistent(self):
        passages = [make_passage(pid="p1", eid="e1"), make_passage(pid="p2", eid="e1", author="kamei", work="kamei_yamatokoji")]
        counts = build_counts(passages)
        fc, _ = build_sites(ENTITIES_ROWS, counts)
        assert check_triangulation(fc, passages, counts) == []

    def test_tampered_counts_fail(self):
        passages = [make_passage(pid="p1", eid="e1")]
        counts = build_counts(passages)
        counts["e1"]["passage_count"] = 99
        fc, _ = build_sites(ENTITIES_ROWS, counts)
        assert check_triangulation(fc, passages, counts)


# ---------------------------------------------------------------- T-055
@pytest.mark.validation
class TestT055Contract:
    def test_valid_record_passes(self):
        counts = build_counts([make_passage()])
        fc, _ = build_sites(ENTITIES_ROWS, counts)
        assert check_contract([make_passage()], fc) == []

    def test_bad_author_enum_fails(self):
        assert check_contract([make_passage(author="basho")], {"type": "FeatureCollection", "features": []})

    def test_missing_source_note_fails(self):
        assert check_contract([make_passage(source_note="")], {"type": "FeatureCollection", "features": []})

    def test_missing_xy_fails(self):
        p = make_passage()
        del p["xy"]
        assert check_contract([p], {"type": "FeatureCollection", "features": []})

    def test_missing_lexicon_version_fails(self):  # Q-04 との接続(T-033 の gold 側)
        assert check_contract([make_passage(lexicon_version="")], {"type": "FeatureCollection", "features": []})
