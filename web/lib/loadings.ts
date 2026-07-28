// PC 軸ラベルの根拠表示(loop_009): 「内省⇔スケッチ」等は負荷量から人間が付けた
// 解釈であって PCA の出力そのものではない — 負荷量上位を明示して根拠付きの読みにする
export interface PcaMeta {
  feature_order: string[];
  components: number[][];
  explained: number[];
  standardize: boolean;
}

export interface SiteMeta {
  generated_at: string;
  lexicon_version: string;
  n_passages: number;
  pca: PcaMeta;
  license: string;
}

/** 負荷量の絶対値上位 n 件を「ラベル±値」形式で要約する */
export function loadingsSummary(
  component: number[],
  featureOrder: string[],
  labels: Record<string, string>,
  n: number,
): string {
  return component
    .map((v, i) => ({ v, key: featureOrder[i] }))
    .sort((a, b) => Math.abs(b.v) - Math.abs(a.v))
    .slice(0, n)
    .map(({ v, key }) => {
      const sign = v < 0 ? "−" : "+";
      return `${labels[key] ?? key}${sign}${Math.abs(v).toFixed(2)}`;
    })
    .join(" ・");
}
