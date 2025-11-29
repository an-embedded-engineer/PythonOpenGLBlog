"""
変換行列管理モジュール

Model、View、Projection行列を管理し、座標変換を実行する
"""
import numpy as np
from src.utils.logger import logger


class Transform:
    """3D座標変換を管理するクラス"""

    def __init__(self) -> None:
        """変換を初期化する"""
        # Model行列（ローカル座標 → ワールド座標）
        self._model = np.eye(4, dtype=np.float32)

        # View行列（ワールド座標 → カメラ座標）
        # カメラ位置、視点、上ベクトル
        self._camera_pos = np.array([0.0, 0.0, 3.0], dtype=np.float32)
        self._camera_target = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        self._camera_up = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        self._view = self._look_at(self._camera_pos, self._camera_target, self._camera_up)

        # Projection行列（カメラ座標 → クリップ座標）
        # 透視投影パラメータ
        self._fov = 45.0  # 視野角（度）
        self._aspect = 800.0 / 600.0  # アスペクト比
        self._near = 0.1  # 近いクリップ面
        self._far = 100.0  # 遠いクリップ面
        self._projection = self._perspective(self._fov, self._aspect, self._near, self._far)

        logger.info("Transform initialized")

    # ===== Model行列 =====

    def set_model_identity(self) -> None:
        """Model行列を単位行列にリセット"""
        self._model = np.eye(4, dtype=np.float32)

    def translate_model(self, x: float, y: float, z: float) -> None:
        """Model行列に平行移動を適用"""
        translation = np.eye(4, dtype=np.float32)
        translation[0, 3] = x
        translation[1, 3] = y
        translation[2, 3] = z
        self._model = translation @ self._model

    def rotate_model_x(self, angle_deg: float) -> None:
        """Model行列にX軸回転を適用（度数法）"""
        angle_rad = np.radians(angle_deg)
        cos_a = np.cos(angle_rad)
        sin_a = np.sin(angle_rad)
        rotation = np.array([
            [1, 0, 0, 0],
            [0, cos_a, -sin_a, 0],
            [0, sin_a, cos_a, 0],
            [0, 0, 0, 1]
        ], dtype=np.float32)
        self._model = rotation @ self._model

    def rotate_model_y(self, angle_deg: float) -> None:
        """Model行列にY軸回転を適用（度数法）"""
        angle_rad = np.radians(angle_deg)
        cos_a = np.cos(angle_rad)
        sin_a = np.sin(angle_rad)
        rotation = np.array([
            [cos_a, 0, sin_a, 0],
            [0, 1, 0, 0],
            [-sin_a, 0, cos_a, 0],
            [0, 0, 0, 1]
        ], dtype=np.float32)
        self._model = rotation @ self._model

    def rotate_model_z(self, angle_deg: float) -> None:
        """Model行列にZ軸回転を適用（度数法）"""
        angle_rad = np.radians(angle_deg)
        cos_a = np.cos(angle_rad)
        sin_a = np.sin(angle_rad)
        rotation = np.array([
            [cos_a, -sin_a, 0, 0],
            [sin_a, cos_a, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ], dtype=np.float32)
        self._model = rotation @ self._model

    def scale_model(self, sx: float, sy: float, sz: float) -> None:
        """Model行列にスケーリングを適用"""
        scale = np.eye(4, dtype=np.float32)
        scale[0, 0] = sx
        scale[1, 1] = sy
        scale[2, 2] = sz
        self._model = scale @ self._model

    # ===== View行列 =====

    def set_camera_position(self, x: float, y: float, z: float) -> None:
        """カメラ位置を設定"""
        self._camera_pos = np.array([x, y, z], dtype=np.float32)
        self._update_view()

    def set_camera_target(self, x: float, y: float, z: float) -> None:
        """カメラの視点を設定"""
        self._camera_target = np.array([x, y, z], dtype=np.float32)
        self._update_view()

    def set_camera_up(self, x: float, y: float, z: float) -> None:
        """カメラの上ベクトルを設定"""
        self._camera_up = np.array([x, y, z], dtype=np.float32)
        self._update_view()

    def _update_view(self) -> None:
        """View行列を再計算"""
        self._view = self._look_at(self._camera_pos, self._camera_target, self._camera_up)

    def _look_at(self, eye: np.ndarray, target: np.ndarray, up: np.ndarray) -> np.ndarray:
        """
        Look At行列を計算（ビュー行列）

        Args:
            eye: カメラ位置
            target: 視点（カメラが見る点）
            up: 上ベクトル

        Returns:
            4x4のView行列
        """
        # 前方向ベクトル（正規化）
        forward = target - eye
        forward = forward / np.linalg.norm(forward)

        # 右ベクトル
        right = np.cross(forward, up)
        right = right / np.linalg.norm(right)

        # 新しい上ベクトル
        up_new = np.cross(right, forward)

        # View行列を構築
        view = np.eye(4, dtype=np.float32)
        view[0, 0:3] = right
        view[1, 0:3] = up_new
        view[2, 0:3] = -forward
        view[0, 3] = -np.dot(right, eye)
        view[1, 3] = -np.dot(up_new, eye)
        view[2, 3] = np.dot(forward, eye)

        return view

    # ===== Projection行列 =====

    def set_fov(self, fov_deg: float) -> None:
        """視野角を設定"""
        self._fov = fov_deg
        self._update_projection()

    def set_aspect(self, aspect: float) -> None:
        """アスペクト比を設定"""
        self._aspect = aspect
        self._update_projection()

    def set_near_far(self, near: float, far: float) -> None:
        """ニアクリップ面とファークリップ面を設定"""
        self._near = near
        self._far = far
        self._update_projection()

    def _update_projection(self) -> None:
        """Projection行列を再計算"""
        self._projection = self._perspective(self._fov, self._aspect, self._near, self._far)

    @staticmethod
    def _perspective(fov_deg: float, aspect: float, near: float, far: float) -> np.ndarray:
        """
        透視投影行列を計算

        Args:
            fov_deg: 視野角（度数法）
            aspect: アスペクト比（幅/高さ）
            near: ニアクリップ面距離
            far: ファークリップ面距離

        Returns:
            4x4のProjection行列
        """
        fov_rad = np.radians(fov_deg)
        f = 1.0 / np.tan(fov_rad / 2.0)

        projection = np.zeros((4, 4), dtype=np.float32)
        projection[0, 0] = f / aspect
        projection[1, 1] = f
        projection[2, 2] = (far + near) / (near - far)
        projection[2, 3] = (2 * far * near) / (near - far)
        projection[3, 2] = -1.0

        return projection

    # ===== 行列取得 =====

    @property
    def model(self) -> np.ndarray:
        """Model行列を取得"""
        return self._model

    @property
    def view(self) -> np.ndarray:
        """View行列を取得"""
        return self._view

    @property
    def projection(self) -> np.ndarray:
        """Projection行列を取得"""
        return self._projection

    @property
    def camera_pos(self) -> tuple[float, float, float]:
        """カメラ位置を取得"""
        return tuple(self._camera_pos)

    @property
    def camera_target(self) -> tuple[float, float, float]:
        """カメラの視点を取得"""
        return tuple(self._camera_target)

    @property
    def camera_up(self) -> tuple[float, float, float]:
        """カメラの上ベクトルを取得"""
        return tuple(self._camera_up)

    @property
    def fov(self) -> float:
        """視野角を取得"""
        return self._fov
