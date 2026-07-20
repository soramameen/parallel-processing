---
name: publish-artifacts
description: このプロジェクトの GitHub Pages に artifacts/ 配下の HTML を公開・更新する。push で自動デプロイされ、完成版 bron-kerbosch.html が index.html になる。Use when user says 「公開して」「publish」「pagesに上げて」「デプロイして」「artifacts 公開」, or after editing artifacts/ HTML and wanting it live.
allowed-tools: bash read edit
---

# Publish Artifacts (GitHub Pages)

このプロジェクトの GitHub Pages 運用。公開URL: https://soramameen.github.io/parallel-processing/

## 構成（既に設定済み・変更不要）

- **公開ルート**: `artifacts/` 配下のすべてのファイルがそのまま公開される
- **index.html**: workflow が `artifacts/bron-kerbosch.html` を `_site/index.html` にコピー。ルートURL（`/`）で完成版が表示される
- **デプロイ方式**: GitHub Actions (`.github/workflows/deploy-pages.yml`)。`main` への push で `artifacts/**` に差分があれば自動実行
- **Pages 設定**: `build_type=workflow`（リポジトリ Settings → Pages → Source: GitHub Actions）

## 通常の公開フロー（HTML を更新・追加したいとき）

1. **変更内容を確認** — 何を公開・更新するか把握する:
   ```bash
   git status
   ls artifacts/
   ```

2. **commit & push** — `artifacts/` の変更を main に反映する。コミットメッセージは内容に合わせる:
   ```bash
   git add artifacts/ .github/workflows/deploy-pages.yml
   git commit -m "publish: <内容>"
   git push origin main
   ```

3. **workflow の実行を監視** — 失敗したらログを見て原因対応:
   ```bash
   sleep 10
   RUN_ID=$(gh run list --workflow=deploy-pages.yml --limit 1 --json databaseId --jq '.[0].databaseId')
   gh run watch "$RUN_ID" --exit-status
   ```
   失敗時の定番原因:
   - `cp: cannot stat 'artifacts/.'` → 公開対象HTMLが **git にコミットされていない**。`git status` で untracked/modified を確認し add して再push。
   - workflow 自体が古い → `.github/workflows/deploy-pages.yml` を確認。

4. **公開を検証** — HTTP 200 と title を確認:
   ```bash
   curl -sI "https://soramameen.github.io/parallel-processing/" | head -3
   curl -s "https://soramameen.github.io/parallel-processing/" | grep -oE '<title>[^<]*</title>'
   ```

5. **報告** — 公開URLと確認結果をユーザーに伝える。

## 公開するファイルを増やしたいとき

- 新しいHTMLを `artifacts/<name>.html` に置いて push すれば `https://soramameen.github.io/parallel-processing/<name>.html` で公開される。
- 別のファイルを index.html（ルート表示）にしたい場合は `.github/workflows/deploy-pages.yml` の `index.html` コピー行を編集する。

## 初回セットアップ（workflow が無い・新規リポジトリの場合のみ）

既存プロジェクトでは本節は不要。Pages 未有効化・workflow がない場合の手順:

1. `.github/workflows/deploy-pages.yml` を作成（既存プロジェクトなら既にある）。
2. HTML を git にコミットして push。
3. Pages を有効化:
   ```bash
   gh api -X POST repos/soramameen/parallel-processing/pages -F build_type=workflow
   ```
4. 上記「通常の公開フロー」の 3〜5 に従いデプロイ・検証。
