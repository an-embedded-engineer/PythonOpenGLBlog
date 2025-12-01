"""
カメラコントローラーモジュール
"""
import numpy as np
from typing import Union

from src.core.mouse_controller import MouseController, MouseButton
from src.graphics.camera import Camera2D, Camera3D, UpAxis
from src.utils.logger import logger


class CameraController:
    """
    マウス入力でカメラを操作するクラス

    操作方法:
    - 左ドラッグ: オービット（3Dカメラのみ）/ 回転（2Dカメラ）
    - 右ドラッグ: パン（平行移動）
    - 中ドラッグ: パン（平行移動）
    - ホイール: ズーム
    """

    def __init__(
        self,
        mouse: MouseController,
        camera_2d: Camera2D,
        camera_3d: Camera3D,
    ) -> None:
        """
        カメラコントローラーを初期化する

        Args:
            mouse: マウスコントローラー
            camera_2d: 2Dカメラ
            camera_3d: 3Dカメラ
        """
        self._mouse = mouse
        self._camera_2d = camera_2d
        self._camera_3d = camera_3d

        # 操作の感度
        self._orbit_sensitivity = 0.5      # オービット感度（度/ピクセル）
        self._pan_sensitivity = 0.01       # パン感度
        self._zoom_sensitivity = 0.1       # ズーム感度
        self._rotation_sensitivity = 0.5   # 2D回転感度（度/ピクセル）

        # imgui上でのマウス操作を無視するフラグ
        self._enabled = True

        logger.info("CameraController initialized")

    @property
    def orbit_sensitivity(self) -> float:
        """オービット感度を取得"""
        return self._orbit_sensitivity

    def set_orbit_sensitivity(self, value: float) -> None:
        """オービット感度を設定"""
        self._orbit_sensitivity = max(0.01, value)

    @property
    def pan_sensitivity(self) -> float:
        """パン感度を取得"""
        return self._pan_sensitivity

    def set_pan_sensitivity(self, value: float) -> None:
        """パン感度を設定"""
        self._pan_sensitivity = max(0.001, value)

    @property
    def zoom_sensitivity(self) -> float:
        """ズーム感度を取得"""
        return self._zoom_sensitivity

    def set_zoom_sensitivity(self, value: float) -> None:
        """ズーム感度を設定"""
        self._zoom_sensitivity = max(0.01, value)

    @property
    def enabled(self) -> bool:
        """カメラ操作が有効か"""
        return self._enabled

    def set_enabled(self, value: bool) -> None:
        """カメラ操作の有効/無効を設定"""
        self._enabled = value

    def update(self, use_3d_camera: bool) -> None:
        """
        カメラを更新する

        Args:
            use_3d_camera: 3Dカメラを使用中か
        """
        if not self._enabled:
            return

        # マウスの移動量とスクロール量を取得
        dx, dy = self._mouse.delta
        scroll_x, scroll_y = self._mouse.scroll

        if use_3d_camera:
            self._update_3d_camera(dx, dy, scroll_y)
        else:
            self._update_2d_camera(dx, dy, scroll_y)

    def _update_3d_camera(self, dx: float, dy: float, scroll: float) -> None:
        """3Dカメラを更新"""
        # 左ドラッグ: オービット（回転）
        if self._mouse.is_left_dragging:
            azimuth, elevation, distance = self._camera_3d.get_orbit()
            # 水平方向のドラッグで方位角を変更
            azimuth -= dx * self._orbit_sensitivity
            # 垂直方向のドラッグで仰角を変更（上下反転）
            elevation += dy * self._orbit_sensitivity
            # 仰角を-89〜89度にクランプ
            elevation = max(-89.0, min(89.0, elevation))
            self._camera_3d.set_orbit(azimuth, elevation, distance)

        # 右ドラッグ: パン（水平面での移動）
        if self._mouse.is_right_dragging:
            # カメラのView行列から右方向と前方向を取得
            view = self._camera_3d.view_matrix
            # View行列の1行目が右方向
            right = np.array([view[0, 0], view[0, 1], view[0, 2]], dtype=np.float32)
            # View行列の3行目の符号反転が前方向
            forward = np.array([-view[2, 0], -view[2, 1], -view[2, 2]], dtype=np.float32)

            # 上方向の軸に応じて水平面に投影
            if self._camera_3d.up_axis == UpAxis.Z_UP:
                # Z-up: XY平面に投影（Z成分を0にして正規化）
                right[2] = 0.0
                forward[2] = 0.0
            else:
                # Y-up: XZ平面に投影（Y成分を0にして正規化）
                right[1] = 0.0
                forward[1] = 0.0

            right_len = np.linalg.norm(right)
            if right_len > 0.001:
                right = right / right_len

            forward_len = np.linalg.norm(forward)
            if forward_len > 0.001:
                forward = forward / forward_len

            # スクリーン座標のドラッグをワールド座標の移動に変換
            # 左右ドラッグで左右移動、上下ドラッグで前後移動
            move: np.ndarray = -dx * self._pan_sensitivity * right - dy * self._pan_sensitivity * forward
            self._camera_3d.translate(float(move[0]), float(move[1]), float(move[2]))

        # 中ドラッグ: 高さ調整（上方向軸の移動）
        if self._mouse.is_middle_dragging:
            # 上下ドラッグで上方向軸に移動
            if self._camera_3d.up_axis == UpAxis.Z_UP:
                self._camera_3d.translate(0.0, 0.0, dy * self._pan_sensitivity)
            else:
                self._camera_3d.translate(0.0, dy * self._pan_sensitivity, 0.0)

        # ホイール: ズーム（距離を変更）
        if scroll != 0.0:
            azimuth, elevation, distance = self._camera_3d.get_orbit()
            distance -= scroll * self._zoom_sensitivity * distance * 0.1
            distance = max(0.5, min(100.0, distance))  # 距離をクランプ
            self._camera_3d.set_orbit(azimuth, elevation, distance)

    def _update_2d_camera(self, dx: float, dy: float, scroll: float) -> None:
        """2Dカメラを更新"""
        # 左ドラッグ: 回転
        if self._mouse.is_left_dragging:
            rotation = self._camera_2d.rotation
            rotation -= dx * self._rotation_sensitivity
            self._camera_2d.set_rotation(rotation)

        # 右ドラッグまたは中ドラッグ: パン（平行移動）
        if self._mouse.is_right_dragging or self._mouse.is_middle_dragging:
            pos_x, pos_y = self._camera_2d.position
            zoom = self._camera_2d.zoom

            # View行列から右方向と上方向を取得
            # View行列の1行目が右方向、2行目が上方向
            view = self._camera_2d.view_matrix
            right_x = view[0, 0]
            right_y = view[0, 1]
            up_x = view[1, 0]
            up_y = view[1, 1]

            # スクリーン座標のドラッグをワールド座標系に変換
            # マウスを右に動かす → カメラ位置を左に（-dx）
            # マウスを上に動かす → カメラ位置を上に（+dy）
            scale = self._pan_sensitivity / zoom
            move_x = (-dx * right_x + dy * up_x) * scale
            move_y = (-dx * right_y + dy * up_y) * scale

            self._camera_2d.set_position(pos_x + move_x, pos_y + move_y)

        # ホイール: ズーム
        if scroll != 0.0:
            zoom = self._camera_2d.zoom
            zoom *= 1.0 + scroll * self._zoom_sensitivity
            zoom = max(0.1, min(10.0, zoom))  # ズームをクランプ
            self._camera_2d.set_zoom(zoom)
