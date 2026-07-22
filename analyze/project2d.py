"""2 次元射影(F-09 用の xy 算出)。PCA の自前実装 — 標準ライブラリのみ(N-01)。

- 対称行列の固有分解は Jacobi 回転法(特徴量は 7 次元程度なので十分)
- 標準化(z-score)は既定で有効: 特徴量のスケール差(sent_len ≫ 率系)を吸収する
- 符号規約: 各主成分ベクトルは最大絶対値成分が正になるよう符号を固定(決定論)
"""

from __future__ import annotations

import math
from dataclasses import dataclass


def jacobi_eigh(
    matrix: list[list[float]], tol: float = 1e-12, max_sweeps: int = 100
) -> tuple[list[float], list[list[float]]]:
    """対称行列の固有値・固有ベクトル(固有値降順)。vecs[i] が i 番目の固有ベクトル。"""
    n = len(matrix)
    a = [row[:] for row in matrix]
    v = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]

    for _ in range(max_sweeps):
        off = math.sqrt(sum(a[i][j] ** 2 for i in range(n) for j in range(n) if i != j))
        if off < tol:
            break
        for p in range(n - 1):
            for q in range(p + 1, n):
                if abs(a[p][q]) < tol / (n * n):
                    continue
                theta = (a[q][q] - a[p][p]) / (2.0 * a[p][q])
                t = math.copysign(1.0, theta) / (abs(theta) + math.sqrt(theta * theta + 1.0))
                c = 1.0 / math.sqrt(t * t + 1.0)
                s = t * c
                for k in range(n):
                    akp, akq = a[k][p], a[k][q]
                    a[k][p] = c * akp - s * akq
                    a[k][q] = s * akp + c * akq
                for k in range(n):
                    apk, aqk = a[p][k], a[q][k]
                    a[p][k] = c * apk - s * aqk
                    a[q][k] = s * apk + c * aqk
                for k in range(n):
                    vkp, vkq = v[k][p], v[k][q]
                    v[k][p] = c * vkp - s * vkq
                    v[k][q] = s * vkp + c * vkq

    pairs = sorted(
        ((a[i][i], [v[k][i] for k in range(n)]) for i in range(n)),
        key=lambda kv: -kv[0],
    )
    vals = [p[0] for p in pairs]
    vecs = []
    for _, vec in pairs:
        m = max(vec, key=abs)
        if m < 0:
            vec = [-x for x in vec]
        vecs.append(vec)
    return vals, vecs


@dataclass
class PCAResult:
    mean: list[float]
    scale: list[float]  # 標準化に使った標準偏差(standardize=False なら全 1)
    components: list[list[float]]  # [pc1, pc2]
    explained: list[float]  # 寄与率 [pc1, pc2]
    xy: list[tuple[float, float]]


def pca_2d(rows: list[list[float]], standardize: bool = True) -> PCAResult:
    n = len(rows)
    if n < 2:
        raise ValueError("PCA には 2 点以上が必要です")
    d = len(rows[0])
    mean = [sum(r[k] for r in rows) / n for k in range(d)]
    if standardize:
        scale = [
            math.sqrt(sum((r[k] - mean[k]) ** 2 for r in rows) / (n - 1)) or 1.0
            for k in range(d)
        ]
    else:
        scale = [1.0] * d
    z = [[(r[k] - mean[k]) / scale[k] for k in range(d)] for r in rows]

    cov = [
        [sum(z[i][p] * z[i][q] for i in range(n)) / (n - 1) for q in range(d)]
        for p in range(d)
    ]
    vals, vecs = jacobi_eigh(cov)
    total = sum(v for v in vals if v > 0) or 1.0
    components = vecs[:2]
    explained = [max(vals[0], 0.0) / total, max(vals[1] if d > 1 else 0.0, 0.0) / total]
    xy = [
        (
            sum(z[i][k] * components[0][k] for k in range(d)),
            sum(z[i][k] * components[1][k] for k in range(d)) if d > 1 else 0.0,
        )
        for i in range(n)
    ]
    return PCAResult(mean=mean, scale=scale, components=components, explained=explained, xy=xy)


FEATURE_KEYS = [
    "comparative", "religious", "sensory", "first_person",
    "present_tense", "sent_len", "comma_density",
]


def main() -> int:
    """out/silver_passages.json に xy を付与して out/silver_passages_xy.json へ。"""
    import json
    from pathlib import Path

    silver = json.loads(Path("out/silver_passages.json").read_text(encoding="utf-8"))
    rows = [[r["features"][k] for k in FEATURE_KEYS] for r in silver["passages"]]
    result = pca_2d(rows, standardize=True)
    for rec, (x, y) in zip(silver["passages"], result.xy):
        rec["xy"] = [round(x, 4), round(y, 4)]
    silver["pca"] = {
        "feature_order": FEATURE_KEYS,
        "components": [[round(c, 4) for c in comp] for comp in result.components],
        "explained": [round(e, 4) for e in result.explained],
        "standardize": True,
    }
    out = Path("out/silver_passages_xy.json")
    out.write_text(json.dumps(silver, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"passages: {len(rows)} / 寄与率 PC1 {result.explained[0]:.3f} PC2 {result.explained[1]:.3f}")
    print("PC1 loadings:", {k: round(result.components[0][i], 3) for i, k in enumerate(FEATURE_KEYS)})
    print("PC2 loadings:", {k: round(result.components[1][i], 3) for i, k in enumerate(FEATURE_KEYS)})
    print(f"→ {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
