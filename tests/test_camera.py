"""
カメラモジュールのユニットテスト
"""
import math

import numpy as np
import pytest

from src.graphics.camera import Camera2D, Camera3D, CameraBase, CameraMode


class TestCamera2D:
    """Camera2Dクラスのテスト"""

    def test_init_default(self) -> None:
        """デフォルト初期化のテスト"""
        camera = Camera2D()
        assert camera.mode == CameraMode.CAMERA_2D
        assert camera.position == (0.0, 0.0)
        assert camera.zoom == 1.0
        assert camera.rotation == 0.0
        assert camera.near == -10.0
        assert camera.far == 10.0

    def test_init_custom_size(self) -> None:
        """カスタムサイズでの初期化テスト"""
        camera = Camera2D(width=1920, height=1080)
        assert camera.aspect == pytest.approx(1920 / 1080)

    def test_set_position(self) -> None:
        """位置設定のテスト"""
        camera = Camera2D()
        camera.set_position(1.5, -2.0)
        assert camera.position == (1.5, -2.0)

    def test_set_zoom(self) -> None:
        """ズーム設定のテスト"""
        camera = Camera2D()
        camera.set_zoom(2.0)
        assert camera.zoom == 2.0

    def test_set_zoom_minimum(self) -> None:
        """ズーム最小値のテスト"""
        camera = Camera2D()
        camera.set_zoom(0.0)  # 0はクランプされる
        assert camera.zoom == 0.01

    def test_set_rotation(self) -> None:
        """回転設定のテスト"""
        camera = Camera2D()
        camera.set_rotation(45.0)
        assert camera.rotation == 45.0

    def test_set_rotation_normalization(self) -> None:
        """回転角度の正規化テスト"""
        camera = Camera2D()
        camera.set_rotation(400.0)  # 360を超える
        assert camera.rotation == pytest.approx(40.0)
        camera.set_rotation(-30.0)  # 負の値
        assert camera.rotation == pytest.approx(330.0)

    def test_set_clip_planes(self) -> None:
        """クリップ面設定のテスト"""
        camera = Camera2D()
        camera.set_clip_planes(-100.0, 100.0)
        assert camera.near == -100.0
        assert camera.far == 100.0

    def test_reset(self) -> None:
        """リセットのテスト"""
        camera = Camera2D()
        camera.set_position(5.0, 5.0)
        camera.set_zoom(3.0)
        camera.set_rotation(90.0)
        camera.reset()
        assert camera.position == (0.0, 0.0)
        assert camera.zoom == 1.0
        assert camera.rotation == 0.0

    def test_view_matrix_identity_at_default(self) -> None:
        """デフォルト状態でのView行列テスト"""
        camera = Camera2D()
        view = camera.view_matrix
        # 回転0、オフセット0なので単位行列に近い
        assert view.shape == (4, 4)
        assert view[0, 0] == pytest.approx(1.0)
        assert view[1, 1] == pytest.approx(1.0)
        assert view[0, 3] == pytest.approx(0.0)
        assert view[1, 3] == pytest.approx(0.0)

    def test_view_matrix_with_position(self) -> None:
        """位置オフセット時のView行列テスト"""
        camera = Camera2D()
        camera.set_position(2.0, 3.0)
        view = camera.view_matrix
        # 平行移動部分が負のオフセット
        assert view[0, 3] == pytest.approx(-2.0)
        assert view[1, 3] == pytest.approx(-3.0)

    def test_view_matrix_with_rotation(self) -> None:
        """回転時のView行列テスト"""
        camera = Camera2D()
        camera.set_rotation(90.0)
        view = camera.view_matrix
        # 90度回転: cos(90)=0, sin(90)=1
        assert view[0, 0] == pytest.approx(0.0, abs=1e-6)
        assert view[0, 1] == pytest.approx(1.0)
        assert view[1, 0] == pytest.approx(-1.0)
        assert view[1, 1] == pytest.approx(0.0, abs=1e-6)

    def test_projection_matrix_shape(self) -> None:
        """Projection行列の形状テスト"""
        camera = Camera2D()
        proj = camera.projection_matrix
        assert proj.shape == (4, 4)
        assert proj.dtype == np.float32

    def test_set_viewport(self) -> None:
        """ビューポート変更のテスト"""
        camera = Camera2D(800, 600)
        camera.set_viewport(1920, 1080)
        assert camera.aspect == pytest.approx(1920 / 1080)


class TestCamera3D:
    """Camera3Dクラスのテスト"""

    def test_init_default(self) -> None:
        """デフォルト初期化のテスト"""
        camera = Camera3D()
        assert camera.mode == CameraMode.CAMERA_3D
        assert camera.position == (0.0, 0.0, 5.0)
        assert camera.target == (0.0, 0.0, 0.0)
        assert camera.up == (0.0, 1.0, 0.0)
        assert camera.fov == 45.0
        assert camera.near == 0.1
        assert camera.far == 100.0

    def test_init_custom_size(self) -> None:
        """カスタムサイズでの初期化テスト"""
        camera = Camera3D(width=1920, height=1080)
        assert camera.aspect == pytest.approx(1920 / 1080)

    def test_set_position(self) -> None:
        """位置設定のテスト"""
        camera = Camera3D()
        camera.set_position(1.0, 2.0, 3.0)
        assert camera.position == (1.0, 2.0, 3.0)

    def test_set_target(self) -> None:
        """視点設定のテスト"""
        camera = Camera3D()
        camera.set_target(1.0, 1.0, 1.0)
        assert camera.target == (1.0, 1.0, 1.0)

    def test_set_up(self) -> None:
        """上ベクトル設定のテスト"""
        camera = Camera3D()
        camera.set_up(0.0, 0.0, 1.0)
        assert camera.up == (0.0, 0.0, 1.0)

    def test_set_fov(self) -> None:
        """視野角設定のテスト"""
        camera = Camera3D()
        camera.set_fov(60.0)
        assert camera.fov == 60.0

    def test_set_fov_clamping(self) -> None:
        """視野角クランプのテスト"""
        camera = Camera3D()
        camera.set_fov(0.0)
        assert camera.fov == 1.0  # 最小値
        camera.set_fov(200.0)
        assert camera.fov == 179.0  # 最大値

    def test_set_clip_planes(self) -> None:
        """クリップ面設定のテスト"""
        camera = Camera3D()
        camera.set_clip_planes(0.5, 500.0)
        assert camera.near == 0.5
        assert camera.far == 500.0

    def test_translate(self) -> None:
        """平行移動のテスト"""
        camera = Camera3D()
        initial_pos = camera.position
        initial_target = camera.target
        camera.translate(1.0, 2.0, 3.0)
        assert camera.position == (initial_pos[0] + 1.0, initial_pos[1] + 2.0, initial_pos[2] + 3.0)
        assert camera.target == (initial_target[0] + 1.0, initial_target[1] + 2.0, initial_target[2] + 3.0)

    def test_set_pan(self) -> None:
        """パン設定のテスト"""
        camera = Camera3D()
        camera.set_pan(1.0, 2.0, 3.0)
        # デフォルト位置(0,0,5) + オフセット(1,2,3)
        assert camera.position == (1.0, 2.0, 8.0)
        # デフォルト視点(0,0,0) + オフセット(1,2,3)
        assert camera.target == (1.0, 2.0, 3.0)

    def test_pan_property(self) -> None:
        """panプロパティのテスト"""
        camera = Camera3D()
        camera.set_pan(1.0, 2.0, 3.0)
        assert camera.pan == (1.0, 2.0, 3.0)

    def test_set_orbit(self) -> None:
        """オービット設定のテスト"""
        camera = Camera3D()
        camera.set_orbit(0.0, 0.0, 5.0)
        # azimuth=0, elevation=0 → Z軸正方向に5
        assert camera.position[0] == pytest.approx(0.0, abs=1e-5)
        assert camera.position[1] == pytest.approx(0.0, abs=1e-5)
        assert camera.position[2] == pytest.approx(5.0)

    def test_set_orbit_azimuth_90(self) -> None:
        """オービット（方位角90度）のテスト"""
        camera = Camera3D()
        camera.set_orbit(90.0, 0.0, 5.0)
        # azimuth=90 → X軸正方向に5
        assert camera.position[0] == pytest.approx(5.0)
        assert camera.position[1] == pytest.approx(0.0, abs=1e-5)
        assert camera.position[2] == pytest.approx(0.0, abs=1e-5)

    def test_set_orbit_elevation_90(self) -> None:
        """オービット（仰角90度）のテスト"""
        camera = Camera3D()
        camera.set_orbit(0.0, 90.0, 5.0)
        # elevation=90 → Y軸正方向（真上）に5
        assert camera.position[0] == pytest.approx(0.0, abs=1e-5)
        assert camera.position[1] == pytest.approx(5.0)
        assert camera.position[2] == pytest.approx(0.0, abs=1e-5)

    def test_get_orbit(self) -> None:
        """オービット取得のテスト"""
        camera = Camera3D()
        camera.set_orbit(45.0, 30.0, 10.0)
        azimuth, elevation, distance = camera.get_orbit()
        assert azimuth == pytest.approx(45.0, abs=0.1)
        assert elevation == pytest.approx(30.0, abs=0.1)
        assert distance == pytest.approx(10.0, abs=0.1)

    def test_distance_property(self) -> None:
        """距離プロパティのテスト"""
        camera = Camera3D()
        # デフォルト: position=(0,0,5), target=(0,0,0) → distance=5
        assert camera.distance == pytest.approx(5.0)

    def test_set_distance(self) -> None:
        """距離設定のテスト"""
        camera = Camera3D()
        camera.set_distance(10.0)
        assert camera.distance == pytest.approx(10.0)

    def test_reset(self) -> None:
        """リセットのテスト"""
        camera = Camera3D()
        camera.set_position(10.0, 10.0, 10.0)
        camera.set_target(5.0, 5.0, 5.0)
        camera.set_fov(90.0)
        camera.reset()
        assert camera.position == (0.0, 0.0, 5.0)
        assert camera.target == (0.0, 0.0, 0.0)
        assert camera.fov == 45.0

    def test_view_matrix_shape(self) -> None:
        """View行列の形状テスト"""
        camera = Camera3D()
        view = camera.view_matrix
        assert view.shape == (4, 4)
        assert view.dtype == np.float32

    def test_view_matrix_look_at(self) -> None:
        """Look At行列のテスト"""
        camera = Camera3D()
        view = camera.view_matrix
        # View行列の最後の行は [0, 0, 0, 1] ではなく [0, 0, -1, 0]（透視投影の-z軸）
        # ただし標準的なLook At行列では最後の行は[0, 0, 0, 1]
        assert view[3, 3] == pytest.approx(1.0)
        # 行列が正しく計算されていることを確認
        # デフォルト: eye=(0,0,5), target=(0,0,0) なので前方向は-Z

    def test_projection_matrix_shape(self) -> None:
        """Projection行列の形状テスト"""
        camera = Camera3D()
        proj = camera.projection_matrix
        assert proj.shape == (4, 4)
        assert proj.dtype == np.float32

    def test_projection_matrix_perspective(self) -> None:
        """透視投影行列のテスト"""
        camera = Camera3D()
        proj = camera.projection_matrix
        # [3,2]が-1なら透視投影
        assert proj[3, 2] == pytest.approx(-1.0)

    def test_set_viewport(self) -> None:
        """ビューポート変更のテスト"""
        camera = Camera3D(800, 600)
        camera.set_viewport(1920, 1080)
        assert camera.aspect == pytest.approx(1920 / 1080)


class TestCameraMode:
    """CameraModeのテスト"""

    def test_camera_mode_values(self) -> None:
        """カメラモード値のテスト"""
        assert CameraMode.CAMERA_2D.value == 0
        assert CameraMode.CAMERA_3D.value == 1
