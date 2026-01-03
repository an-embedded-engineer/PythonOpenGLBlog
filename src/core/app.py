"""
アプリケーションモジュール
"""
from pathlib import Path
import random

import numpy as np
from imgui_bundle import imgui
import OpenGL.GL as gl

from src.core.window import Window
from src.core.gui import GUI
from src.core.mouse_controller import MouseController
from src.core.camera_controller import CameraController
from src.graphics import (
    Shader, Camera2D, Camera3D, UpAxis,
    PointGeometry, LineGeometry, TriangleGeometry,
    RectangleGeometry, CubeGeometry, SphereGeometry,
)
from src.graphics.transform import Transform
from src.graphics.batch_renderer import BatchRenderer, PrimitiveType
from src.utils.logger import logger
from src.utils import performance_manager


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

        # Rectangle/Cube/Sphereのパラメータ（ジオメトリ初期化前に定義）
        self._rectangle_width = 1.0
        self._rectangle_height = 1.0
        self._cube_size = 1.0
        self._sphere_radius = 1.0
        self._sphere_segments = 16
        self._sphere_rings = 16
        self._shape_color = [0.5, 0.5, 1.0, 1.0]  # 水色

        # ジオメトリの初期化（点・線・三角形）
        self._point_geometry: PointGeometry | None = None
        self._line_geometry: LineGeometry | None = None
        self._triangle_geometry: TriangleGeometry | None = None
        self._rectangle_geometry: RectangleGeometry | None = None
        self._cube_geometry: CubeGeometry | None = None
        self._sphere_geometry: SphereGeometry | None = None
        self._setup_geometries()

        # 表示する形状の選択（0: 点, 1: 線, 2: 三角形, 3: すべて, 4: 矩形, 5: 立方体, 6: 球体）
        self._geometry_mode = 3

        # ワイヤフレームモード
        self._wireframe_mode = False

        # Allモード用の複数オブジェクト（位置とスケール）
        self._all_mode_objects: list[dict] = []
        self._generate_all_mode_objects()

        # バッチレンダリング
        self._use_batch_rendering = False
        self._batch_renderer_triangles: BatchRenderer | None = None

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

        # === 矩形ジオメトリ ===
        self._rectangle_geometry = RectangleGeometry(
            width=self._rectangle_width,
            height=self._rectangle_height,
            r=self._shape_color[0],
            g=self._shape_color[1],
            b=self._shape_color[2],
        )
        logger.info("Rectangle geometry created")

        # === 立方体ジオメトリ ===
        self._cube_geometry = CubeGeometry(
            size=self._cube_size,
            r=self._shape_color[0],
            g=self._shape_color[1],
            b=self._shape_color[2],
        )
        logger.info("Cube geometry created")

        # === 球体ジオメトリ ===
        self._sphere_geometry = SphereGeometry(
            radius=self._sphere_radius,
            segments=self._sphere_segments,
            rings=self._sphere_rings,
            r=self._shape_color[0],
            g=self._shape_color[1],
            b=self._shape_color[2],
        )
        logger.info("Sphere geometry created")

    def _generate_all_mode_objects(self) -> None:
        """Allモード用のランダムオブジェクトを生成"""
        self._all_mode_objects = []
        # Rectangle 3個
        for _ in range(3):
            self._all_mode_objects.append({
                'type': 'rectangle',
                'pos': [random.uniform(-2, 2), random.uniform(-2, 2), random.uniform(-1, 1)],
                'scale': random.uniform(0.3, 0.8),
                'color': [random.random(), random.random(), random.random()]
            })
        # Cube 3個
        for _ in range(3):
            self._all_mode_objects.append({
                'type': 'cube',
                'pos': [random.uniform(-2, 2), random.uniform(-2, 2), random.uniform(-1, 1)],
                'scale': random.uniform(0.3, 0.8),
                'color': [random.random(), random.random(), random.random()]
            })
        # Sphere 3個
        for _ in range(3):
            self._all_mode_objects.append({
                'type': 'sphere',
                'pos': [random.uniform(-2, 2), random.uniform(-2, 2), random.uniform(-1, 1)],
                'scale': random.uniform(0.3, 0.8),
                'color': [random.random(), random.random(), random.random()]
            })
        logger.info(f"Generated {len(self._all_mode_objects)} objects for All mode")

    def run(self) -> None:
        """メインループを実行する"""
        logger.debug("App.run() start")
        try:
            while not self._window.should_close:
                performance_manager.begin_frame()
                self._update()
                self._render()
                performance_manager.end_frame()
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
        self._draw_performance_window()

    def _draw_settings_window(self) -> None:
        """設定ウィンドウを描画"""
        imgui.begin("Settings")

        # 背景色の変更
        changed, self._clear_color = imgui.color_edit4("Background", self._clear_color)

        # FPSの表示
        imgui.text(f"FPS: {performance_manager.get_fps():.1f}")

        imgui.separator()

        # バッチレンダリング設定
        changed, self._use_batch_rendering = imgui.checkbox("Use Batch Rendering (All Mode)", self._use_batch_rendering)
        if imgui.is_item_hovered():
            imgui.set_tooltip("Enable batch rendering to reduce draw calls\n(Only works in All mode)")

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
        imgui.begin(name="Geometry")

        # 表示モードの選択
        mode_names = ["Points", "Lines", "Triangles", "All", "Rectangle", "Cube", "Sphere"]
        changed, self._geometry_mode = imgui.combo("Display Mode", self._geometry_mode, mode_names)

        # ワイヤフレームモード
        changed_wire, self._wireframe_mode = imgui.checkbox("Wireframe Mode", self._wireframe_mode)

        # Allモード用のオブジェクト再生成ボタン
        if self._geometry_mode == 3:  # All mode
            if imgui.button("Regenerate All Objects"):
                self._generate_all_mode_objects()

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

        # === 矩形の設定 ===
        if imgui.collapsing_header("Rectangle", imgui.TreeNodeFlags_.default_open.value):
            changed_w, self._rectangle_width = imgui.slider_float("Width", self._rectangle_width, 0.1, 3.0)
            changed_h, self._rectangle_height = imgui.slider_float("Height", self._rectangle_height, 0.1, 3.0)
            if changed_w or changed_h:
                if self._rectangle_geometry:
                    self._rectangle_geometry.set_size(self._rectangle_width, self._rectangle_height)

            changed_color, self._shape_color = imgui.color_edit4("Color", self._shape_color)
            if changed_color and self._rectangle_geometry:
                self._rectangle_geometry.set_color(*self._shape_color[:3])

            if self._rectangle_geometry:
                imgui.text(f"Vertices: {self._rectangle_geometry.vertex_count}")
                imgui.text(f"Indices: {self._rectangle_geometry.index_count}")

            if imgui.button("Random Color##rect"):
                if self._rectangle_geometry:
                    self._rectangle_geometry.set_random_colors()

        # === 立方体の設定 ===
        if imgui.collapsing_header("Cube", imgui.TreeNodeFlags_.default_open.value):
            changed_s, self._cube_size = imgui.slider_float("Size", self._cube_size, 0.1, 3.0)
            if changed_s and self._cube_geometry:
                self._cube_geometry.set_size(self._cube_size)

            changed_color, self._shape_color = imgui.color_edit4("Color##cube", self._shape_color)
            if changed_color and self._cube_geometry:
                self._cube_geometry.set_color(*self._shape_color[:3])

            if self._cube_geometry:
                imgui.text(f"Vertices: {self._cube_geometry.vertex_count}")
                imgui.text(f"Indices: {self._cube_geometry.index_count}")

            if imgui.button("Random Color##cube"):
                if self._cube_geometry:
                    self._cube_geometry.set_random_colors()

        # === 球体の設定 ===
        if imgui.collapsing_header("Sphere", imgui.TreeNodeFlags_.default_open.value):
            changed_r, self._sphere_radius = imgui.slider_float("Radius", self._sphere_radius, 0.1, 3.0)
            changed_seg, self._sphere_segments = imgui.slider_int("Segments", self._sphere_segments, 4, 64)
            changed_ring, self._sphere_rings = imgui.slider_int("Rings", self._sphere_rings, 2, 64)

            if changed_r or changed_seg or changed_ring:
                # 球体を再生成
                if self._sphere_geometry:
                    self._sphere_geometry.cleanup()
                self._sphere_geometry = SphereGeometry(
                    radius=self._sphere_radius,
                    segments=self._sphere_segments,
                    rings=self._sphere_rings,
                    r=self._shape_color[0],
                    g=self._shape_color[1],
                    b=self._shape_color[2],
                )

            changed_color, self._shape_color = imgui.color_edit4("Color##sphere", self._shape_color)
            if changed_color and self._sphere_geometry:
                self._sphere_geometry.set_color(*self._shape_color[:3])

            if self._sphere_geometry:
                imgui.text(f"Vertices: {self._sphere_geometry.vertex_count}")
                imgui.text(f"Indices: {self._sphere_geometry.index_count}")

            if imgui.button("Random Color##sphere"):
                if self._sphere_geometry:
                    self._sphere_geometry.set_random_colors()

        imgui.separator()

        # すべてリセット
        if imgui.button("Reset All Geometries"):
            self._setup_geometries()

        imgui.end()

    def _draw_performance_window(self) -> None:
        """パフォーマンスウィンドウを描画"""
        imgui.begin("Performance")

        # 前フレームの統計情報を取得
        stats = performance_manager.get_previous_frame_info()
        fps_stats = performance_manager.get_fps_stats()

        # FPS表示
        imgui.text(f"FPS: {stats.fps:.1f}")
        imgui.text(f"Frame Time: {stats.frame_time_ms:.2f} ms")
        imgui.text(f"Draw Calls: {performance_manager.get_draw_call_count()}")

        imgui.separator()

        # FPS統計
        if imgui.tree_node_ex("FPS Stats", imgui.TreeNodeFlags_.default_open):
            imgui.text(f"Average: {fps_stats['average']:.1f}")
            imgui.text(f"Max: {fps_stats['max']:.1f}")
            imgui.text(f"Min: {fps_stats['min']:.1f}")
            imgui.tree_pop()

        imgui.separator()

        # 処理時間の階層表示
        if imgui.tree_node_ex("Timing (Hierarchical)", imgui.TreeNodeFlags_.default_open):
            self._draw_hierarchical_stats(stats.hierarchical_stats, 0)
            imgui.tree_pop()

        imgui.separator()

        # ログ出力ボタン
        if imgui.button("Print Stats to Log (Hierarchical)"):
            performance_manager.print_stats(hierarchical=True)

        if imgui.button("Print Stats to Log (Flat, Sorted)"):
            performance_manager.print_stats(hierarchical=False, sort_by_time=True)

        if imgui.button("Reset Stats"):
            performance_manager.reset()

        imgui.end()

    def _draw_hierarchical_stats(self, stats_node: dict, depth: int) -> None:
        """階層化された統計をimguiで表示"""
        # 実行順序でソート
        sorted_nodes = sorted(stats_node.items(),
                            key=lambda x: x[1].get('execution_order', 0))

        for node_name, node_data in sorted_nodes:
            timing_ms = node_data['time'] * 1000
            call_count = node_data['call_count']
            children = node_data['children']

            is_actual_leaf = len(children) == 0

            if is_actual_leaf:
                # リーフノード
                display_text = f"{node_name}: {timing_ms:.2f}ms"
                if call_count > 1:
                    display_text += f" (x{call_count})"
                imgui.text(display_text)
            else:
                # 中間ノード（ツリーノードとして表示）
                total_children_time = self._calculate_total_children_time(children)
                total_children_ms = total_children_time * 1000

                # ラベル（表示テキスト）とID部分を完全に分離
                # ID部分は固定値、ラベル部分は毎フレーム更新される
                display_label = f"{node_name}: {timing_ms:.2f}ms (children: {total_children_ms:.2f}ms)"
                node_id = f"{node_name}_{depth}"  # ID部分のみ

                # tree_node_exを使用してラベルとフラグを指定
                if imgui.tree_node_ex(node_id, imgui.TreeNodeFlags_.default_open, display_label):
                    self._draw_hierarchical_stats(children, depth + 1)
                    imgui.tree_pop()

    def _calculate_total_children_time(self, children: dict) -> float:
        """子ノードの合計時間を計算"""
        total_time = 0.0
        for child_data in children.values():
            if len(child_data['children']) == 0:
                total_time += child_data['time']
            else:
                total_time += self._calculate_total_children_time(child_data['children'])
        return total_time

    def _render(self) -> None:
        """描画処理"""
        with performance_manager.time_operation("Render"):
            # 背景色の適用
            gl.glClearColor(*self._clear_color)

            # 深度テストを有効化（3D描画用）
            gl.glEnable(gl.GL_DEPTH_TEST)

            # 画面のクリア
            gl.glClear(int(gl.GL_COLOR_BUFFER_BIT) | int(gl.GL_DEPTH_BUFFER_BIT))

            # ジオメトリの描画
            with performance_manager.time_operation("Draw Geometries"):
                self._draw_geometries()

            # imguiのレンダリング
            with performance_manager.time_operation("Render GUI"):
                self._gui.render()

            # バッファの入れ替え
            self._window.swap_buffers()

    def _draw_geometries(self) -> None:
        """ジオメトリを描画する"""
        if not self._shader:
            return

        # バッチレンダリングを使用するかどうか
        if self._use_batch_rendering and self._geometry_mode == 3:
            self._draw_with_batching()
        else:
            self._draw_without_batching()

    def _draw_without_batching(self) -> None:
        """バッチレンダリングなしで描画（従来の方法）"""
        if not self._shader:
            return

        # ドローコールカウントをリセット
        draw_call_count = 0

        # ワイヤフレームモードの設定
        if self._wireframe_mode:
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)
        else:
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)

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
        # 0: Points, 1: Lines, 2: Triangles, 3: All, 4: Rectangle, 5: Cube, 6: Sphere
        if self._geometry_mode == 0 or self._geometry_mode == 3:
            if self._point_geometry:
                with performance_manager.time_operation("Draw Points"):
                    self._point_geometry.draw()
                    draw_call_count += 1

        if self._geometry_mode == 1 or self._geometry_mode == 3:
            if self._line_geometry:
                with performance_manager.time_operation("Draw Lines"):
                    self._line_geometry.draw()
                    draw_call_count += 1

        if self._geometry_mode == 2 or self._geometry_mode == 3:
            if self._triangle_geometry:
                with performance_manager.time_operation("Draw Triangles"):
                    self._triangle_geometry.draw()
                    draw_call_count += 1

        # Allモードの場合、複数のRectangle/Cube/Sphereを描画
        if self._geometry_mode == 3:
            with performance_manager.time_operation("Draw All Objects"):
                for obj in self._all_mode_objects:
                    # 個別のModel行列を設定
                    self._transform.set_model_identity()
                    self._transform.translate_model(obj['pos'][0], obj['pos'][1], obj['pos'][2])
                    self._transform.scale_model(obj['scale'], obj['scale'], obj['scale'])
                    self._transform.rotate_model_x(self._rotation_x)
                    self._transform.rotate_model_y(self._rotation_y)
                    self._transform.rotate_model_z(self._rotation_z)
                    self._shader.set_mat4("model", self._transform.model)

                    # オブジェクトタイプに応じて描画
                    if obj['type'] == 'rectangle' and self._rectangle_geometry:
                        # 一時的に色を変更
                        original_color = self._rectangle_geometry._color
                        self._rectangle_geometry.set_color(*obj['color'])
                        self._rectangle_geometry.draw()
                        self._rectangle_geometry.set_color(*original_color)
                        draw_call_count += 1
                    elif obj['type'] == 'cube' and self._cube_geometry:
                        original_color = self._cube_geometry._color
                        self._cube_geometry.set_color(*obj['color'])
                        self._cube_geometry.draw()
                        self._cube_geometry.set_color(*original_color)
                        draw_call_count += 1
                    elif obj['type'] == 'sphere' and self._sphere_geometry:
                        original_color = self._sphere_geometry._color
                        self._sphere_geometry.set_color(*obj['color'])
                        self._sphere_geometry.draw()
                        self._sphere_geometry.set_color(*original_color)
                        draw_call_count += 1

        if self._geometry_mode == 4:
            if self._rectangle_geometry:
                with performance_manager.time_operation("Draw Rectangle"):
                    self._rectangle_geometry.draw()
                    draw_call_count += 1

        if self._geometry_mode == 5:
            if self._cube_geometry:
                with performance_manager.time_operation("Draw Cube"):
                    self._cube_geometry.draw()
                    draw_call_count += 1

        if self._geometry_mode == 6:
            if self._sphere_geometry:
                with performance_manager.time_operation("Draw Sphere"):
                    self._sphere_geometry.draw()
                    draw_call_count += 1

        # ドローコール数を記録
        performance_manager.set_draw_call_count(draw_call_count)

        # ワイヤフレームモードをリセット
        if self._wireframe_mode:
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)

    def _draw_with_batching(self) -> None:
        """バッチレンダリングを使用して描画（Allモード専用）"""
        if not self._shader:
            return

        # バッチレンダラーを初期化（初回のみ）
        if self._batch_renderer_triangles is None:
            self._batch_renderer_triangles = BatchRenderer(PrimitiveType.TRIANGLES)

        # バッチをクリア
        self._batch_renderer_triangles.clear()

        # ワイヤフレームモードの設定
        if self._wireframe_mode:
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)
        else:
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)

        # シェーダーを使用
        self._shader.use()

        # 現在のカメラを取得
        camera = self._camera_3d if self._use_3d_camera else self._camera_2d

        # View/Projection行列をシェーダーに設定
        self._shader.set_mat4("view", camera.view_matrix)
        self._shader.set_mat4("projection", camera.projection_matrix)

        # Allモードの全オブジェクトをバッチに追加
        with performance_manager.time_operation("Build Batch"):
            for obj in self._all_mode_objects:
                # 個別のModel行列を計算
                self._transform.set_model_identity()
                self._transform.translate_model(obj['pos'][0], obj['pos'][1], obj['pos'][2])
                self._transform.scale_model(obj['scale'], obj['scale'], obj['scale'])
                self._transform.rotate_model_x(self._rotation_x)
                self._transform.rotate_model_y(self._rotation_y)
                self._transform.rotate_model_z(self._rotation_z)
                model_matrix = self._transform.model.copy()

                # オブジェクトタイプに応じて頂点データを取得してバッチに追加
                geometry = None
                if obj['type'] == 'rectangle' and self._rectangle_geometry:
                    geometry = self._rectangle_geometry
                elif obj['type'] == 'cube' and self._cube_geometry:
                    geometry = self._cube_geometry
                elif obj['type'] == 'sphere' and self._sphere_geometry:
                    geometry = self._sphere_geometry

                if geometry:
                    # 一時的に色を設定
                    original_color = geometry._color
                    geometry.set_color(*obj['color'])

                    # 頂点データを取得
                    vertices, indices = geometry.get_vertex_data()

                    # 色を戻す
                    geometry.set_color(*original_color)

                    # バッチに追加
                    self._batch_renderer_triangles.add_geometry(vertices, indices, model_matrix)

        # バッチをビルド＆描画（1回のドローコール）
        with performance_manager.time_operation("Draw Batch"):
            # Model行列は単位行列に設定（各頂点は既に変換済み）
            self._shader.set_mat4("model", np.eye(4, dtype=np.float32))
            self._batch_renderer_triangles.flush()

        # ドローコール数を記録（バッチレンダリングは1回）
        performance_manager.set_draw_call_count(1)

        # ワイヤフレームモードをリセット
        if self._wireframe_mode:
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)

    def _shutdown(self) -> None:
        """終了処理"""
        # バッチレンダラーの解放
        if self._batch_renderer_triangles:
            self._batch_renderer_triangles.cleanup()

        # ジオメトリリソースの解放
        if self._point_geometry:
            self._point_geometry.cleanup()
        if self._line_geometry:
            self._line_geometry.cleanup()
        if self._triangle_geometry:
            self._triangle_geometry.cleanup()
        if self._rectangle_geometry:
            self._rectangle_geometry.cleanup()
        if self._cube_geometry:
            self._cube_geometry.cleanup()
        if self._sphere_geometry:
            self._sphere_geometry.cleanup()

        # シェーダーの解放
        if self._shader:
            self._shader.delete()

        self._gui.shutdown()
        self._window.terminate()


