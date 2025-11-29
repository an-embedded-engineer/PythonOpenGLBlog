"""
imgui管理モジュール
"""
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer

from src.core.window import Window
from src.utils.logger import logger


class GUI:
    """imgui管理クラス"""

    def __init__(self, window: Window) -> None:
        """imguiを初期化する"""
        logger.debug("GUI.__init__ start")
        imgui.create_context()
        logger.debug("imgui.create_context() done")
        self._impl = GlfwRenderer(window.handle)
        logger.debug("GlfwRenderer created")
        logger.debug("GUI.__init__ end")

    def process_inputs(self) -> None:
        """入力を処理する"""
        self._impl.process_inputs()

    def new_frame(self) -> None:
        """新しいフレームを開始する"""
        imgui.new_frame()

    def render(self) -> None:
        """imguiをレンダリングする"""
        imgui.render()
        self._impl.render(imgui.get_draw_data())

    def shutdown(self) -> None:
        """imguiを終了する"""
        logger.debug("GUI.shutdown() called")
        self._impl.shutdown()

    @staticmethod
    def get_fps() -> float:
        """FPSを取得する"""
        return imgui.get_io().framerate
