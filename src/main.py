
"""
PythonOpenGL - Phase 3: imgui基礎
"""
# imgui_bundleをglfwより先にインポート（GLFWライブラリの重複警告を回避）
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer

import glfw
from OpenGL.GL import (
    glClear,
    glClearColor,
    glViewport,
    GL_COLOR_BUFFER_BIT,
)


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
        window = glfw.create_window(800, 600, "PythonOpenGL - imgui", None, None)
        if not window:
            raise RuntimeError("ウィンドウの作成に失敗しました")

        # OpenGLコンテキストを現在のスレッドに設定
        glfw.make_context_current(window)

        # imguiの初期化
        imgui.create_context()
        impl = GlfwRenderer(window)

        # 背景色（RGBA、0.0〜1.0）
        clear_color = [0.2, 0.2, 0.2, 1.0]

        # メインループ
        while not glfw.window_should_close(window):
            # イベントの処理
            glfw.poll_events()
            impl.process_inputs()

            # imguiフレーム開始
            imgui.new_frame()

            # ===== imguiウィンドウ =====
            imgui.begin("Settings")

            # 背景色の変更
            changed, clear_color = imgui.color_edit4("Background", clear_color)

            # FPSの表示
            imgui.text(f"FPS: {imgui.get_io().framerate:.1f}")

            # ボタンの例
            if imgui.button("Reset Color"):
                clear_color = [0.2, 0.2, 0.2, 1.0]

            imgui.end()
            # ===========================

            # 背景色の適用
            glClearColor(*clear_color)

            # 画面のクリア
            glClear(GL_COLOR_BUFFER_BIT)

            # imguiのレンダリング
            imgui.render()
            impl.render(imgui.get_draw_data())

            # バッファの入れ替え
            glfw.swap_buffers(window)

        # imguiの終了処理
        impl.shutdown()

    finally:
        # GLFWの終了処理
        glfw.terminate()


if __name__ == '__main__':
    main()
