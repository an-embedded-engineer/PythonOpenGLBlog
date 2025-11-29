# GitHub Copilotと作る Pythonで OpenGL 3Dプログラミング

## 第2回「GLFWでウィンドウを作る」

[:contents]

### はじめに

前回は、Pythonで3Dプログラミングを行うための開発環境を構築しました。

今回は、いよいよOpenGLプログラミングの第一歩として、GLFWを使ってウィンドウを表示してみます。ウィンドウの作成は、3Dグラフィックスを表示するための基盤となる重要なステップです。

### GLFWとは

**GLFW**（Graphics Library Framework）は、OpenGLアプリケーションの開発を支援するライブラリです。以下の機能を提供します：

- ウィンドウの作成と管理
- OpenGLコンテキストの作成
- キーボード・マウス入力の処理
- ジョイスティック対応
- マルチモニター対応

GLFWは軽量で使いやすく、クロスプラットフォーム（Windows、macOS、Linux）で動作します。

### 最小限のウィンドウ表示

まずは、最小限のコードでウィンドウを表示してみましょう。

`src/main.py`を以下の内容に更新します：

```python
"""
PythonOpenGL - Phase 2: GLFWウィンドウ作成
"""
import glfw
from OpenGL.GL import (
    glClear,
    glClearColor,
    GL_COLOR_BUFFER_BIT,
)


def main() -> None:
    """メイン関数"""
    # GLFWの初期化
    if not glfw.init():
        raise RuntimeError("GLFWの初期化に失敗しました")

    try:
        # ウィンドウの作成
        window = glfw.create_window(800, 600, "PythonOpenGL", None, None)
        if not window:
            raise RuntimeError("ウィンドウの作成に失敗しました")

        # OpenGLコンテキストを現在のスレッドに設定
        glfw.make_context_current(window)

        # 背景色の設定（ダークグレー）
        glClearColor(0.2, 0.2, 0.2, 1.0)

        # メインループ
        while not glfw.window_should_close(window):
            # 画面のクリア
            glClear(GL_COLOR_BUFFER_BIT)

            # バッファの入れ替え（ダブルバッファリング）
            glfw.swap_buffers(window)

            # イベントの処理
            glfw.poll_events()

    finally:
        # GLFWの終了処理
        glfw.terminate()


if __name__ == '__main__':
    main()
```

### コードの解説

#### 1. GLFWの初期化

```python
if not glfw.init():
    raise RuntimeError("GLFWの初期化に失敗しました")
```

`glfw.init()`でGLFWライブラリを初期化します。失敗した場合は`False`が返されるので、エラー処理を行います。

#### 2. ウィンドウの作成

```python
window = glfw.create_window(800, 600, "PythonOpenGL", None, None)
```

`glfw.create_window()`でウィンドウを作成します。引数は以下の通りです：

| 引数 | 説明 |
|------|------|
| 800 | ウィンドウの幅（ピクセル） |
| 600 | ウィンドウの高さ（ピクセル） |
| "PythonOpenGL" | ウィンドウのタイトル |
| None | フルスクリーン時のモニター（Noneで通常ウィンドウ） |
| None | コンテキストを共有するウィンドウ（Noneで共有なし） |

#### 3. OpenGLコンテキストの設定

```python
glfw.make_context_current(window)
```

OpenGLの描画命令は「コンテキスト」と呼ばれる状態に対して行われます。この行で、作成したウィンドウのOpenGLコンテキストを現在のスレッドに紐づけます。

#### 4. 背景色の設定

```python
glClearColor(0.2, 0.2, 0.2, 1.0)
```

`glClearColor()`で画面をクリアする際の色を設定します。引数はRGBA（赤、緑、青、透明度）で、それぞれ0.0〜1.0の範囲で指定します。ここではダークグレー（0.2, 0.2, 0.2）を設定しています。

#### 5. メインループ

```python
while not glfw.window_should_close(window):
    glClear(GL_COLOR_BUFFER_BIT)
    glfw.swap_buffers(window)
    glfw.poll_events()
```

3Dアプリケーションの心臓部となるメインループです。ウィンドウが閉じられるまで以下を繰り返します：

1. **glClear()**: 画面を背景色でクリア
2. **swap_buffers()**: バッファを入れ替えて描画結果を表示（ダブルバッファリング）
3. **poll_events()**: キーボード・マウスなどのイベントを処理

#### 6. 終了処理

```python
finally:
    glfw.terminate()
```

`try-finally`を使って、エラーが発生しても必ず`glfw.terminate()`が呼ばれるようにしています。これにより、GLFWが確保したリソースが適切に解放されます。

### 動作確認

コードを実行してみましょう：

```bash
# 仮想環境を有効化
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# 実行
python src/main.py
```

ダークグレーの背景を持つウィンドウが表示されれば成功です！

ウィンドウを閉じるには、ウィンドウの×ボタンをクリックするか、Escキーを押して...と言いたいところですが、まだキーボード入力を処理していないので×ボタンでのみ閉じられます。

### キーボード入力の追加

ウィンドウをEscキーで閉じられるようにしましょう。また、ウィンドウサイズの変更にも対応します。

```python
"""
PythonOpenGL - Phase 2: GLFWウィンドウ作成（キーボード対応版）
"""
import glfw
from OpenGL.GL import (
    glClear,
    glClearColor,
    glViewport,
    GL_COLOR_BUFFER_BIT,
)


def key_callback(window, key: int, scancode: int, action: int, mods: int) -> None:
    """キーボード入力のコールバック関数"""
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)


def framebuffer_size_callback(window, width: int, height: int) -> None:
    """フレームバッファサイズ変更時のコールバック関数"""
    glViewport(0, 0, width, height)


def main() -> None:
    """メイン関数"""
    # GLFWの初期化
    if not glfw.init():
        raise RuntimeError("GLFWの初期化に失敗しました")

    try:
        # OpenGLバージョンの指定（3.3 Core Profile）
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, True)  # macOSで必要

        # ウィンドウの作成
        window = glfw.create_window(800, 600, "PythonOpenGL", None, None)
        if not window:
            raise RuntimeError("ウィンドウの作成に失敗しました")

        # OpenGLコンテキストを現在のスレッドに設定
        glfw.make_context_current(window)

        # コールバック関数の設定
        glfw.set_key_callback(window, key_callback)
        glfw.set_framebuffer_size_callback(window, framebuffer_size_callback)

        # 背景色の設定（ダークグレー）
        glClearColor(0.2, 0.2, 0.2, 1.0)

        # メインループ
        while not glfw.window_should_close(window):
            # 画面のクリア
            glClear(GL_COLOR_BUFFER_BIT)

            # バッファの入れ替え
            glfw.swap_buffers(window)

            # イベントの処理
            glfw.poll_events()

    finally:
        # GLFWの終了処理
        glfw.terminate()


if __name__ == '__main__':
    main()
```

### 追加したコードの解説

#### OpenGLバージョンの指定

```python
glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, True)
```

`window_hint()`でウィンドウ作成時のオプションを設定します。ここでは以下を指定しています：

- **OpenGL 3.3**: モダンなOpenGLの基本となるバージョン
- **Core Profile**: 古い非推奨機能を使わないモード
- **Forward Compatible**: macOSで必要なオプション

#### キーボードコールバック

```python
def key_callback(window, key: int, scancode: int, action: int, mods: int) -> None:
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)
```

キーが押されたときに呼ばれる関数です。Escキーが押されたらウィンドウを閉じるフラグを立てます。

#### フレームバッファサイズコールバック

```python
def framebuffer_size_callback(window, width: int, height: int) -> None:
    glViewport(0, 0, width, height)
```

ウィンドウサイズが変更されたときに呼ばれます。`glViewport()`で描画領域を新しいサイズに合わせて更新します。

### 背景色を変えてみよう

せっかくなので、背景色を変えて遊んでみましょう。`glClearColor()`の引数を変更すると、様々な色の背景を表示できます。

```python
# 例: 青みがかったグレー
glClearColor(0.1, 0.1, 0.2, 1.0)

# 例: 暗い緑
glClearColor(0.0, 0.2, 0.1, 1.0)

# 例: コーンフラワーブルー（DirectXのデフォルト背景色）
glClearColor(0.392, 0.584, 0.929, 1.0)
```

次回、imguiを導入すると、スライダーでリアルタイムに色を変更できるようになります！

### まとめ

今回は、GLFWを使ってOpenGLウィンドウを作成しました。

- GLFWの初期化と終了処理
- ウィンドウの作成
- OpenGLコンテキストの設定
- メインループの実装
- キーボード入力のコールバック
- ウィンドウサイズ変更への対応

次回は、imguiを導入して、パラメータをリアルタイムに調整できるデバッグUIを追加します。

---

**前回**: [第1回「開発環境を整えよう」](https://an-embedded-engineer.hateblo.jp/entry/2025/11/29/234119)

**次回**: 第3回「imguiを組み込む」（準備中）
