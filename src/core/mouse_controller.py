"""
マウス入力管理モジュール
"""
from enum import IntEnum
from typing import Callable, Optional, Tuple

import glfw

from src.utils.logger import logger


class MouseButton(IntEnum):
    """マウスボタン"""
    LEFT = glfw.MOUSE_BUTTON_LEFT
    RIGHT = glfw.MOUSE_BUTTON_RIGHT
    MIDDLE = glfw.MOUSE_BUTTON_MIDDLE


class MouseController:
    """
    マウス入力を管理するクラス

    GLFWからのマウスイベントを処理し、
    ドラッグ状態やスクロール量を追跡する

    Note:
        既存のコールバック（imgui等）を保持し、チェーンで呼び出す
    """

    def __init__(self, window_handle) -> None:
        """
        マウスコントローラーを初期化する

        Args:
            window_handle: GLFWウィンドウハンドル
        """
        self._window = window_handle

        # マウス位置
        self._current_x = 0.0
        self._current_y = 0.0
        self._last_x = 0.0
        self._last_y = 0.0

        # ボタン状態
        self._button_pressed = {
            MouseButton.LEFT: False,
            MouseButton.RIGHT: False,
            MouseButton.MIDDLE: False,
        }

        # ドラッグ開始位置
        self._drag_start_x = 0.0
        self._drag_start_y = 0.0

        # スクロール量（フレームごとにリセット）
        self._scroll_x = 0.0
        self._scroll_y = 0.0

        # 既存のコールバックを保存（imgui等）
        self._prev_mouse_button_callback: Optional[Callable] = None
        self._prev_cursor_pos_callback: Optional[Callable] = None
        self._prev_scroll_callback: Optional[Callable] = None

        # 既存のコールバックを取得してから、新しいコールバックを登録
        # Note: glfw.set_*_callback は前のコールバックを返す
        self._prev_mouse_button_callback = glfw.set_mouse_button_callback(
            window_handle, self._mouse_button_callback
        )
        self._prev_cursor_pos_callback = glfw.set_cursor_pos_callback(
            window_handle, self._cursor_pos_callback
        )
        self._prev_scroll_callback = glfw.set_scroll_callback(
            window_handle, self._scroll_callback
        )

        # 初期位置を取得
        x, y = glfw.get_cursor_pos(window_handle)
        self._current_x = x
        self._current_y = y
        self._last_x = x
        self._last_y = y

        logger.info("MouseController initialized")

    def _mouse_button_callback(self, window, button: int, action: int, mods: int) -> None:
        """マウスボタンコールバック"""
        # 既存のコールバック（imgui）を先に呼び出す
        if self._prev_mouse_button_callback:
            self._prev_mouse_button_callback(window, button, action, mods)

        if button in [MouseButton.LEFT, MouseButton.RIGHT, MouseButton.MIDDLE]:
            mouse_button = MouseButton(button)
            if action == glfw.PRESS:
                self._button_pressed[mouse_button] = True
                self._drag_start_x = self._current_x
                self._drag_start_y = self._current_y
            elif action == glfw.RELEASE:
                self._button_pressed[mouse_button] = False

    def _cursor_pos_callback(self, window, x: float, y: float) -> None:
        """カーソル位置コールバック"""
        # 既存のコールバック（imgui）を先に呼び出す
        if self._prev_cursor_pos_callback:
            self._prev_cursor_pos_callback(window, x, y)

        self._current_x = x
        self._current_y = y

    def _scroll_callback(self, window, x_offset: float, y_offset: float) -> None:
        """スクロールコールバック"""
        # 既存のコールバック（imgui）を先に呼び出す
        if self._prev_scroll_callback:
            self._prev_scroll_callback(window, x_offset, y_offset)

        self._scroll_x += x_offset
        self._scroll_y += y_offset

    def update(self) -> None:
        """
        フレーム更新

        前フレームの位置を保存し、スクロール量をリセット
        """
        self._last_x = self._current_x
        self._last_y = self._current_y
        self._scroll_x = 0.0
        self._scroll_y = 0.0

    @property
    def position(self) -> Tuple[float, float]:
        """現在のマウス位置"""
        return (self._current_x, self._current_y)

    @property
    def delta(self) -> Tuple[float, float]:
        """前フレームからの移動量"""
        return (self._current_x - self._last_x, self._current_y - self._last_y)

    @property
    def scroll(self) -> Tuple[float, float]:
        """スクロール量（X, Y）"""
        return (self._scroll_x, self._scroll_y)

    def is_pressed(self, button: MouseButton) -> bool:
        """指定ボタンが押されているか"""
        return self._button_pressed.get(button, False)

    def is_dragging(self, button: MouseButton) -> bool:
        """指定ボタンでドラッグ中か"""
        return self._button_pressed.get(button, False)

    @property
    def is_left_dragging(self) -> bool:
        """左ボタンでドラッグ中か"""
        return self._button_pressed[MouseButton.LEFT]

    @property
    def is_right_dragging(self) -> bool:
        """右ボタンでドラッグ中か"""
        return self._button_pressed[MouseButton.RIGHT]

    @property
    def is_middle_dragging(self) -> bool:
        """中ボタンでドラッグ中か"""
        return self._button_pressed[MouseButton.MIDDLE]
