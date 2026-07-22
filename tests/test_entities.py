# T-02x — transform/entities.py(実体タグ付け)のフィクスチャ駆動テスト
from pathlib import Path

import pytest

from transform.entities import load_entities, tag_paragraphs

FIXTURES = Path(__file__).parent.parent / "data" / "fixtures"


@pytest.fixture(scope="module")
def entities():
    return load_entities(FIXTURES / "entities_test.csv")


def ids(result, i):
    return sorted({t.entity_id for t in result.tags[i]})


# ---------------------------------------------------------------- T-021
@pytest.mark.unit
class TestT021NameAndAlias:
    def test_formal_name(self, entities):
        r = tag_paragraphs(["中宮寺の門をくぐる。"], entities)
        assert ids(r, 0) == ["test-001"]

    def test_alias_same_entity(self, entities):
        r = tag_paragraphs(["御寺の門前に立つ。"], entities)
        assert ids(r, 0) == ["test-001"]

    def test_longest_match_priority(self, entities):
        # 「薬師寺」の中の「薬師」を別実体としてタグ付けしない
        r = tag_paragraphs(["薬師寺の塔を見る。"], entities)
        assert ids(r, 0) == ["test-004"]

    def test_surface_and_span_recorded(self, entities):
        r = tag_paragraphs(["中宮寺と法隆寺を巡る。"], entities)
        surfaces = {(t.surface, t.start) for t in r.tags[0]}
        assert ("中宮寺", 0) in surfaces
        assert ("法隆寺", 4) in surfaces


# ---------------------------------------------------------------- T-022
@pytest.mark.unit
class TestT022ContextRule:
    def test_bare_alias_without_context_not_tagged(self, entities):
        r = tag_paragraphs(["観音の微笑が浮かぶ。"], entities)
        assert ids(r, 0) == []

    def test_same_paragraph_context(self, entities):
        r = tag_paragraphs(["中宮寺の観音の微笑が浮かぶ。"], entities)
        assert "test-002" in ids(r, 0)

    def test_preceding_window_context(self, entities):
        paras = [
            "中宮寺に着いた。",
            "門前の道。",
            "堂内は暗い。",
            "観音の微笑が浮かぶ。",  # 3 段落前に親寺 → 有効
        ]
        r = tag_paragraphs(paras, entities)
        assert "test-002" in ids(r, 3)

    def test_outside_window_not_tagged(self, entities):
        paras = [
            "中宮寺に着いた。",
            "門前の道。",
            "堂内は暗い。",
            "夕暮れが迫る。",
            "観音の微笑が浮かぶ。",  # 4 段落前 → 窓外で無効
        ]
        r = tag_paragraphs(paras, entities)
        assert ids(r, 4) == []

    def test_ambiguous_two_parents_goes_to_review(self, entities):
        # 同一段落に二つの親寺 → ctx 別名は保留(捏造禁止)
        r = tag_paragraphs(["中宮寺と薬師寺、堂の弥勒と薬師を思う。"], entities)
        tagged = ids(r, 0)
        assert "test-002" in tagged  # 弥勒の ctx 親は中宮寺のみ → 有効
        assert "test-005" in tagged  # 薬師の ctx 親は薬師寺のみ → 有効
        r2 = tag_paragraphs(["中宮寺のそばの薬師寺。観音を拝む。"], entities)
        # 「観音」は test-002(親=中宮寺)と test-006(親=薬師寺)の共有 ctx 別名。
        # 両親寺が文脈内 → 実体を確定できないので保留し needs_review に出す
        assert "test-002" not in ids(r2, 0)
        assert "test-006" not in ids(r2, 0)
        assert any(v.surface == "観音" and v.reason == "ambiguous_ctx" for v in r2.needs_review)


# ---------------------------------------------------------------- T-023
@pytest.mark.unit
class TestT023UnknownCandidates:
    def test_unknown_temple_like_word_reviewed_not_tagged(self, entities):
        r = tag_paragraphs(["斑鳩の里の吉田寺を訪ねた。"], entities)
        assert ids(r, 0) == []
        assert any(v.surface == "吉田寺" for v in r.needs_review)

    def test_known_names_not_in_review(self, entities):
        r = tag_paragraphs(["法隆寺と中宮寺を巡る。"], entities)
        assert not any(v.surface in ("法隆寺", "中宮寺") for v in r.needs_review)

    def test_review_row_has_position_and_snippet(self, entities):
        r = tag_paragraphs(["朝に吉田寺を訪ねた。"], entities)
        row = next(v for v in r.needs_review if v.surface == "吉田寺")
        assert row.para_index == 0
        assert "吉田寺" in row.snippet
