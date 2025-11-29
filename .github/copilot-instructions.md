# Copilot Instructions - PythonOpenGL

## プロジェクト概要

OpenGL 3DプログラミングをPythonで学ぶブログシリーズのサンプルコード。
各フェーズで段階的に`src/main.py`を拡張していく構成。

## 開発フロー

### ブランチ運用
- 各フェーズは専用ブランチで開発: `phase{番号}/{キーワード}`
- 例: `phase4a/shader-vertex`, `phase6b/complex-shapes`
- 記事公開時にタグ付け（`v4a.0`等）→ mainにマージ

### コード編集の原則
- `src/main.py`は**段階的に拡張**する（前フェーズのコードを維持しつつ機能追加）
- 各フェーズで動作するサンプルコードを維持する

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
- シェーダーはGLSLで記述（バージョン: `#version 330 core`）
- シェーダーファイルは別ファイル(.glsl)に分離（Phase 4で`shaders/`ディレクトリを作成予定）

### テスト
- Phase 4以降、クラスや機能単位でpytestによるユニットテストを作成
- テストファイルは`tests/`ディレクトリに配置

## ディレクトリ構成

```
src/main.py        # メインプログラム（段階的に拡張）
src/shaders/       # シェーダーファイル（Phase 4以降）
tests/             # ユニットテスト（Phase 4以降）
plan/              # ブログ計画・設計メモ
blog/              # ブログ記事下書き
```

## フェーズ一覧（参照: plan/blog_phases.md）

Phase 1-3: 環境構築・ウィンドウ・imgui基礎
Phase 4a-4c: シェーダー・初ポリゴン描画
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

## 注意事項

- ブログ記事用サンプルのため、**読みやすさ・教育的価値**を重視
- 複雑な抽象化より、明示的で理解しやすいコードを優先
- imguiでパラメータ調整可能にし、インタラクティブなデモを目指す
