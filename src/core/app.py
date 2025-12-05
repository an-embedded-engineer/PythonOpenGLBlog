"""
アプリケーションモジュール
"""
from pathlib import Path

import numpy as np
from imgui_bundle import imgui
import OpenGL.GL as gl

from src.core.window import Window
from src.core.gui import GUI
from src.core.mouse_controller import MouseController
from src.core.camera_controller import CameraController
from src.graphics import (
    Shader, Camera2D, Camera3D, CameraMode, UpAxis,
    PointGeometry, LineGeometry, TriangleGeometry,
)
from src.graphics.transform import Transform
from src.utils.logger import logger


class App:
    """アプリケーションクラス"""

    # シェーダーファイルのディレクトリ
    SHADER_DIR = Path(__file__).parent.parent / "shaders"

    def __init__(self) -> None:
        """アプリケーションを初期化する"""
        logger.debug("App.__init__ start")
        self._window = Window(800, 600, "PythonOpenGL")
        self._gui = GUI(self._window)

        # GUI初期化後にキーコールバックを設定（GlfwRendererが上書きするため）
        self._window.setup_key_callback()

        # 背景色（RGBA、0.0〜1.0）
        self._clear_color = [0.2, 0.2, 0.2, 1.0]

        # カメラ（2D/3D切り替え対応）
        self._camera_2d = Camera2D(800, 600)
        self._camera_3d = Camera3D(800, 600)
        self._use_3d_camera = True  # 3Dカメラを使用

        # マウスコントローラー（GUI初期化後に作成）
        self._mouse = MouseController(self._window.handle)

        # カメラコントローラー
        self._camera_controller = CameraController(
            self._mouse,
            self._camera_2d,
            self._camera_3d,
        )

        # 座標変換（Model行列用）
        self._transform = Transform()

        # Model行列の回転パラメータ（imguiで調整可能）
        self._rotation_x = 0.0
        self._rotation_y = 0.0
        self._rotation_z = 0.0

        # シェーダーの初期化
        self._shader: Shader | None = None
        self._setup_shader()

        # ジオメトリの初期化（点・線・三角形）
        self._point_geometry: PointGeometry | None = None
        self._line_geometry: LineGeometry | None = None
        self._triangle_geometry: TriangleGeometry | None = None
        self._setup_geometries()

        # 表示する形状の選択（0: 点, 1: 線, 2: 三角形, 3: すべて）
        self._geometry_mode = 3

        logger.debug("App.__init__ end")

    def _setup_shader(self) -> None:
        """シェーダーをセットアップする"""
        vertex_path = self.SHADER_DIR / "basic.vert"
        fragment_path = self.SHADER_DIR / "basic.frag"
        self._shader = Shader(vertex_path, fragment_path)

    def _setup_geometries(self) -> None:
        """ジオメトリをセットアップする"""
        # === 点ジオメトリ ===
        self._point_geometry = PointGeometry()
        self._point_geometry.set_point_size(8.0)
        # サンプルの点を追加
        self._point_geometry.add_point(-0.8, 0.8, 0.0, 1.0, 0.0, 0.0)   # 赤
        self._point_geometry.add_point(0.0, 0.8, 0.0, 0.0, 1.0, 0.0)    # 緑
        self._point_geometry.add_point(0.8, 0.8, 0.0, 0.0, 0.0, 1.0)    # 青
        self._point_geometry.add_point(-0.4, 0.4, 0.0, 1.0, 1.0, 0.0)   # 黄
        self._point_geometry.add_point(0.4, 0.4, 0.0, 1.0, 0.0, 1.0)    # マゼンタ
        logger.info("Point geometry created")

        # === 線ジオメトリ ===
        self._line_geometry = LineGeometry()
        self._line_geometry.set_line_width(2.0)
        # サンプルの線を追加（座標軸風）
        self._line_geometry.add_line(-1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0)  # X軸（赤）
        self._line_geometry.add_line(0.0, -1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0)  # Y軸（緑）
        self._line_geometry.add_line(0.0, 0.0, -1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0)  # Z軸（青）
        # グラデーション線
        self._line_geometry.add_line_colored(
            -0.5, -0.3, 0.0, 1.0, 0.0, 0.0,  # 始点: 赤
            0.5, -0.3, 0.0, 0.0, 0.0, 1.0    # 終点: 青
        )
        logger.info("Line geometry created")

        # === 三角形ジオメトリ ===
        self._triangle_geometry = TriangleGeometry()
        # 虹色の三角形
        self._triangle_geometry.add_triangle_colored(
            -0.5, -0.5, 0.0, 1.0, 0.0, 0.0,  # 左下: 赤
            0.5, -0.5, 0.0, 0.0, 1.0, 0.0,   # 右下: 緑
            0.0, 0.5, 0.0, 0.0, 0.0, 1.0     # 上: 青
        )
        logger.info("Triangle geometry created")

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

        # imguiがマウスを使用していない場合のみカメラ操作を有効化
        io = imgui.get_io()
        self._camera_controller.set_enabled(not io.want_capture_mouse)

        # カメラコントローラーを更新
        self._camera_controller.update(self._use_3d_camera)

        # マウスコントローラーを更新（フレーム終了時）
        self._mouse.update()

        # ===== imguiウィンドウ =====
        self._draw_settings_window()
        self._draw_camera_window()
        self._draw_transform_window()
        self._draw_geometry_window()

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

    def _draw_camera_window(self) -> None:
        """Draw camera window"""
        imgui.begin("Camera")

        # Camera mode selection
        mode_names = ["2D (Orthographic)", "3D (Perspective)"]
        current_mode = 1 if self._use_3d_camera else 0
        changed_mode, new_mode = imgui.combo("Mode", current_mode, mode_names)
        if changed_mode:
            self._use_3d_camera = (new_mode == 1)

        # Up axis selection (3D only)
        if self._use_3d_camera:
            up_axis_names = ["Y-up (OpenGL)", "Z-up (CAD)"]
            current_up = 1 if self._camera_3d.up_axis == UpAxis.Z_UP else 0
            changed_up, new_up = imgui.combo("Up Axis", current_up, up_axis_names)
            if changed_up:
                self._camera_3d.set_up_axis(UpAxis.Z_UP if new_up == 1 else UpAxis.Y_UP)

        imgui.separator()

        if not self._use_3d_camera:
            # === 2D Camera Settings ===
            imgui.text("2D Camera Settings")

            # Camera position (XY plane)
            cam_pos = self._camera_2d.position
            changed_x, cam_x = imgui.slider_float("Offset X", cam_pos[0], -5.0, 5.0)
            changed_y, cam_y = imgui.slider_float("Offset Y", cam_pos[1], -5.0, 5.0)
            if changed_x or changed_y:
                self._camera_2d.set_position(cam_x, cam_y)

            # Zoom
            changed_zoom, zoom = imgui.slider_float("Zoom", self._camera_2d.zoom, 0.1, 5.0)
            if changed_zoom:
                self._camera_2d.set_zoom(zoom)

            # Rotation
            changed_rot, rotation = imgui.slider_float("Rotation", self._camera_2d.rotation, 0.0, 360.0)
            if changed_rot:
                self._camera_2d.set_rotation(rotation)

        else:
            # === 3D Camera Settings ===
            imgui.text("3D Camera Settings")

            # Orbit (spherical coordinates around target)
            if imgui.collapsing_header("Orbit (Rotate around target)", imgui.TreeNodeFlags_.default_open.value):
                orbit = self._camera_3d.get_orbit()
                changed_az, azimuth = imgui.slider_float("Azimuth", orbit[0], -180.0, 180.0)
                changed_el, elevation = imgui.slider_float("Elevation", orbit[1], -89.0, 89.0)
                changed_dist, distance = imgui.slider_float("Distance", orbit[2], 1.0, 20.0)
                if changed_az or changed_el or changed_dist:
                    self._camera_3d.set_orbit(azimuth, elevation, distance)

            # Pan (parallel translation)
            if imgui.collapsing_header("Pan (Move camera and target)", imgui.TreeNodeFlags_.default_open.value):
                pan = self._camera_3d.pan
                changed_pan_x, pan_x = imgui.slider_float("Pan X", pan[0], -5.0, 5.0)
                changed_pan_y, pan_y = imgui.slider_float("Pan Y", pan[1], -5.0, 5.0)
                changed_pan_z, pan_z = imgui.slider_float("Pan Z", pan[2], -5.0, 5.0)
                if changed_pan_x or changed_pan_y or changed_pan_z:
                    self._camera_3d.set_pan(pan_x, pan_y, pan_z)

            # Projection settings
            if imgui.collapsing_header("Projection", imgui.TreeNodeFlags_.default_open.value):
                changed_fov, fov = imgui.slider_float("FOV", self._camera_3d.fov, 15.0, 120.0)
                if changed_fov:
                    self._camera_3d.set_fov(fov)

        imgui.separator()

        # Mouse controls help
        if imgui.collapsing_header("Mouse Controls"):
            if self._use_3d_camera:
                imgui.bullet_text("Left Drag: Orbit (rotate)")
                imgui.bullet_text("Right Drag: Pan (horizontal)")
                imgui.bullet_text("Middle Drag: Height adjust")
                imgui.bullet_text("Scroll: Zoom (distance)")
            else:
                imgui.bullet_text("Left Drag: Rotate")
                imgui.bullet_text("Right/Middle Drag: Pan")
                imgui.bullet_text("Scroll: Zoom")

        imgui.separator()

        # Reset button
        if imgui.button("Reset Camera"):
            if self._use_3d_camera:
                self._camera_3d.reset()
            else:
                self._camera_2d.reset()

        imgui.end()

    def _draw_transform_window(self) -> None:
        """座標変換ウィンドウを描画"""
        imgui.begin("Transform")

        # Model行列の回転
        changed_x, self._rotation_x = imgui.slider_float("Rotate X", self._rotation_x, 0.0, 360.0)
        changed_y, self._rotation_y = imgui.slider_float("Rotate Y", self._rotation_y, 0.0, 360.0)
        changed_z, self._rotation_z = imgui.slider_float("Rotate Z", self._rotation_z, 0.0, 360.0)

        # リセットボタン
        if imgui.button("Reset Rotation"):
            self._rotation_x = 0.0
            self._rotation_y = 0.0
            self._rotation_z = 0.0

        imgui.end()

    def _draw_geometry_window(self) -> None:
        """形状ウィンドウを描画"""
        imgui.begin("Geometry")

        # 表示モードの選択
        mode_names = ["Points", "Lines", "Triangles", "All"]
        changed, self._geometry_mode = imgui.combo("Display Mode", self._geometry_mode, mode_names)

        imgui.separator()

        # === 点の設定 ===
        if imgui.collapsing_header("Points", imgui.TreeNodeFlags_.default_open.value):
            if self._point_geometry:
                # 点のサイズ
                changed_size, size = imgui.slider_float(
                    "Point Size", self._point_geometry.point_size, 1.0, 20.0
                )
                if changed_size:
                    self._point_geometry.set_point_size(size)

                imgui.text(f"Point Count: {self._point_geometry.vertex_count}")

                if imgui.button("Clear Points"):
                    self._point_geometry.clear()

                if imgui.button("Add Random Point"):
                    import random
                    x = random.uniform(-1.0, 1.0)
                    y = random.uniform(-1.0, 1.0)
                    z = random.uniform(-0.5, 0.5)
                    r = random.uniform(0.0, 1.0)
                    g = random.uniform(0.0, 1.0)
                    b = random.uniform(0.0, 1.0)
                    self._point_geometry.add_point(x, y, z, r, g, b)

        # === 線の設定 ===
        if imgui.collapsing_header("Lines", imgui.TreeNodeFlags_.default_open.value):
            if self._line_geometry:
                # Note: macOS Core Profileでは glLineWidth() は 1.0 のみサポート
                # そのためLine Widthスライダーは省略

                imgui.text(f"Line Count: {len(self._line_geometry.lines)}")

                if imgui.button("Clear Lines"):
                    self._line_geometry.clear()

                if imgui.button("Add Random Line"):
                    import random
                    x1, y1 = random.uniform(-1.0, 1.0), random.uniform(-1.0, 1.0)
                    x2, y2 = random.uniform(-1.0, 1.0), random.uniform(-1.0, 1.0)
                    r = random.uniform(0.0, 1.0)
                    g = random.uniform(0.0, 1.0)
                    b = random.uniform(0.0, 1.0)
                    self._line_geometry.add_line(x1, y1, 0.0, x2, y2, 0.0, r, g, b)

        # === 三角形の設定 ===
        if imgui.collapsing_header("Triangles", imgui.TreeNodeFlags_.default_open.value):
            if self._triangle_geometry:
                imgui.text(f"Triangle Count: {len(self._triangle_geometry.triangles)}")

                if imgui.button("Clear Triangles"):
                    self._triangle_geometry.clear()

                if imgui.button("Add Random Triangle"):
                    import random
                    # ランダムな中心位置
                    cx = random.uniform(-0.5, 0.5)
                    cy = random.uniform(-0.5, 0.5)
                    size = random.uniform(0.1, 0.3)
                    # ランダムな色
                    r1, g1, b1 = random.random(), random.random(), random.random()
                    r2, g2, b2 = random.random(), random.random(), random.random()
                    r3, g3, b3 = random.random(), random.random(), random.random()
                    self._triangle_geometry.add_triangle_colored(
                        cx - size, cy - size, 0.0, r1, g1, b1,
                        cx + size, cy - size, 0.0, r2, g2, b2,
                        cx, cy + size, 0.0, r3, g3, b3
                    )

        imgui.separator()

        # すべてリセット
        if imgui.button("Reset All Geometries"):
            self._setup_geometries()

        imgui.end()

    def _render(self) -> None:
        """描画処理"""
        # 背景色の適用
        gl.glClearColor(*self._clear_color)

        # 深度テストを有効化（3D描画用）
        gl.glEnable(gl.GL_DEPTH_TEST)

        # 画面のクリア
        gl.glClear(int(gl.GL_COLOR_BUFFER_BIT) | int(gl.GL_DEPTH_BUFFER_BIT))

        # ジオメトリの描画
        self._draw_geometries()

        # imguiのレンダリング
        self._gui.render()

        # バッファの入れ替え
        self._window.swap_buffers()

    def _draw_geometries(self) -> None:
        """ジオメトリを描画する"""
        if not self._shader:
            return

        # Model行列を更新
        self._transform.set_model_identity()
        self._transform.rotate_model_x(self._rotation_x)
        self._transform.rotate_model_y(self._rotation_y)
        self._transform.rotate_model_z(self._rotation_z)

        # シェーダーを使用
        self._shader.use()

        # 現在のカメラを取得
        camera = self._camera_3d if self._use_3d_camera else self._camera_2d

        # 行列をシェーダーに設定
        self._shader.set_mat4("model", self._transform.model)
        self._shader.set_mat4("view", camera.view_matrix)
        self._shader.set_mat4("projection", camera.projection_matrix)

        # 形状の描画（モードに応じて）
        # 0: Points, 1: Lines, 2: Triangles, 3: All
        if self._geometry_mode == 0 or self._geometry_mode == 3:
            if self._point_geometry:
                self._point_geometry.draw()

        if self._geometry_mode == 1 or self._geometry_mode == 3:
            if self._line_geometry:
                self._line_geometry.draw()

        if self._geometry_mode == 2 or self._geometry_mode == 3:
            if self._triangle_geometry:
                self._triangle_geometry.draw()

    def _shutdown(self) -> None:
        """終了処理"""
        # ジオメトリリソースの解放
        if self._point_geometry:
            self._point_geometry.cleanup()
        if self._line_geometry:
            self._line_geometry.cleanup()
        if self._triangle_geometry:
            self._triangle_geometry.cleanup()

        # シェーダーの解放
        if self._shader:
            self._shader.delete()

        self._gui.shutdown()
        self._window.terminate()


