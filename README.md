# parallel-processing

Linux / WSL2 / macOS のどれでも同じ Python 開発環境を作れるテンプレートです。

- **Nix**: Python 本体やシステム側の依存を再現性を持って提供します
- **uv**: Python パッケージのインストールや仮想環境を高速に管理します
- **direnv**: ディレクトリに入っただけで自動的に環境が有効になります

> 🔗 **公開ページ**: https://soramameen.github.io/parallel-processing/
>
> このリポジトリで作った学習資料（Bron–Kerbosch 法の解説など）は GitHub Pages で公開しています。

---

## 目次

- [0. このREADMEの読み方](#0-このreadmeの読み方)
- [1. 必要なものをインストールする](#1-必要なものをインストールする)
  - [1.1 Nix（パッケージマネージャー）](#11-nixパッケージマネージャー)
  - [1.2 direnv（自動環境有効化）](#12-direnv自動環境有効化)
- [2. このプロジェクトを動かす](#2-このプロジェクトを動かす)
- [3. よく使うコマンド](#3-よく使うコマンド)
- [4. トラブルシューティング](#4-トラブルシューティング)
- [5. ファイルの説明](#5-ファイルの説明)

---

## 0. このREADMEの読み方

ターミナル（コマンドを打つ黒い画面）で以下のコマンドを順番に実行してください。
コマンドは ** `$` の記号以降** を入力します。記号自体は入力しないでください。

```bash
$ echo "Hello"
```

の場合は `echo "Hello"` と入力します。

---

## 1. 必要なものをインストールする

### 1.1 Nix（パッケージマネージャー）

Nix は「どのマシンでも同じ環境を作れる」パッケージマネージャーです。

#### macOS の場合

ターミナルを開いて、以下を1行ずつ実行してください。

```bash
$ curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | \
  sh -s -- install
```

インストーラーの指示に従って進めてください。完了したら、ターミナルを**再起動**するか、以下を実行してください。

```bash
$ . /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh
```

#### WSL2（Windows）の場合

WSL2 のターミナル（Ubuntu など）を開いて、以下を実行してください。

```bash
$ curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | \
  sh -s -- install --no-confirm
```

完了したら、以下を実行するか、ターミナルを再起動してください。

```bash
$ . /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh
```

#### Linux（Ubuntu / Debian など）の場合

ターミナルを開いて、以下を実行してください。

```bash
$ curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | \
  sh -s -- install --no-confirm
```

完了したら、以下を実行するか、一度ログアウトして再ログインしてください。

```bash
$ . /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh
```

#### Nix が入ったか確認

どの OS でも、以下を実行してバージョンが表示されればOKです。

```bash
$ nix --version
nix (Nix) 2.x.x
```

---

### 1.2 direnv（自動環境有効化）

direnv は「特定のフォルダに入ると、自動で環境変数を切り替える」ツールです。
このプロジェクトでは、フォルダに入った瞬間に Nix の環境が有効になるようにしています。

#### macOS（Homebrew を使う場合）

Homebrew が入っていれば以下でインストールできます。

```bash
$ brew install direnv nix-direnv
```

#### WSL2 / Linux（Nix を使う場合）

Nix を使ってインストールします。

```bash
$ nix profile install nixpkgs#direnv
$ nix profile install nixpkgs#nix-direnv
```

#### シェルへの追記

direnv を有効にするために、シェルの設定ファイルに1行追加する必要があります。

使っているシェルを確認するには、以下を実行してください。

```bash
$ echo $SHELL
```

##### Bash を使っている場合

```bash
$ echo 'eval "$(direnv hook bash)"' >> ~/.bashrc
$ source ~/.bashrc
```

##### Zsh を使っている場合（macOS のデフォルトなど）

```bash
$ echo 'eval "$(direnv hook zsh)"' >> ~/.zshrc
$ source ~/.zshrc
```

##### Fish を使っている場合

```bash
$ echo 'direnv hook fish | source' >> ~/.config/fish/config.fish
```

---

## 2. このプロジェクトを動かす

### 2.1 リポジトリをクローンする

まだクローンしていない場合は、以下を実行してください。

```bash
$ git clone https://github.com/soramameen/parallel-processing.git
$ cd parallel-processing
```

すでにクローン済みなら、そのフォルダに移動するだけです。

```bash
$ cd parallel-processing
```

### 2.2 自動で環境を有効化する（direnv）

初回だけ、以下のコマンドを実行して環境の自動有効化を許可します。

```bash
$ direnv allow
```

これでフォルダに入るたびに、自動的に Python 3.12 と uv が使えるようになります。

初回は Nix がパッケージをダウンロードするため、数分かかることがあります。気長に待ってください。

### 2.3 Python パッケージをインストールする

```bash
$ uv sync --all-groups
```

これで開発用パッケージ（ruff, mypy, pytest など）も含めてインストールされます。

### 2.4 動作確認

以下を実行して、環境が正しく動いているか確認してください。

```bash
$ uv run python src/parallel_processing/greet.py
Hello, Nix + uv! Running on Python 3.12
```

表示されれば成功です。

テストも実行してみましょう。

```bash
$ uv run pytest
```

`1 passed` のように表示されればOKです。

---

## 3. よく使うコマンド

### Python スクリプトを実行する

```bash
$ uv run python src/parallel_processing/greet.py
```

### 新しいパッケージを追加する

```bash
$ uv add パッケージ名
```

例：`requests` を追加する場合

```bash
$ uv add requests
```

### 開発用パッケージを追加する

```bash
$ uv add --group dev パッケージ名
```

例：`black` を開発用に追加する場合

```bash
$ uv add --group dev black
```

### コードのLint（構文チェック）を実行する

```bash
$ uv run ruff check .
```

### コードの自動修正を試す

```bash
$ uv run ruff check . --fix
```

### 型チェックを実行する

```bash
$ uv run mypy .
```

### テストを実行する

```bash
$ uv run pytest
```

### 仮想環境を再作成したいとき

何かおかしいと思ったら、ロックファイルと仮想環境を作り直してみてください。

```bash
$ rm -rf .venv uv.lock
$ uv sync --all-groups
```

---

## 4. トラブルシューティング

### `nix: command not found` と表示される

Nix のインストール後、ターミナルを再起動していないか、シェルの設定ファイルが読み込まれていない可能性があります。

```bash
$ . /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh
```

を実行してから、もう一度 `nix --version` を試してください。

### `direnv: command not found` と表示される

direnv がインストールされていないか、シェルのフック設定が反映されていません。

1. インストールされているか確認

```bash
$ which direnv
```

何も表示されない場合は、[1.2 direnvのインストール](#12-direnv自動環境有効化) に戻ってください。

2. フック設定を確認

```bash
$ grep "direnv hook" ~/.bashrc ~/.zshrc 2>/dev/null
```

何も表示されない場合は、該当するシェルの設定ファイルに `eval "$(direnv hook bash)"` または `eval "$(direnv hook zsh)"` を追加してください。

### `direnv allow` 後、毎回 Nix のダウンロードが始まる

通常は初回だけダウンロードします。毎回ダウンロードする場合は、`direnv` と `nix-direnv` のどちらかが正しく設定されていない可能性があります。

```bash
$ echo 'source $HOME/.nix-profile/share/nix-direnv/direnvrc' >> ~/.config/direnv/direnvrc
```

`~/.config/direnv/` フォルダがない場合は先に作成してください。

```bash
$ mkdir -p ~/.config/direnv
```

### `uv: command not found` と表示される

direnv の環境が有効になっていない可能性があります。

```bash
$ cd ..
$ cd parallel-processing
```

と一度フォルダを出て入り直すか、以下を実行してください。

```bash
$ nix develop
```

### WSL2 でネットワークエラーが出る

WSL2 では `systemd` が有効になっていないと Nix のサービスが動かないことがあります。

```bash
$ test -f /etc/wsl.conf && cat /etc/wsl.conf
```

以下の内容が含まれていない場合、`/etc/wsl.conf` を作成・編集してください。

```ini
[boot]
systemd=true
```

その後、WSL2 をシャットダウンして再起動してください。

```powershell
# PowerShell（Windows側）で実行
wsl --shutdown
```

---

## 5. ファイルの説明

| ファイル | 役割 |
|---|---|
| `flake.nix` | Nix が読む設定ファイル。Python 3.12 や uv をインストールする指示が書いてあります。 |
| `.envrc` | direnv が読む設定ファイル。このフォルダに入ったら `flake.nix` を使うよう指示しています。 |
| `pyproject.toml` | Python プロジェクトの設定ファイル。依存パッケージやツールの設定が書いてあります。 |
| `uv.lock` | uv が作るロックファイル。どのバージョンのパッケージを使うか正確に記録しています。 |
| `src/parallel_processing/` | Python のソースコードを置くフォルダです。 |
| `tests/` | テストコードを置くフォルダです。 |

---

## 6. 次に何をすればいい？

- 新しい Python ファイルを `src/parallel_processing/` に作って、`uv run python ファイル名.py` で実行してみましょう。
- 必要なパッケージがあれば `uv add パッケージ名` で追加しましょう。
- テストを書く場合は `tests/` に `test_*.py` という名前でファイルを作り、`uv run pytest` で実行しましょう。

何かうまくいかない場合は、エラーメッセージをコピーして相談してください。
