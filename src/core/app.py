"""
アプリケーションモジュール
"""
from imgui_bundle import imgui
from OpenGL.GL import (
    glClear,
    glClearColor,
    GL_COLOR_BUFFER_BIT,
)

from src.core.window import Window
from src.core.gui import GUI
from src.utils.logger import logger


class App:
    """アプリケーションクラス"""

    def __init__(self) -> None:
        """アプリケーションを初期化する"""
        logger.debug("App.__init__ start")
        self._window = Window(800, 600, "PythonOpenGL")
        self._gui = GUI(self._window)

        # GUI初期化後にキーコールバックを設定（GlfwRendererが上書きするため）
        self._window.setup_key_callback()

        # 背景色（RGBA、0.0〜1.0）
        self._clear_color = [0.2, 0.2, 0.2, 1.0]
        logger.debug("App.__init__ end")

    def run(self) -> None:
        """メインループを実行する"""
        logger.debug("App.run() start")
        try:
            while not self._window.should_close:
                self._update()
                self._render()
            logger.debug("Main loop ended")
        finally:
            self._shutdown()
        logger.debug("App.run() end")

    def _update(self) -> None:
        """更新処理"""
        self._window.poll_events()
        self._gui.process_inputs()
        self._gui.new_frame()

        # ===== imguiウィンドウ =====
        self._draw_settings_window()

    def _draw_settings_window(self) -> None:
        """設定ウィンドウを描画"""
        imgui.begin("Settings")

        # 背景色の変更
        changed, self._clear_color = imgui.color_edit4("Background", self._clear_color)

        # FPSの表示
        imgui.text(f"FPS: {self._gui.get_fps():.1f}")

        # ボタンの例
        if imgui.button("Reset Color"):
            self._clear_color = [0.2, 0.2, 0.2, 1.0]

        imgui.end()

    def _render(self) -> None:
        """描画処理"""
        # 背景色の適用
        glClearColor(*self._clear_color)

        # 画面のクリア
        glClear(GL_COLOR_BUFFER_BIT)

        # imguiのレンダリング
        self._gui.render()

        # バッファの入れ替え
        self._window.swap_buffers()

    def _shutdown(self) -> None:
        """終了処理"""
        self._gui.shutdown()
        self._window.terminate()
