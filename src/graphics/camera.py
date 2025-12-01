"""
カメラモジュール

2D/3Dカメラの基底クラスと派生クラスを提供
"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import Tuple, Union

import numpy as np

from src.utils.logger import logger


class CameraMode(Enum):
    """カメラモード"""
    CAMERA_2D = 0  # 正射影（2D）
    CAMERA_3D = 1  # 透視投影（3D）


class CameraBase(ABC):
    """
    カメラの基底クラス

    View行列とProjection行列を提供する抽象クラス
    """

    def __init__(self, width: int = 800, height: int = 600) -> None:
        """
        カメラを初期化する

        Args:
            width: ビューポートの幅
            height: ビューポートの高さ
        """
        self._width = width
        self._height = height
        self._aspect = width / height if height > 0 else 1.0

        # 行列のキャッシュ
        self._view_matrix = np.eye(4, dtype=np.float32)
        self._projection_matrix = np.eye(4, dtype=np.float32)

    @property
    @abstractmethod
    def mode(self) -> CameraMode:
        """カメラモードを取得"""
        pass

    @property
    def view_matrix(self) -> np.ndarray:
        """View行列を取得"""
        return self._view_matrix

    @property
    def projection_matrix(self) -> np.ndarray:
        """Projection行列を取得"""
        return self._projection_matrix

    @property
    def aspect(self) -> float:
        """アスペクト比を取得"""
        return self._aspect

    def set_viewport(self, width: int, height: int) -> None:
        """ビューポートサイズを設定"""
        self._width = width
        self._height = height
        self._aspect = width / height if height > 0 else 1.0
        self._update_projection_matrix()

    @abstractmethod
    def reset(self) -> None:
        """カメラをデフォルト状態にリセット"""
        pass

    @abstractmethod
    def _update_view_matrix(self) -> None:
        """View行列を更新"""
        pass

    @abstractmethod
    def _update_projection_matrix(self) -> None:
        """Projection行列を更新"""
        pass


class Camera2D(CameraBase):
    """
    2Dカメラクラス

    正射影（Orthographic Projection）を使用
    """

    def __init__(self, width: int = 800, height: int = 600) -> None:
        """
        2Dカメラを初期化する

        Args:
            width: ビューポートの幅
            height: ビューポートの高さ
        """
        super().__init__(width, height)

        # カメラ位置（XY平面上のオフセット）
        self._position_x = 0.0
        self._position_y = 0.0

        # ズーム倍率
        self._zoom = 1.0

        # 回転角度（度）
        self._rotation = 0.0

        # クリップ面
        self._near = -10.0
        self._far = 10.0

        # 初期行列を計算
        self._update_view_matrix()
        self._update_projection_matrix()

        logger.info("Camera2D initialized")

    @property
    def mode(self) -> CameraMode:
        """カメラモードを取得"""
        return CameraMode.CAMERA_2D

    @property
    def position(self) -> Tuple[float, float]:
        """カメラ位置を取得"""
        return (self._position_x, self._position_y)

    def set_position(self, x: float, y: float) -> None:
        """カメラ位置を設定"""
        self._position_x = x
        self._position_y = y
        self._update_view_matrix()

    @property
    def zoom(self) -> float:
        """ズーム倍率を取得"""
        return self._zoom

    def set_zoom(self, zoom: float) -> None:
        """ズーム倍率を設定"""
        self._zoom = max(0.01, zoom)  # 最小値0.01にクランプ
        self._update_projection_matrix()

    @property
    def rotation(self) -> float:
        """回転角度を取得(度)"""
        return self._rotation

    def set_rotation(self, rotation: float) -> None:
        """回転角度を設定(度)"""
        self._rotation = rotation % 360.0  # 0〜360度に正規化
        self._update_view_matrix()

    @property
    def near(self) -> float:
        """ニアクリップ面を取得"""
        return self._near

    @property
    def far(self) -> float:
        """ファークリップ面を取得"""
        return self._far

    def set_clip_planes(self, near: float, far: float) -> None:
        """クリップ面を設定"""
        self._near = near
        self._far = far
        self._update_projection_matrix()

    def reset(self) -> None:
        """カメラをデフォルト状態にリセット"""
        self._position_x = 0.0
        self._position_y = 0.0
        self._zoom = 1.0
        self._rotation = 0.0
        self._update_view_matrix()
        self._update_projection_matrix()
        logger.info("Camera2D reset to default")

    def _update_view_matrix(self) -> None:
        """View行列を更新"""
        # 回転行列を計算
        angle_rad = np.radians(self._rotation)
        cos_a = np.cos(angle_rad)
        sin_a = np.sin(angle_rad)

        # View行列 = 回転 * 平行移動
        self._view_matrix = np.eye(4, dtype=np.float32)
        # 回転部分
        self._view_matrix[0, 0] = cos_a
        self._view_matrix[0, 1] = sin_a
        self._view_matrix[1, 0] = -sin_a
        self._view_matrix[1, 1] = cos_a
        # 平行移動部分（回転後の座標系で適用）
        self._view_matrix[0, 3] = -(cos_a * self._position_x + sin_a * self._position_y)
        self._view_matrix[1, 3] = -(-sin_a * self._position_x + cos_a * self._position_y)

    def _update_projection_matrix(self) -> None:
        """Projection行列を更新（正射影）"""
        # ズームを適用した表示範囲
        half_width = self._aspect / self._zoom
        half_height = 1.0 / self._zoom

        left = -half_width
        right = half_width
        bottom = -half_height
        top = half_height

        # 正射影行列
        self._projection_matrix = np.zeros((4, 4), dtype=np.float32)
        self._projection_matrix[0, 0] = 2.0 / (right - left)
        self._projection_matrix[1, 1] = 2.0 / (top - bottom)
        self._projection_matrix[2, 2] = -2.0 / (self._far - self._near)
        self._projection_matrix[0, 3] = -(right + left) / (right - left)
        self._projection_matrix[1, 3] = -(top + bottom) / (top - bottom)
        self._projection_matrix[2, 3] = -(self._far + self._near) / (self._far - self._near)
        self._projection_matrix[3, 3] = 1.0


class Camera3D(CameraBase):
    """
    3Dカメラクラス

    透視投影（Perspective Projection）を使用
    """

    def __init__(self, width: int = 800, height: int = 600) -> None:
        """
        3Dカメラを初期化する

        Args:
            width: ビューポートの幅
            height: ビューポートの高さ
        """
        super().__init__(width, height)

        # カメラ位置
        self._position = np.array([0.0, 0.0, 5.0], dtype=np.float32)
        # カメラの視点（見る点）
        self._target = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        # 上ベクトル
        self._up = np.array([0.0, 1.0, 0.0], dtype=np.float32)

        # 透視投影パラメータ
        self._fov = 45.0  # 視野角（度）
        self._near = 0.1  # ニアクリップ面
        self._far = 100.0  # ファークリップ面

        # 初期行列を計算
        self._update_view_matrix()
        self._update_projection_matrix()

        logger.info("Camera3D initialized")

    @property
    def mode(self) -> CameraMode:
        """カメラモードを取得"""
        return CameraMode.CAMERA_3D

    @property
    def position(self) -> Tuple[float, float, float]:
        """カメラ位置を取得"""
        return tuple(self._position)

    def set_position(self, x: float, y: float, z: float) -> None:
        """カメラ位置を設定"""
        self._position = np.array([x, y, z], dtype=np.float32)
        self._update_view_matrix()

    @property
    def target(self) -> Tuple[float, float, float]:
        """カメラの視点を取得"""
        return tuple(self._target)

    def set_target(self, x: float, y: float, z: float) -> None:
        """カメラの視点を設定"""
        self._target = np.array([x, y, z], dtype=np.float32)
        self._update_view_matrix()

    @property
    def up(self) -> Tuple[float, float, float]:
        """上ベクトルを取得"""
        return tuple(self._up)

    def set_up(self, x: float, y: float, z: float) -> None:
        """上ベクトルを設定"""
        self._up = np.array([x, y, z], dtype=np.float32)
        self._update_view_matrix()

    @property
    def fov(self) -> float:
        """視野角を取得（度）"""
        return self._fov

    def set_fov(self, fov: float) -> None:
        """視野角を設定（度）"""
        self._fov = max(1.0, min(179.0, fov))  # 1〜179度にクランプ
        self._update_projection_matrix()

    @property
    def near(self) -> float:
        """ニアクリップ面を取得"""
        return self._near

    @property
    def far(self) -> float:
        """ファークリップ面を取得"""
        return self._far

    def set_clip_planes(self, near: float, far: float) -> None:
        """クリップ面を設定"""
        self._near = near
        self._far = far
        self._update_projection_matrix()

    def translate(self, dx: float, dy: float, dz: float) -> None:
        """
        カメラを平行移動する

        カメラ位置と視点を同時に移動させることで、
        見ている方向を維持したままパン（平行移動）する

        Args:
            dx: X方向の移動量
            dy: Y方向の移動量
            dz: Z方向の移動量
        """
        delta = np.array([dx, dy, dz], dtype=np.float32)
        self._position = self._position + delta
        self._target = self._target + delta
        self._update_view_matrix()

    def set_pan(self, x: float, y: float, z: float) -> None:
        """
        カメラのパン位置を設定

        カメラ位置と視点の両方にオフセットを適用
        デフォルト位置からの平行移動を設定

        Args:
            x: X方向のオフセット
            y: Y方向のオフセット
            z: Z方向のオフセット
        """
        # デフォルトのカメラ位置と視点にオフセットを加算
        default_pos = np.array([0.0, 0.0, 5.0], dtype=np.float32)
        default_target = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        offset = np.array([x, y, z], dtype=np.float32)

        self._position = default_pos + offset
        self._target = default_target + offset
        self._update_view_matrix()

    @property
    def pan(self) -> Tuple[float, float, float]:
        """
        現在のパンオフセットを取得

        視点（target）の位置をパンオフセットとして返す
        """
        return tuple(self._target)

    def set_orbit(self, azimuth: float, elevation: float, distance: float) -> None:
        """
        オービット（球面座標）でカメラ位置を設定

        視点（target）を中心とした球面上にカメラを配置
        マウスドラッグでの回転操作のベースとなる

        Args:
            azimuth: 方位角（水平回転、度）0=正面、90=右、-90=左
            elevation: 仰角（垂直回転、度）0=水平、90=真上、-90=真下
            distance: 視点からの距離
        """
        # 度からラジアンに変換
        azimuth_rad = np.radians(azimuth)
        elevation_rad = np.radians(elevation)

        # 球面座標からカメラ位置を計算
        # Y-up座標系: X=右、Y=上、Z=手前
        x = distance * np.cos(elevation_rad) * np.sin(azimuth_rad)
        y = distance * np.sin(elevation_rad)
        z = distance * np.cos(elevation_rad) * np.cos(azimuth_rad)

        # カメラ位置を更新（視点からの相対位置）
        self._position = self._target + np.array([x, y, z], dtype=np.float32)
        self._update_view_matrix()

    def get_orbit(self) -> Tuple[float, float, float]:
        """
        現在のオービットパラメータを取得

        Returns:
            (azimuth, elevation, distance): 方位角、仰角、距離
        """
        # カメラ位置から視点への相対ベクトル
        rel = self._position - self._target
        distance = float(np.linalg.norm(rel))

        if distance < 0.001:
            return (0.0, 0.0, distance)

        # 正規化
        rel_norm = rel / distance

        # 仰角（Y成分から）
        elevation = np.degrees(np.arcsin(np.clip(rel_norm[1], -1.0, 1.0)))

        # 方位角（XZ平面上の角度）
        azimuth = np.degrees(np.arctan2(rel_norm[0], rel_norm[2]))

        return (float(azimuth), float(elevation), distance)

    @property
    def distance(self) -> float:
        """視点からカメラまでの距離を取得"""
        return float(np.linalg.norm(self._position - self._target))

    def set_distance(self, distance: float) -> None:
        """
        視点からカメラまでの距離を設定

        カメラの方向は維持したまま、距離のみを変更

        Args:
            distance: 新しい距離
        """
        # 現在の方向ベクトル
        direction = self._position - self._target
        dir_len = np.linalg.norm(direction)

        if dir_len > 0.001:
            direction = direction / dir_len
        else:
            direction = np.array([0.0, 0.0, 1.0], dtype=np.float32)

        # 新しい距離で位置を計算
        self._position = self._target + direction * distance
        self._update_view_matrix()

    def reset(self) -> None:
        """カメラをデフォルト状態にリセット"""
        self._position = np.array([0.0, 0.0, 5.0], dtype=np.float32)
        self._target = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        self._up = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        self._fov = 45.0
        self._update_view_matrix()
        self._update_projection_matrix()
        logger.info("Camera3D reset to default")

    def _update_view_matrix(self) -> None:
        """View行列を更新（Look At行列）"""
        eye = self._position
        target = self._target
        up = self._up

        # 前方向ベクトル（正規化）
        forward = target - eye
        forward_len = np.linalg.norm(forward)
        if forward_len > 0:
            forward = forward / forward_len

        # 右ベクトル
        right = np.cross(forward, up)
        right_len = np.linalg.norm(right)
        if right_len > 0:
            right = right / right_len

        # 新しい上ベクトル
        up_new = np.cross(right, forward)

        # View行列を構築
        self._view_matrix = np.eye(4, dtype=np.float32)
        self._view_matrix[0, 0:3] = right
        self._view_matrix[1, 0:3] = up_new
        self._view_matrix[2, 0:3] = -forward
        self._view_matrix[0, 3] = -np.dot(right, eye)
        self._view_matrix[1, 3] = -np.dot(up_new, eye)
        self._view_matrix[2, 3] = np.dot(forward, eye)

    def _update_projection_matrix(self) -> None:
        """Projection行列を更新（透視投影）"""
        fov_rad = np.radians(self._fov)
        f = 1.0 / np.tan(fov_rad / 2.0)

        self._projection_matrix = np.zeros((4, 4), dtype=np.float32)
        self._projection_matrix[0, 0] = f / self._aspect
        self._projection_matrix[1, 1] = f
        self._projection_matrix[2, 2] = (self._far + self._near) / (self._near - self._far)
        self._projection_matrix[2, 3] = (2.0 * self._far * self._near) / (self._near - self._far)
        self._projection_matrix[3, 2] = -1.0


# 型エイリアス
Camera = Union[Camera2D, Camera3D]
