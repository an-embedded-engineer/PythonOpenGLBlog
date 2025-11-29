
"""
PythonOpenGL - Phase 2: GLFWウィンドウ作成
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
