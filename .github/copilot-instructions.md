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

| # | ステップ | 内容 | 完了条件 |
|---|----------|------|----------|
| 1 | ブランチ作成 | `phase{番号}/{キーワード}` でブランチ作成 | ブランチ切り替え完了 |
| 2 | リファクタリング | (必要に応じて)コード整理、レビュー、動作確認 | 動作確認OK |
| 3 | コード・記事作成 | 機能実装、ブログ記事作成、自動テスト作成 | テスト通過 |
| 4 | 変更点レビュー | git diffで変更内容を確認 | ユーザー確認OK |
| 5 | 動作確認 | アプリケーション実行、動作テスト | 動作確認OK |
| 6 | レビュー・承認 | ユーザーによる最終レビュー | 承認取得 |
| 7 | コミット・プッシュ | 変更をコミットしてリモートにプッシュ | プッシュ完了 |
| 8 | 記事公開 | はてなブログに記事を公開、公開URL連絡 | URL受領 |
| 9 | リンク更新 | 計画、記事リスト、前回記事からのリンク更新 | 更新完了 |
| 10 | レビュー・承認 | リンク更新のレビュー | 承認取得 |
| 11 | タグ付け・マージ | `v{番号}.0` タグ作成、mainにマージ・プッシュ | マージ完了 |
| 12 | フェーズ終了 | 次フェーズの準備完了 | 完了確認 |

### ブランチ運用
- 各フェーズは専用ブランチで開発: `phase{番号}/{キーワード}`
- 例: `phase4/shader-triangle`, `phase6b/complex-shapes`
- 記事公開時にタグ付け（`v4.0`等）→ mainにマージ

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
- 記事公開時に `plan/blog_phases.md` の「公開済み記事」テーブルを更新
- 記録項目: Phase番号、タイトル、公開日、Gitタグ、URL
- 前回記事の「次回」リンクも公開URLに更新する

## 注意事項

- ブログ記事用サンプルのため、**読みやすさ・教育的価値**を重視
- 複雑な抽象化より、明示的で理解しやすいコードを優先
- imguiでパラメータ調整可能にし、インタラクティブなデモを目指す
