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

### SKILLファイル

詳細な開発手順は以下のSKILLファイルを参照：
- **フェーズ開発手順**: `.github/skills/phase-development-workflow/SKILL.md`
  - 12ステップの完全なチェックリスト、Git操作、コミットメッセージルール
- **記事公開後のリンク更新**: `.github/skills/update-blog-links-after-publish/SKILL.md`
  - 4つのファイル更新手順（blog_phases.md, 前回記事, 今回記事, introduction.md）

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
Phase 5a: 座標変換の基礎
Phase 5b: 2D/3Dカメラの実装
Phase 5c: マウスでカメラ操作
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

### ブログ記事下書きのルール
- **画像パス**: ローカルファイルの相対パスを使用（例: `images/phase6_1.png`）
  - GitHubでのプレビュー表示に対応
  - はてなブログ公開時にフォトライフ形式に差し替え
- **前回・次回リンク**: 記事末尾に必ず記載
  ```markdown
  ---

  **前回**: [第N回「タイトル」](URL)

  **次回**: 第N+1回「タイトル」（準備中）
  ```
  - 公開時に「次回」リンクを実URLに更新

### 進捗管理
- 記事公開後のリンク更新については `.github/skills/update-blog-links-after-publish/SKILL.md` を参照

## 注意事項

- ブログ記事用サンプルのため、**読みやすさ・教育的価値**を重視
- 複雑な抽象化より、明示的で理解しやすいコードを優先
- imguiでパラメータ調整可能にし、インタラクティブなデモを目指す
