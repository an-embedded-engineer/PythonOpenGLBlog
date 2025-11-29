"""
ウィンドウ管理モジュール
"""
import glfw

from src.utils.logger import logger


class Window:
    """ウィンドウ管理クラス"""

    def __init__(self, width: int = 800, height: int = 600, title: str = "PythonOpenGL") -> None:
        """ウィンドウを作成する"""
        logger.debug("Window.__init__ start")

        # GLFWの初期化
        if not glfw.init():
            raise RuntimeError("GLFWの初期化に失敗しました")
        logger.debug("glfw.init() done")

        # OpenGLバージョンの指定（3.3 Core Profile）
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, True)  # macOSで必要

        # ウィンドウの作成
        self._handle = glfw.create_window(width, height, title, None, None)
        if not self._handle:
            glfw.terminate()
            raise RuntimeError("ウィンドウの作成に失敗しました")
        logger.debug("glfw.create_window() done")

        # OpenGLコンテキストを現在のスレッドに設定
        glfw.make_context_current(self._handle)
        logger.debug("Window.__init__ end")

    def setup_key_callback(self) -> None:
        """キーボードコールバックを設定する（GUI初期化後に呼ぶ）"""
        logger.debug("Window.setup_key_callback() called")
        glfw.set_key_callback(self._handle, self._key_callback)

    def _key_callback(self, window, key: int, scancode: int, action: int, mods: int) -> None:
        """キーボード入力のコールバック関数"""
        logger.debug(f"_key_callback: key={key}, action={action}")
        if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
            logger.debug("ESC pressed, setting should_close")
            glfw.set_window_should_close(self._handle, True)

    @property
    def handle(self):
        """GLFWウィンドウハンドルを取得"""
        return self._handle

    @property
    def should_close(self) -> bool:
        """ウィンドウを閉じるべきか"""
        return glfw.window_should_close(self._handle)

    def swap_buffers(self) -> None:
        """バッファを入れ替える"""
        glfw.swap_buffers(self._handle)

    def poll_events(self) -> None:
        """イベントを処理する"""
        glfw.poll_events()

    def terminate(self) -> None:
        """GLFWを終了する"""
        logger.debug("Window.terminate() called")
        glfw.terminate()
