# SETUP.md — 開発開始手順(VS Code + Claude Code / Windows)

前提: C:\_ClaudeCode\harness-kit が構築済み(tsukiji-atlas と共通基盤)。
未構築の場合は tsukiji-atlas の SETUP.md 手順 1〜3 を先に実施
(HC テンプレートのコピー元は loop-observability\templates\ — 修正済みパスに注意)。

## 1. プロジェクト初期化

```powershell
cd C:\_ClaudeCode
Expand-Archive $env:USERPROFILE\Downloads\yamato-gaze-scaffold.zip -DestinationPath .
cd yamato-gaze
git init -b main
python ..\harness-kit\scaffold-kit\scripts\scaffoldctl.py init --registry ..\harness-kit\scaffold-kit\registry
git add -A; git commit -m "chore: scaffold — yamato-gaze 初期化"
```

init 後の確認: AGENTS.md 末尾に managed block、harness\ に looplog.py / wtctl.py。
`.wt\gate.json` は本プロジェクト同梱版が優先(「既に存在」表示は正常)。

## 2. 依存パッケージ(本プロジェクトは標準ライブラリ+2件)

```powershell
pip install pytest "fugashi[unidic-lite]"
```

fugashi + unidic-lite は形態素解析(スタンス特徴量の品詞判定)に必須。
ゼロ依存原則からの逸脱は SPEC N-01 に理由を明記済み。
確認: `python -c "import fugashi; print(fugashi.Tagger()('大和路を歩く'))"`

## 3. fleet への登録と GitHub

```powershell
Add-Content C:\_ClaudeCode\harness-kit\fleet.txt "C:\_ClaudeCode\yamato-gaze"
# GitHub に twill3c/yamato-gaze を作成して push(private で開始、公開判断は P5)
```

## 4. VS Code で開く

```powershell
code C:\_ClaudeCode\yamato-gaze
```

worktree 並走時は `code C:\_ClaudeCode\yamato-gaze.worktrees\loop_xxx` で別ウィンドウ。

## 5. 最初のループ(Claude Code に貼るプロンプト)

```
このリポジトリの CLAUDE.md を読み、7 段階プロトコルに従って
IMPLEMENTATION_GUIDE.md の P1(loop_001)を開始してください。
loop_001 はコーパス探査です。3 作品+著者ベースライン候補の
青空文庫収録状況(特に亀井勝一郎)・底本・仮名遣いを確認し、
結果によって SPEC の該当箇所を確定させます。実装はまだ行いません。
```

## 6. Vercel(P5 で使用)

GitHub 連携 → yamato-gaze を Import。Next.js 静的エクスポート、環境変数不要。
公開(public 化+LICENSE 配置)は P5 の手順に従う。奈良行きの日程が P5 の締切。
