# T-03x — transform/align.py(整列 F-04)・transform/stance.py(特徴量 F-05・感度分析 F-12)
from pathlib import Path

import pytest

from extract.aozora import parse
from transform.align import build_passages
from transform.entities import load_entities, tag_paragraphs
from transform.stance import (
    LexiconVersionError,
    compute_features,
    load_lexicons,
    sensitivity_report,
)

FIXTURES = Path(__file__).parent.parent / "data" / "fixtures"

SYN_TEXT = (
    "整列試験文\n"
    "試験 太郎\n"
    "\n"
    "　中宮寺の門をくぐる。\n"
    "　御寺の庭は静かだ。\n"
    "　空を見上げて歩いた。\n"
    "　中宮寺の弥勒は微笑む。\n"
    "　法隆寺に向かう。\n"
    "\n"
    "底本：「整列試験文集」試験文庫、試験書房\n"
    "入力：入力花子\n"
    "校正：校正次郎\n"
)


@pytest.fixture(scope="module")
def entities():
    return load_entities(FIXTURES / "entities_test.csv")


@pytest.fixture(scope="module")
def doc():
    return parse(SYN_TEXT)


@pytest.fixture(scope="module")
def passages(doc, entities):
    tags = tag_paragraphs([p.base for p in doc.paragraphs], entities).tags
    return build_passages("synwork", doc, tags)


# ---------------------------------------------------------------- T-031
@pytest.mark.unit
class TestT031Merge:
    def by_entity(self, passages, eid):
        return [p for p in passages if p.entity_id == eid]

    def test_consecutive_merged(self, passages):
        # 段落 0(中宮寺)・1(御寺)は連続 → 1 passage、段落 3 は別 passage
        ps = self.by_entity(passages, "test-001")
        spans = sorted((p.para_start, p.para_end) for p in ps)
        assert spans == [(0, 1), (3, 3)]

    def test_multi_entity_paragraph_in_both(self, passages):
        # 段落 3 は中宮寺+弥勒(ctx 有効)の両実体の passage に属する
        assert any(p.entity_id == "test-002" and p.para_start == 3 for p in passages)

    def test_nonconsecutive_not_merged(self, passages):
        ps = self.by_entity(passages, "test-001")
        assert len(ps) == 2

    def test_quote_is_verbatim(self, passages, doc):
        for p in passages:
            assert p.quote == "\n".join(
                doc.paragraphs[i].raw for i in range(p.para_start, p.para_end + 1)
            )
            assert doc.raw_body[p.char_start : p.char_end].replace("\r", "") \
                .startswith(p.quote.split("\n")[0])

    def test_passage_id_unique(self, passages):
        ids_ = [p.passage_id for p in passages]
        assert len(ids_) == len(set(ids_))

    def test_blank_line_breaks_merge(self, entities):
        # 空行を挟む同一実体の連続段落は index が連続でも併合しない(Q-03 の逐語性)
        text = (
            "併合試験\n著者 名\n\n"
            "　中宮寺に着く。\n"
            "\n"
            "　中宮寺の庭。\n"
            "\n底本：「試」試文庫、試書房\n入力：A\n校正：B\n"
        )
        doc2 = parse(text)
        tags = tag_paragraphs([p.base for p in doc2.paragraphs], entities).tags
        ps = [p for p in build_passages("w", doc2, tags) if p.entity_id == "test-001"]
        assert len(ps) == 2
        # quote は raw_body スライスと逐語一致する
        for p in ps:
            sliced = doc2.raw_body[p.char_start : p.char_end].replace("\r\n", "\n")
            assert sliced == p.quote


# ---------------------------------------------------------------- T-032
@pytest.mark.unit
class TestT032HandComputed:
    TEXT = (
        "この柱はギリシアの神殿に似ている。"
        "堂内はひんやりとして、線香の匂いがする。"
        "私は御仏に祈りを捧げた。"
    )

    @pytest.fixture(scope="class")
    def feats(self):
        lex = load_lexicons(FIXTURES / "lexicons_v1")
        return compute_features(self.TEXT, lex)

    def test_sentence_count(self, feats):
        assert feats.counts["n_sentences"] == 3

    def test_comparative(self, feats):
        # ギリシア 1 + に似 1 = 2 ヒット / 3 文
        assert feats.counts["comparative_hits"] == 2
        assert feats.values["comparative"] == pytest.approx(2 / 3)

    def test_religious(self, feats):
        # 祈り 1 + 御仏 1 = 2 ヒット
        assert feats.counts["religious_hits"] == 2
        assert feats.values["religious"] == pytest.approx(
            2 / feats.counts["n_morphemes"]
        )

    def test_sensory(self, feats):
        # ひんやり 1 + 匂い 1 = 2 ヒット
        assert feats.counts["sensory_hits"] == 2

    def test_comma_density(self, feats):
        # 読点は 1 個(「ひんやりとして、」)
        assert feats.counts["n_commas"] == 1
        assert feats.values["comma_density"] == pytest.approx(
            1 / feats.counts["n_chars"]
        )

    def test_sent_len(self, feats):
        assert feats.values["sent_len"] == pytest.approx(
            feats.counts["n_chars"] / 3
        )


# ---------------------------------------------------------------- T-033
@pytest.mark.unit
class TestT033LexiconVersion:
    def test_version_stamp(self):
        lex = load_lexicons(FIXTURES / "lexicons_v1")
        feats = compute_features("御仏に祈る。", lex)
        assert feats.lexicon_version == "comparative:9.1|religious:9.1|sensory:9.1"

    def test_version_header_missing_is_error(self, tmp_path):
        d = tmp_path / "lex"
        d.mkdir()
        for name in ("comparative", "religious", "sensory"):
            (d / f"{name}.csv").write_text("term,kind,note\nx,noun,\n", encoding="utf-8")
        with pytest.raises(LexiconVersionError):
            load_lexicons(d)


# ---------------------------------------------------------------- T-034
@pytest.mark.unit
class TestT034MorphRates:
    @pytest.fixture(scope="class")
    def lex(self):
        return load_lexicons(FIXTURES / "lexicons_v1")

    def test_first_person_counted(self, lex):
        feats = compute_features("私は塔を見た。僕らは歩いた。", lex)
        assert feats.counts["first_person_hits"] == 2  # 私・僕

    def test_no_first_person(self, lex):
        feats = compute_features("塔が立っている。", lex)
        assert feats.counts["first_person_hits"] == 0

    def test_past_sentences(self, lex):
        feats = compute_features("私は塔を見た。庭を歩いた。", lex)
        assert feats.values["present_tense"] == pytest.approx(0.0)

    def test_present_sentences(self, lex):
        feats = compute_features("塔が立っている。屋根が美しい。", lex)
        assert feats.values["present_tense"] == pytest.approx(1.0)

    def test_mixed_tense(self, lex):
        feats = compute_features("塔が立っている。庭を歩いた。", lex)
        assert feats.values["present_tense"] == pytest.approx(0.5)


# ---------------------------------------------------------------- T-035
@pytest.mark.unit
class TestT035Sensitivity:
    def test_only_changed_paragraph_shifts(self, tmp_path):
        lex_old = load_lexicons(FIXTURES / "lexicons_v1")
        lex_new = load_lexicons(FIXTURES / "lexicons_v2")  # religious に「微笑」追加
        texts = {
            "p1": "御仏の微笑が浮かぶ。",  # 変更語を含む → religious が変位
            "p2": "塔が立っている。",  # 変更語なし → 変位ゼロ
        }
        report = sensitivity_report(texts, lex_old, lex_new)
        assert report["p1"]["religious"] != 0.0
        assert all(abs(v) < 1e-12 for v in report["p2"].values())
        assert report["p1"]["comparative"] == pytest.approx(0.0)
