"""
カメラコントローラーモジュールのユニットテスト
"""
import pytest
from unittest.mock import MagicMock, PropertyMock

import numpy as np

from src.core.camera_controller import CameraController
from src.graphics.camera import UpAxis


class TestCameraController:
    """CameraControllerクラスのテスト"""

    @pytest.fixture
    def mock_mouse(self) -> MagicMock:
        """モックマウスコントローラーを作成"""
        mouse = MagicMock()
        mouse.delta = (0.0, 0.0)
        mouse.scroll = (0.0, 0.0)
        mouse.is_left_dragging = False
        mouse.is_right_dragging = False
        mouse.is_middle_dragging = False
        return mouse

    @pytest.fixture
    def mock_camera_2d(self) -> MagicMock:
        """モック2Dカメラを作成"""
        camera = MagicMock()
        camera.position = (0.0, 0.0)
        camera.zoom = 1.0
        camera.rotation = 0.0
        camera.view_matrix = np.eye(4, dtype=np.float32)
        return camera

    @pytest.fixture
    def mock_camera_3d(self) -> MagicMock:
        """モック3Dカメラを作成"""
        camera = MagicMock()
        camera.get_orbit.return_value = (0.0, 30.0, 5.0)  # azimuth, elevation, distance
        camera.view_matrix = np.eye(4, dtype=np.float32)
        camera.up_axis = UpAxis.Y_UP
        return camera

    @pytest.fixture
    def controller(
        self,
        mock_mouse: MagicMock,
        mock_camera_2d: MagicMock,
        mock_camera_3d: MagicMock
    ) -> CameraController:
        """CameraControllerインスタンスを作成"""
        return CameraController(mock_mouse, mock_camera_2d, mock_camera_3d)

    def test_init(self, controller: CameraController) -> None:
        """初期化のテスト"""
        assert controller.orbit_sensitivity == 0.5
        assert controller.pan_sensitivity == 0.01
        assert controller.zoom_sensitivity == 0.1
        assert controller.enabled is True

    def test_set_orbit_sensitivity(self, controller: CameraController) -> None:
        """オービット感度設定のテスト"""
        controller.set_orbit_sensitivity(1.0)
        assert controller.orbit_sensitivity == 1.0

        # 最小値クランプ
        controller.set_orbit_sensitivity(0.0)
        assert controller.orbit_sensitivity == 0.01

    def test_set_pan_sensitivity(self, controller: CameraController) -> None:
        """パン感度設定のテスト"""
        controller.set_pan_sensitivity(0.05)
        assert controller.pan_sensitivity == 0.05

        # 最小値クランプ
        controller.set_pan_sensitivity(0.0)
        assert controller.pan_sensitivity == 0.001

    def test_set_zoom_sensitivity(self, controller: CameraController) -> None:
        """ズーム感度設定のテスト"""
        controller.set_zoom_sensitivity(0.5)
        assert controller.zoom_sensitivity == 0.5

        # 最小値クランプ
        controller.set_zoom_sensitivity(0.0)
        assert controller.zoom_sensitivity == 0.01

    def test_set_enabled(self, controller: CameraController) -> None:
        """有効/無効設定のテスト"""
        controller.set_enabled(False)
        assert controller.enabled is False

        controller.set_enabled(True)
        assert controller.enabled is True

    def test_update_disabled(
        self,
        controller: CameraController,
        mock_mouse: MagicMock,
        mock_camera_3d: MagicMock
    ) -> None:
        """無効時の更新テスト"""
        mock_mouse.delta = (10.0, 10.0)
        mock_mouse.is_left_dragging = True

        controller.set_enabled(False)
        controller.update(use_3d_camera=True)

        # カメラが更新されないことを確認
        mock_camera_3d.set_orbit.assert_not_called()

    def test_3d_orbit(
        self,
        controller: CameraController,
        mock_mouse: MagicMock,
        mock_camera_3d: MagicMock
    ) -> None:
        """3Dオービットのテスト"""
        mock_mouse.delta = (10.0, 5.0)
        mock_mouse.is_left_dragging = True

        controller.update(use_3d_camera=True)

        mock_camera_3d.set_orbit.assert_called_once()
        args = mock_camera_3d.set_orbit.call_args[0]
        # azimuth: 0 - 10*0.5 = -5
        # elevation: 30 + 5*0.5 = 32.5
        # distance: 5 (変更なし)
        assert args[0] == pytest.approx(-5.0)
        assert args[1] == pytest.approx(32.5)
        assert args[2] == pytest.approx(5.0)

    def test_3d_orbit_elevation_clamp(
        self,
        controller: CameraController,
        mock_mouse: MagicMock,
        mock_camera_3d: MagicMock
    ) -> None:
        """3Dオービット仰角クランプのテスト"""
        mock_camera_3d.get_orbit.return_value = (0.0, 85.0, 5.0)
        mock_mouse.delta = (0.0, 20.0)  # 大きく上にドラッグ
        mock_mouse.is_left_dragging = True

        controller.update(use_3d_camera=True)

        args = mock_camera_3d.set_orbit.call_args[0]
        # elevation: 85 + 20*0.5 = 95 → 89にクランプ
        assert args[1] == pytest.approx(89.0)

    def test_3d_zoom(
        self,
        controller: CameraController,
        mock_mouse: MagicMock,
        mock_camera_3d: MagicMock
    ) -> None:
        """3Dズームのテスト"""
        mock_mouse.scroll = (0.0, 1.0)

        controller.update(use_3d_camera=True)

        mock_camera_3d.set_orbit.assert_called_once()
        args = mock_camera_3d.set_orbit.call_args[0]
        # distance: 5 - 1*0.1*5*0.1 = 4.95
        assert args[2] == pytest.approx(4.95)

    def test_3d_height_y_up(
        self,
        controller: CameraController,
        mock_mouse: MagicMock,
        mock_camera_3d: MagicMock
    ) -> None:
        """3D高さ調整（Y-up）のテスト"""
        mock_mouse.delta = (0.0, 10.0)
        mock_mouse.is_middle_dragging = True
        mock_camera_3d.up_axis = UpAxis.Y_UP

        controller.update(use_3d_camera=True)

        mock_camera_3d.translate.assert_called_once()
        args = mock_camera_3d.translate.call_args[0]
        # Y軸方向に移動: (0, dy*pan_sensitivity, 0)
        assert args[0] == pytest.approx(0.0)
        assert args[1] == pytest.approx(0.1)  # 10 * 0.01
        assert args[2] == pytest.approx(0.0)

    def test_3d_height_z_up(
        self,
        controller: CameraController,
        mock_mouse: MagicMock,
        mock_camera_3d: MagicMock
    ) -> None:
        """3D高さ調整（Z-up）のテスト"""
        mock_mouse.delta = (0.0, 10.0)
        mock_mouse.is_middle_dragging = True
        mock_camera_3d.up_axis = UpAxis.Z_UP

        controller.update(use_3d_camera=True)

        mock_camera_3d.translate.assert_called_once()
        args = mock_camera_3d.translate.call_args[0]
        # Z軸方向に移動: (0, 0, dy*pan_sensitivity)
        assert args[0] == pytest.approx(0.0)
        assert args[1] == pytest.approx(0.0)
        assert args[2] == pytest.approx(0.1)  # 10 * 0.01

    def test_2d_rotation(
        self,
        controller: CameraController,
        mock_mouse: MagicMock,
        mock_camera_2d: MagicMock
    ) -> None:
        """2D回転のテスト"""
        mock_mouse.delta = (10.0, 0.0)
        mock_mouse.is_left_dragging = True

        controller.update(use_3d_camera=False)

        mock_camera_2d.set_rotation.assert_called_once()
        args = mock_camera_2d.set_rotation.call_args[0]
        # rotation: 0 - 10*0.5 = -5
        assert args[0] == pytest.approx(-5.0)

    def test_2d_zoom(
        self,
        controller: CameraController,
        mock_mouse: MagicMock,
        mock_camera_2d: MagicMock
    ) -> None:
        """2Dズームのテスト"""
        mock_mouse.scroll = (0.0, 1.0)

        controller.update(use_3d_camera=False)

        mock_camera_2d.set_zoom.assert_called_once()
        args = mock_camera_2d.set_zoom.call_args[0]
        # zoom: 1 * (1 + 1*0.1) = 1.1
        assert args[0] == pytest.approx(1.1)

    def test_2d_pan(
        self,
        controller: CameraController,
        mock_mouse: MagicMock,
        mock_camera_2d: MagicMock
    ) -> None:
        """2Dパンのテスト（回転なし）"""
        mock_mouse.delta = (10.0, 5.0)
        mock_mouse.is_right_dragging = True
        mock_camera_2d.view_matrix = np.eye(4, dtype=np.float32)

        controller.update(use_3d_camera=False)

        mock_camera_2d.set_position.assert_called_once()
        args = mock_camera_2d.set_position.call_args[0]
        # 回転なしなので、dx方向に-0.1、dy方向に+0.05
        assert args[0] == pytest.approx(-0.1)  # -dx * 0.01
        assert args[1] == pytest.approx(0.05)  # dy * 0.01
