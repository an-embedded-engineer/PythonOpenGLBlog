"""
アプリケーションモジュール
"""
import ctypes
from pathlib import Path

import numpy as np
from imgui_bundle import imgui
import OpenGL.GL as gl

from src.core.window import Window
from src.core.gui import GUI
from src.graphics import Shader
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

        # 座標変換
        self._transform = Transform()

        # Model行列の回転パラメータ（imguiで調整可能）
        self._rotation_x = 0.0
        self._rotation_y = 0.0
        self._rotation_z = 0.0

        # シェーダーとジオメトリの初期化
        self._shader: Shader | None = None
        self._vao: int = 0
        self._vbo: int = 0
        self._setup_shader()
        self._setup_geometry()

        logger.debug("App.__init__ end")

    def _setup_shader(self) -> None:
        """シェーダーをセットアップする"""
        vertex_path = self.SHADER_DIR / "basic.vert"
        fragment_path = self.SHADER_DIR / "basic.frag"
        self._shader = Shader(vertex_path, fragment_path)

    def _setup_geometry(self) -> None:
        """三角形のジオメトリをセットアップする"""
        # 頂点データ（位置 x, y, z, 色 r, g, b）
        # 虹色の三角形
        vertices = np.array([
            # 位置              # 色
            -0.5, -0.5, 0.0,   1.0, 0.0, 0.0,  # 左下: 赤
             0.5, -0.5, 0.0,   0.0, 1.0, 0.0,  # 右下: 緑
             0.0,  0.5, 0.0,   0.0, 0.0, 1.0,  # 上: 青
        ], dtype=np.float32)

        # VAO（頂点配列オブジェクト）の作成
        self._vao = gl.glGenVertexArrays(1)
        gl.glBindVertexArray(self._vao)

        # VBO（頂点バッファオブジェクト）の作成
        self._vbo = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices, gl.GL_STATIC_DRAW)

        # 頂点属性の設定
        stride = 6 * vertices.itemsize  # 1頂点あたり6つのfloat（位置3 + 色3）

        # 属性0: 位置（location = 0）
        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, stride, None)
        gl.glEnableVertexAttribArray(0)

        # 属性1: 色（location = 1）
        offset = 3 * vertices.itemsize  # 色データのオフセット（位置の後）
        gl.glVertexAttribPointer(1, 3, gl.GL_FLOAT, gl.GL_FALSE, stride, ctypes.c_void_p(offset))
        gl.glEnableVertexAttribArray(1)

        # バインド解除
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glBindVertexArray(0)

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

        # ===== imguiウィンドウ =====
        self._draw_settings_window()
        self._draw_camera_window()
        self._draw_transform_window()

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
        """カメラウィンドウを描画"""
        imgui.begin("Camera")

        # カメラ位置
        cam_pos = self._transform.camera_pos
        changed_pos_x, cam_x = imgui.slider_float("Camera X##pos", cam_pos[0], -10.0, 10.0)
        changed_pos_y, cam_y = imgui.slider_float("Camera Y##pos", cam_pos[1], -10.0, 10.0)
        changed_pos_z, cam_z = imgui.slider_float("Camera Z##pos", cam_pos[2], -10.0, 10.0)

        if changed_pos_x or changed_pos_y or changed_pos_z:
            self._transform.set_camera_position(cam_x, cam_y, cam_z)

        # カメラ視点
        cam_target = self._transform.camera_target
        changed_tgt_x, tgt_x = imgui.slider_float("Target X##pos", cam_target[0], -5.0, 5.0)
        changed_tgt_y, tgt_y = imgui.slider_float("Target Y##pos", cam_target[1], -5.0, 5.0)
        changed_tgt_z, tgt_z = imgui.slider_float("Target Z##pos", cam_target[2], -5.0, 5.0)

        if changed_tgt_x or changed_tgt_y or changed_tgt_z:
            self._transform.set_camera_target(tgt_x, tgt_y, tgt_z)

        # 視野角
        changed_fov, fov = imgui.slider_float("FOV", self._transform.fov, 15.0, 120.0)
        if changed_fov:
            self._transform.set_fov(fov)

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

    def _render(self) -> None:
        """描画処理"""
        # 背景色の適用
        gl.glClearColor(*self._clear_color)

        # 画面のクリア
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        # 三角形の描画
        self._draw_triangle()

        # imguiのレンダリング
        self._gui.render()

        # バッファの入れ替え
        self._window.swap_buffers()

    def _draw_triangle(self) -> None:
        """三角形を描画する"""
        if not self._shader:
            return

        # Model行列を更新
        self._transform.set_model_identity()
        self._transform.rotate_model_x(self._rotation_x)
        self._transform.rotate_model_y(self._rotation_y)
        self._transform.rotate_model_z(self._rotation_z)

        # シェーダーを使用
        self._shader.use()

        # 行列をシェーダーに設定
        self._shader.set_mat4("model", self._transform.model)
        self._shader.set_mat4("view", self._transform.view)
        self._shader.set_mat4("projection", self._transform.projection)

        # 三角形の描画
        gl.glBindVertexArray(self._vao)
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 3)
        gl.glBindVertexArray(0)

    def _shutdown(self) -> None:
        """終了処理"""
        # OpenGLリソースの解放
        if self._vao:
            gl.glDeleteVertexArrays(1, [self._vao])
        if self._vbo:
            gl.glDeleteBuffers(1, [self._vbo])
        if self._shader:
            self._shader.delete()

        self._gui.shutdown()
        self._window.terminate()


