# デプロイ手順(loop_008 / F-10)

**本番 URL(2026-07-23 稼働確認)**: https://yamato-gaze.vercel.app
(地図+三面鏡: `/` / 散布図: `/scatter/`)

## 構成

- Next.js 静的エクスポート(web/next.config.mjs: `output: "export"`)。サーバ・環境変数不要
- データは web/public/data/ の 3 JSON に静的バンドル(初期ロード後の追加取得ゼロ, N-05)
- データ更新時は `python -m gold.export` → `python -m gold.validate` → コミット → push で再デプロイ

## Vercel セットアップ(初回のみ・人間工程)

1. https://vercel.com/ に GitHub アカウント(twill3c)で連携
2. Add New → Project → `twill3c/yamato-gaze` を Import
3. **Root Directory を `web` に設定**(それ以外は自動検出のままで可:
   Framework = Next.js / Build = `next build` / Output = 自動)
4. Deploy → 発行された URL を確認

## デプロイ後の確認(docs/p5_checklist.md の N-05 項目)

- [ ] 本番 URL で地図・三面鏡・散布図が動く
- [ ] スマホ実機: 初期ロード後に機内モード → 三面鏡・散布図が閲覧可能(地図タイルは除く)
- [ ] 帰属表示(青空文庫・地理院)が見える

## 公開範囲

- GitHub リポジトリは private で開始(SETUP §3)。public 化はライセンス配置
  (LICENSE / LICENSE-DATA.md — 配置済み)の確認後に人間が判断
- Vercel の URL 公開自体はリポジトリ公開と独立に可能
