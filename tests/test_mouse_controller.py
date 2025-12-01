"""
マウスコントローラーモジュールのユニットテスト
"""
import pytest
from unittest.mock import MagicMock, patch

from src.core.mouse_controller import MouseController, MouseButton


class MockGLFW:
    """GLFWモジュールのモック"""
    MOUSE_BUTTON_LEFT = 0
    MOUSE_BUTTON_RIGHT = 1
    MOUSE_BUTTON_MIDDLE = 2
    PRESS = 1
    RELEASE = 0


class TestMouseButton:
    """MouseButtonのテスト"""

    def test_enum_values(self) -> None:
        """列挙値のテスト"""
        assert MouseButton.LEFT.value == 0
        assert MouseButton.RIGHT.value == 1
        assert MouseButton.MIDDLE.value == 2

    def test_int_conversion(self) -> None:
        """int変換のテスト"""
        assert MouseButton(0) == MouseButton.LEFT
        assert MouseButton(1) == MouseButton.RIGHT
        assert MouseButton(2) == MouseButton.MIDDLE


class TestMouseController:
    """MouseControllerクラスのテスト"""

    @pytest.fixture
    def mock_window(self) -> MagicMock:
        """モックウィンドウを作成"""
        return MagicMock()

    @pytest.fixture
    def controller(self, mock_window: MagicMock) -> MouseController:
        """MouseControllerインスタンスを作成"""
        with patch('src.core.mouse_controller.glfw') as mock_glfw:
            mock_glfw.MOUSE_BUTTON_LEFT = 0
            mock_glfw.MOUSE_BUTTON_RIGHT = 1
            mock_glfw.MOUSE_BUTTON_MIDDLE = 2
            mock_glfw.PRESS = 1
            mock_glfw.RELEASE = 0
            mock_glfw.get_cursor_pos.return_value = (100.0, 200.0)
            mock_glfw.set_mouse_button_callback.return_value = None
            mock_glfw.set_cursor_pos_callback.return_value = None
            mock_glfw.set_scroll_callback.return_value = None

            controller = MouseController(mock_window)
            return controller

    def test_init(self, controller: MouseController) -> None:
        """初期化のテスト"""
        assert controller.position == (100.0, 200.0)
        assert controller.delta == (0.0, 0.0)
        assert controller.scroll == (0.0, 0.0)
        assert not controller.is_left_dragging
        assert not controller.is_right_dragging
        assert not controller.is_middle_dragging

    def test_button_press(self, controller: MouseController) -> None:
        """ボタン押下のテスト"""
        with patch('src.core.mouse_controller.glfw') as mock_glfw:
            mock_glfw.PRESS = 1
            mock_glfw.RELEASE = 0

            # 左ボタンを押す
            controller._mouse_button_callback(None, 0, 1, 0)
            assert controller.is_left_dragging

            # 左ボタンを離す
            controller._mouse_button_callback(None, 0, 0, 0)
            assert not controller.is_left_dragging

    def test_button_press_right(self, controller: MouseController) -> None:
        """右ボタン押下のテスト"""
        with patch('src.core.mouse_controller.glfw') as mock_glfw:
            mock_glfw.PRESS = 1
            mock_glfw.RELEASE = 0

            controller._mouse_button_callback(None, 1, 1, 0)
            assert controller.is_right_dragging

            controller._mouse_button_callback(None, 1, 0, 0)
            assert not controller.is_right_dragging

    def test_button_press_middle(self, controller: MouseController) -> None:
        """中ボタン押下のテスト"""
        with patch('src.core.mouse_controller.glfw') as mock_glfw:
            mock_glfw.PRESS = 1
            mock_glfw.RELEASE = 0

            controller._mouse_button_callback(None, 2, 1, 0)
            assert controller.is_middle_dragging

            controller._mouse_button_callback(None, 2, 0, 0)
            assert not controller.is_middle_dragging

    def test_cursor_position_update(self, controller: MouseController) -> None:
        """カーソル位置更新のテスト"""
        controller._cursor_pos_callback(None, 150.0, 250.0)
        assert controller.position == (150.0, 250.0)
        assert controller.delta == (50.0, 50.0)  # 150-100, 250-200

    def test_scroll(self, controller: MouseController) -> None:
        """スクロールのテスト"""
        controller._scroll_callback(None, 0.0, 1.0)
        assert controller.scroll == (0.0, 1.0)

        controller._scroll_callback(None, 0.0, -2.0)
        assert controller.scroll == (0.0, -1.0)  # 1.0 + (-2.0) = -1.0

    def test_update_resets_scroll(self, controller: MouseController) -> None:
        """update()がスクロール量をリセットするテスト"""
        controller._scroll_callback(None, 0.0, 1.0)
        assert controller.scroll == (0.0, 1.0)

        controller.update()
        assert controller.scroll == (0.0, 0.0)

    def test_update_saves_last_position(self, controller: MouseController) -> None:
        """update()が前フレーム位置を保存するテスト"""
        controller._cursor_pos_callback(None, 150.0, 250.0)
        assert controller.delta == (50.0, 50.0)

        controller.update()
        assert controller.delta == (0.0, 0.0)  # lastが更新されたのでdeltaは0

    def test_is_pressed(self, controller: MouseController) -> None:
        """is_pressed()のテスト"""
        assert not controller.is_pressed(MouseButton.LEFT)

        with patch('src.core.mouse_controller.glfw') as mock_glfw:
            mock_glfw.PRESS = 1
            controller._mouse_button_callback(None, 0, 1, 0)

        assert controller.is_pressed(MouseButton.LEFT)

    def test_is_dragging(self, controller: MouseController) -> None:
        """is_dragging()のテスト"""
        assert not controller.is_dragging(MouseButton.LEFT)

        with patch('src.core.mouse_controller.glfw') as mock_glfw:
            mock_glfw.PRESS = 1
            controller._mouse_button_callback(None, 0, 1, 0)

        assert controller.is_dragging(MouseButton.LEFT)

    def test_callback_chaining(self, mock_window: MagicMock) -> None:
        """コールバックチェーンのテスト"""
        prev_callback = MagicMock()

        with patch('src.core.mouse_controller.glfw') as mock_glfw:
            mock_glfw.MOUSE_BUTTON_LEFT = 0
            mock_glfw.MOUSE_BUTTON_RIGHT = 1
            mock_glfw.MOUSE_BUTTON_MIDDLE = 2
            mock_glfw.PRESS = 1
            mock_glfw.RELEASE = 0
            mock_glfw.get_cursor_pos.return_value = (0.0, 0.0)
            mock_glfw.set_mouse_button_callback.return_value = prev_callback
            mock_glfw.set_cursor_pos_callback.return_value = None
            mock_glfw.set_scroll_callback.return_value = None

            controller = MouseController(mock_window)

            # ボタンコールバックを呼ぶ
            controller._mouse_button_callback(None, 0, 1, 0)

            # 前のコールバックが呼ばれたことを確認
            prev_callback.assert_called_once_with(None, 0, 1, 0)
