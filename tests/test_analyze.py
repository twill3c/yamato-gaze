# T-04x — analyze/baseline.py(変位ベクトル F-06)・analyze/project2d.py(PCA 自前実装)
import math

import pytest

from analyze.baseline import displacement
from analyze.project2d import jacobi_eigh, pca_2d

FEATS = ["a", "b", "c"]


# ---------------------------------------------------------------- T-041
@pytest.mark.unit
class TestT041Displacement:
    def test_known_centroid_difference(self):
        # 大和側重心 (2, 4, 6)、ベースライン重心 (1, 1, 1) → 変位 (1, 3, 5)
        yamato = [
            {"a": 1.0, "b": 3.0, "c": 5.0},
            {"a": 3.0, "b": 5.0, "c": 7.0},
        ]
        base = [
            {"a": 0.0, "b": 0.0, "c": 0.0},
            {"a": 2.0, "b": 2.0, "c": 2.0},
        ]
        d = displacement(yamato, base)
        assert d["a"] == pytest.approx(1.0)
        assert d["b"] == pytest.approx(3.0)
        assert d["c"] == pytest.approx(5.0)

    def test_zero_displacement(self):
        same = [{"a": 1.0, "b": 2.0, "c": 3.0}]
        d = displacement(same, same)
        assert all(abs(v) < 1e-12 for v in d.values())

    def test_norm_available(self):
        d = displacement([{"a": 3.0, "b": 4.0}], [{"a": 0.0, "b": 0.0}])
        norm = math.sqrt(sum(v * v for v in d.values()))
        assert norm == pytest.approx(5.0)


# ---------------------------------------------------------------- 固有分解(T-042 の基盤)
@pytest.mark.unit
class TestJacobi:
    def test_diagonal_matrix(self):
        vals, vecs = jacobi_eigh([[3.0, 0.0], [0.0, 1.0]])
        assert vals[0] == pytest.approx(3.0)
        assert vals[1] == pytest.approx(1.0)
        assert abs(vecs[0][0]) == pytest.approx(1.0)

    def test_known_symmetric(self):
        # [[2,1],[1,2]] の固有値は 3 と 1、第1固有ベクトルは (1,1)/√2
        vals, vecs = jacobi_eigh([[2.0, 1.0], [1.0, 2.0]])
        assert vals[0] == pytest.approx(3.0)
        assert vals[1] == pytest.approx(1.0)
        v1 = vecs[0]
        assert abs(v1[0]) == pytest.approx(abs(v1[1]))

    def test_reconstruction(self):
        m = [[4.0, 1.0, 0.5], [1.0, 3.0, 0.2], [0.5, 0.2, 2.0]]
        vals, vecs = jacobi_eigh(m)
        # A·v = λ·v
        for lam, v in zip(vals, vecs):
            for i in range(3):
                av = sum(m[i][j] * v[j] for j in range(3))
                assert av == pytest.approx(lam * v[i], abs=1e-8)


# ---------------------------------------------------------------- T-042
@pytest.mark.unit
class TestT042PCA:
    def test_first_component_matches_analytic_direction(self):
        # 既知の 2 次元構造: 主方向 d1=(2,1,0)/√5、副方向 d2=(-1,2,0)/√5(直交)
        d1 = (2 / math.sqrt(5), 1 / math.sqrt(5), 0.0)
        d2 = (-1 / math.sqrt(5), 2 / math.sqrt(5), 0.0)
        # ss は Σs=0 かつ Σt·s=0 を満たす(t と直交 — 前提を下で検算)
        ts = [-2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0]
        ss = [0.2, -0.2, 0.1, -0.1, 0.0, -0.1, 0.1, -0.2, 0.2]
        assert sum(ss) == pytest.approx(0.0)
        assert sum(t * s for t, s in zip(ts, ss)) == pytest.approx(0.0)
        rows = [
            [t * d1[k] + s * d2[k] for k in range(3)]
            for t, s in zip(ts, ss)
        ]
        result = pca_2d(rows, standardize=False)
        pc1 = result.components[0]
        cos = abs(sum(pc1[k] * d1[k] for k in range(3)))
        assert cos == pytest.approx(1.0, abs=1e-6)  # 符号自由

    def test_xy_shape_and_centering(self):
        rows = [[1.0, 2.0], [3.0, 4.0], [5.0, 7.0]]
        result = pca_2d(rows, standardize=False)
        assert len(result.xy) == 3
        mean_x = sum(p[0] for p in result.xy) / 3
        assert mean_x == pytest.approx(0.0, abs=1e-9)

    def test_standardized_smoke(self):
        rows = [
            [0.01, 100.0, 0.5],
            [0.02, 120.0, 0.4],
            [0.03, 90.0, 0.6],
            [0.015, 110.0, 0.55],
        ]
        result = pca_2d(rows, standardize=True)
        assert len(result.xy) == 4
        assert result.explained[0] >= result.explained[1] >= 0.0
        assert sum(result.explained) <= 1.0 + 1e-9

    def test_deterministic_sign_convention(self):
        rows = [[1.0, 0.0], [2.0, 0.1], [3.0, -0.1], [4.0, 0.05]]
        r1 = pca_2d(rows, standardize=False)
        r2 = pca_2d(list(rows), standardize=False)
        assert r1.components == r2.components
        # 符号規約: 各主成分は最大絶対値成分が正
        for comp in r1.components:
            m = max(comp, key=abs)
            assert m > 0
