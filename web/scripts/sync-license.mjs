// LICENSE-DATA.md(リポジトリ直下が正)を web/public へ同期する(loop_011)。
// prebuild / predev から実行 — 手書き複製による乖離(DRIFT)を防ぐ
import { copyFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const src = join(here, "..", "..", "LICENSE-DATA.md");
const dest = join(here, "..", "public", "LICENSE-DATA.md");
mkdirSync(dirname(dest), { recursive: true });
copyFileSync(src, dest);
console.log(`sync-license: ${src} -> ${dest}`);
