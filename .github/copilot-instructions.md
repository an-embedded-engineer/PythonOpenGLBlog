# Copilot Instructions - PythonOpenGL

## プロジェクト概要

OpenGL 3DプログラミングをPythonで学ぶブログシリーズのサンプルコード。
各フェーズで段階的に`src/main.py`を拡張していく構成。

## クイックスタート

```bash
source .venv/bin/activate && python -m src.main
```

## アーキテクチャ

```
src/main.py          → App (core/app.py) → Window, GUI, Shader
     ↓                      ↓
setup_logger()        メインループ: _update() → _render()
```

- **App** (`core/app.py`): メインループ、シェーダー/ジオメトリ管理、imgui描画
- **Window** (`core/window.py`): GLFW初期化、OpenGL 3.3 Core Profile設定
- **GUI** (`core/gui.py`): imgui-bundle + GlfwRenderer
- **Shader** (`graphics/shader.py`): GLSLコンパイル/リンク、uniform管理

## 開発フロー


### フェーズ開発の手順（必須チェックリスト）

各フェーズ開始時に以下の手順を確認し、順番に実施すること。

| # | ステップ | 内容 | 完了条件 | 担当 |
|---|----------|------|----------|------|
| 1 | ブランチ作成 | `phase{番号}/{キーワード}` でブランチ作成 | ブランチ切り替え完了 | ユーザー |
| 2 | リファクタリング | (必要に応じて)コード整理、レビュー、動作確認（詳細は2-1〜2-3） | 動作確認OK | Copilot/ユーザー（詳細は下記サブステップ参照） |
| 2-1 | リファクタ指示 | リファクタを実施する箇所・目的を指示 | 指示記録済み | ユーザー |
| 2-2 | リファクタ仕様検討 | Copilotが提案するリファクタ仕様を作成 | 仕様案作成 | Copilot |
| 2-3 | リファクタ実行・承認 | リファクタを実行し最終確認 | 動作確認OK | ユーザー |
| 3 | コード・記事作成 | 機能実装、ブログ記事作成、自動テスト作成（詳細は3-1〜3-3） | テスト通過 | Copilot/ユーザー（詳細は下記サブステップ参照） |
| 3-1 | 要件整理 | 機能要件や記事構成を確定する | 要件確定 | ユーザー |
| 3-2 | 実装・記事下書き | Copilotがコード生成・記事下書きを作成 | 下書き作成 | Copilot |
| 3-3 | レビュー・最終承認 | ユーザーがレビュー、修正、承認を行う | テスト通過・承認済み | ユーザー |
| 4 | 変更点レビュー | git diffで変更内容を確認（詳細は4-1〜4-2） | ユーザー確認OK | Copilot/ユーザー（詳細は下記サブステップ参照） |
| 4-1 | 変更点説明 | Copilotが差分と意図を説明する | 説明提供 | Copilot |
| 4-2 | 変更点承認 | ユーザーが差分を確認し承認する | ユーザー承認済み | ユーザー |
| 5 | 動作確認 | アプリケーション実行、動作テスト（詳細は5-1〜5-2） | 動作確認OK | Copilot/ユーザー（詳細は下記サブステップ参照） |
| 5-1 | 動作確認手順作成 | Copilotが実行手順とテストケースを提示 | 手順提示済み | Copilot |
| 5-2 | 実行・検証 | ユーザーがアプリケーションを実行し検証 | 動作確認OK | ユーザー |
| 6 | レビュー・承認 | ユーザーによる最終レビュー | 承認取得 | ユーザー |
| 7 | コミット・プッシュ | 変更をコミットしてリモートにプッシュ | プッシュ完了 | ユーザー |
| 8 | 記事公開 | はてなブログに記事を公開、公開URL連絡 | URL受領 | ユーザー |
| 9 | リンク更新 | 計画、記事リスト、前回記事からのリンク更新（詳細は9-1〜9-3） | 更新完了 | Copilot/ユーザー（詳細は下記サブステップ参照） |
| 9-1 | リンク更新案作成 | Copilotがリンク更新案を作成する | 更新案作成済み | Copilot |
| 9-2 | ファイル修正 | Copilotが対象ファイルに修正を入れる（ユーザー確認前） | 修正済み | Copilot |
| 9-3 | 公開URL確認・最終コミット | ユーザーが公開URLを確認し、最終コミットを行う | 最終コミット済み | ユーザー |
| 10 | レビュー・承認 | リンク更新のレビュー | 承認取得 | ユーザー |
| 11 | タグ付け・マージ | `v{番号}.0` タグ作成、mainにマージ・プッシュ | マージ完了 | ユーザー |
| 12 | フェーズ終了 | 次フェーズの準備完了（詳細は12-1〜12-2） | 完了確認 | Copilot/ユーザー（詳細は下記サブステップ参照） |
| 12-1 | 次回準備案作成 | CopilotがIssueやタスクを作成・提案する | 案作成済み | Copilot |
| 12-2 | 次フェーズ開始承認 | ユーザーが案を確認し、次フェーズ開始を承認する | 承認済み | ユーザー |

### ブランチ運用
- 各フェーズは専用ブランチで開発: `phase{番号}/{キーワード}`
- 例: `phase4/shader-triangle`, `phase6b/complex-shapes`
- 記事公開時にタグ付け（`v4.0`等）→ mainにマージ

### Git操作手順（ユーザー主導）
- **コミット**: 機能実装完了後、ステージ・コミット・プッシュを実施
  ```bash
  git add -A
  git commit -m "feat: Phase {番号}{サブ番号} - {機能説明}"
  git push -u origin phase{番号}{サブ番号}/{キーワード}
  ```
- **タグ付け・マージ**: 記事公開後、以下の順序で実施
  ```bash
  git tag v{番号}{サブ番号}.0  # タグ作成（例: v5a.0）
  git checkout main
  git merge phase{番号}{サブ番号}/{キーワード}
  git push origin main
  git push origin v{番号}{サブ番号}.0
  ```

### コミットメッセージルール
- **機能実装**: `feat: Phase {番号} - {説明}`
- **ドキュメント更新**: `docs: Phase {番号} - {説明}`
- **バグ修正**: `fix: {説明}`
- **リファクタリング**: `refactor: {説明}`
- 例:
  - `feat: Phase 5a - 座標変換システムの実装`
  - `docs: Phase 5a - リンク更新（公開済み記事一覧）`

### コード編集の原則
- `src/main.py`は**段階的に拡張**する（前フェーズのコードを維持しつつ機能追加）
- 各フェーズで動作するサンプルコードを維持する
- **教育的価値重視**: 複雑な抽象化より明示的で理解しやすいコードを優先
- **imguiでインタラクティブ**: パラメータ調整可能なデモを目指す

## 技術スタック

| ライブラリ | 用途 |
|-----------|------|
| `glfw` | ウィンドウ管理・入力処理 |
| `PyOpenGL` | OpenGLバインディング |
| `numpy` | 行列計算・頂点データ |
| `imgui-bundle` | デバッグUI・パラメータ調整 |
| `mapbox_earcut` | ポリゴン三角形分割 |

## コーディング規約

### Python
- 型ヒントを使用（`def main() -> None:`）
- エントリポイントは`if __name__ == '__main__':`で囲む

### OpenGL
- OpenGL 3.3+ Core Profileを使用
- PyOpenGLは `import OpenGL.GL as gl` 形式でインポートし、`gl.` プレフィックスで使用
- シェーダーはGLSLで記述（バージョン: `#version 330 core`）
- シェーダーファイルは `src/shaders/` に配置（`.vert`, `.frag` 拡張子）
- 頂点属性: `layout (location = 0) in vec3 aPos;`

### ロガー
```python
from src.utils import setup_logger, logger, FORCE, TIME, TRACE
setup_logger(level=logging.DEBUG, log_to_file=True, log_dir="logs")
logger.debug("message")  # カスタムレベル: logger.force(), logger.time(), logger.trace()
```

### imgui初期化順序（重要）
```python
self._window = Window(800, 600, "Title")
self._gui = GUI(self._window)
self._window.setup_key_callback()  # GUI後にコールバック設定（GlfwRendererが上書きするため）
```

### テスト
- Phase 4以降、クラスや機能単位でpytestによるユニットテストを作成
- テストファイルは`tests/`ディレクトリに配置

## ディレクトリ構成

```
src/
├── main.py           # エントリポイント
├── core/             # コアモジュール
│   ├── app.py        # Appクラス（メインループ、描画処理）
│   ├── window.py     # Windowクラス（GLFW管理）
│   └── gui.py        # GUIクラス（imgui管理）
├── graphics/         # 描画関連
│   └── shader.py     # Shaderクラス（シェーダー管理）
├── shaders/          # GLSLシェーダーファイル
│   ├── basic.vert    # 頂点シェーダー
│   └── basic.frag    # フラグメントシェーダー
└── utils/            # ユーティリティ
    └── logger.py     # カスタムロガー（カラー出力、ORフィルタ対応）
tests/                # ユニットテスト
plan/                 # ブログ計画・設計メモ
blog/                 # ブログ記事下書き
```

## フェーズ一覧（参照: plan/blog_phases.md）

Phase 1-3: 環境構築・ウィンドウ・imgui基礎
Phase 4: シェーダー入門・三角形描画
Phase 5: カメラ・座標変換
Phase 6a-6b: 形状描画（基本→複合）
Phase 7a-7b: 高速化（バッチ→インスタンシング）
Phase 8-12: テクスチャ・ライティング・応用

## ブログ記事について

### 公開先
- **はてなブログ**: https://an-embedded-engineer.hateblo.jp/
- 記法: Markdown

### はてなブログ固有の記法
- 画像: `[f:id:ユーザー名:画像ID:plain]` 形式（フォトライフにアップロード）
- 記事リンク: `[記事タイトル:embed:cite]` または URL直接貼り付けでカード形式
- コードブロック: 標準Markdownの ``` で可（シンタックスハイライト対応）
- 目次: `[:contents]` で自動生成
- 脚注: `((脚注テキスト))` 形式

### 進捗管理
- 記事公開時に以下のファイルを更新する：
  1. `plan/blog_phases.md` - 「公開済み記事」テーブルに新規行を追加（Phase番号、タイトル、公開日、Gitタグ、URL）
  2. `blog/phase{前回番号}.md` - 最後の「次回」リンク部分を公開URLに更新
  3. `blog/phase{今回番号}.md` - 画像キャプションなどの確認（必要に応じて修正）
  4. `blog/phase0_introduction.md` - 公開済み記事一覧テーブルに新規行を追加

## 注意事項

- ブログ記事用サンプルのため、**読みやすさ・教育的価値**を重視
- 複雑な抽象化より、明示的で理解しやすいコードを優先
- imguiでパラメータ調整可能にし、インタラクティブなデモを目指す
