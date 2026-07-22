/** 静的エクスポート(F-10)。サーバ・環境変数不要で Vercel/任意の静的ホストに置ける。
    データは public/data の単一 JSON 群 — 初期ロード後の追加取得ゼロ(N-05) */
const nextConfig = {
  output: "export",
  images: { unoptimized: true },
};

export default nextConfig;
