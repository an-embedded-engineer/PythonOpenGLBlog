"""
インスタンスレンダリングモジュール

1つのベースジオメトリを多数インスタンスで効率よく描画するクラス。
glVertexAttribDivisor と glDrawElementsInstanced を使用。
"""

from typing import Optional
import numpy as np
import OpenGL.GL as gl


class InstanceRenderer:
    """
    インスタンスレンダリングクラス

    1つのベースジオメトリを N インスタンス分、1回のドローコールで描画する。

    頂点属性レイアウト:
      Location 0: aPos         (vec3) - ベース頂点座標
      Location 1: aColor       (vec3) - ベース頂点カラー（シェーダー内で未使用）

    インスタンス属性レイアウト（glVertexAttribDivisor = 1）:
      Location 2: aInstanceOffset (vec3)  - インスタンスの位置オフセット
      Location 3: aInstanceColor  (vec3)  - インスタンスのカラー
      Location 4: aInstanceScale  (float) - インスタンスのスケール

    インスタンスVBOの1要素 = 7 floats (offset.xyz, color.rgb, scale)
    """

    # インスタンスVBO内の各属性のオフセット（float単位）
    _INSTANCE_STRIDE_FLOATS = 7
    _INSTANCE_OFFSET_OFFSET = 0   # vec3: x, y, z
    _INSTANCE_COLOR_OFFSET = 3    # vec3: r, g, b
    _INSTANCE_SCALE_OFFSET = 6    # float: scale

    def __init__(self) -> None:
        """InstanceRendererを初期化する"""
        self._vao: int = 0
        self._vbo: int = 0           # ベース頂点バッファ
        self._ebo: int = 0           # インデックスバッファ（オプション）
        self._instance_vbo: int = 0  # インスタンスデータバッファ

        self._vertex_count: int = 0
        self._index_count: int = 0
        self._instance_count: int = 0
        self._use_indices: bool = False

    def set_geometry(self,
                     vertices: np.ndarray,
                     indices: Optional[np.ndarray] = None) -> None:
        """
        ベースジオメトリを設定する

        Args:
            vertices: 頂点データ (N, 6) [x, y, z, r, g, b] float32
            indices:  インデックスデータ (M,) uint32（None の場合は非インデックス描画）
        """
        if vertices.size == 0:
            return

        self._vertex_count = len(vertices)
        self._use_indices = indices is not None
        if indices is not None:
            self._index_count = len(indices)

        self._setup_vertex_buffers(vertices, indices)

    def set_instances(self,
                      offsets: np.ndarray,
                      colors: np.ndarray,
                      scales: np.ndarray) -> None:
        """
        インスタンスデータを設定する（初回）

        Args:
            offsets: 各インスタンスの位置オフセット (N, 3) float32
            colors:  各インスタンスのカラー (N, 3) float32
            scales:  各インスタンスのスケール (N,) float32
        """
        instance_data = self._pack_instance_data(offsets, colors, scales)
        self._instance_count = len(offsets)
        self._setup_instance_buffer(instance_data)

    def update_instances(self,
                         offsets: np.ndarray,
                         colors: np.ndarray,
                         scales: np.ndarray) -> None:
        """
        インスタンスデータを更新する（動的更新）

        set_instances() よりも効率的（バッファを再利用）

        Args:
            offsets: 各インスタンスの位置オフセット (N, 3) float32
            colors:  各インスタンスのカラー (N, 3) float32
            scales:  各インスタンスのスケール (N,) float32
        """
        if self._instance_vbo == 0:
            self.set_instances(offsets, colors, scales)
            return

        instance_data = self._pack_instance_data(offsets, colors, scales)
        new_count = len(offsets)

        if new_count != self._instance_count:
            # インスタンス数が変わった場合はバッファを再確保
            self._instance_count = new_count
            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._instance_vbo)
            gl.glBufferData(
                gl.GL_ARRAY_BUFFER,
                instance_data.nbytes,
                instance_data,
                gl.GL_DYNAMIC_DRAW
            )
        else:
            # サイズが同じなら部分更新（高速）
            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._instance_vbo)
            gl.glBufferSubData(
                gl.GL_ARRAY_BUFFER,
                0,
                instance_data.nbytes,
                instance_data
            )

        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)

    def draw(self) -> None:
        """
        インスタンシング描画を実行する

        glDrawElementsInstanced または glDrawArraysInstanced を使用し、
        self._instance_count 個のインスタンスを 1回のドローコールで描画する。
        """
        if self._vao == 0 or self._instance_count == 0:
            return

        gl.glBindVertexArray(self._vao)

        if self._use_indices and self._index_count > 0:
            gl.glDrawElementsInstanced(
                gl.GL_TRIANGLES,
                self._index_count,
                gl.GL_UNSIGNED_INT,
                None,
                self._instance_count
            )
        else:
            gl.glDrawArraysInstanced(
                gl.GL_TRIANGLES,
                0,
                self._vertex_count,
                self._instance_count
            )

        gl.glBindVertexArray(0)

    def cleanup(self) -> None:
        """OpenGLリソースを解放する"""
        if self._instance_vbo != 0:
            gl.glDeleteBuffers(1, [self._instance_vbo])
            self._instance_vbo = 0

        if self._ebo != 0:
            gl.glDeleteBuffers(1, [self._ebo])
            self._ebo = 0

        if self._vbo != 0:
            gl.glDeleteBuffers(1, [self._vbo])
            self._vbo = 0

        if self._vao != 0:
            gl.glDeleteVertexArrays(1, [self._vao])
            self._vao = 0

    @property
    def instance_count(self) -> int:
        """現在のインスタンス数"""
        return self._instance_count

    @property
    def vertex_count(self) -> int:
        """ベースジオメトリの頂点数"""
        return self._vertex_count

    @property
    def index_count(self) -> int:
        """ベースジオメトリのインデックス数"""
        return self._index_count

    # ------------------------------------------------------------------ #
    # Private helpers
    # ------------------------------------------------------------------ #

    def _pack_instance_data(self,
                            offsets: np.ndarray,
                            colors: np.ndarray,
                            scales: np.ndarray) -> np.ndarray:
        """
        インスタンス属性を1つのインタリーブ配列にパックする

        レイアウト（1インスタンス = 7 floats）:
          [offset.x, offset.y, offset.z, color.r, color.g, color.b, scale]

        Args:
            offsets: (N, 3)
            colors:  (N, 3)
            scales:  (N,) or (N, 1)

        Returns:
            インタリーブされたインスタンスデータ (N, 7) float32
        """
        n = len(offsets)
        scales_2d = scales.reshape(n, 1) if scales.ndim == 1 else scales
        instance_data = np.hstack([
            offsets.reshape(n, 3),
            colors.reshape(n, 3),
            scales_2d.reshape(n, 1),
        ]).astype(np.float32)
        return instance_data

    def _setup_vertex_buffers(self,
                              vertices: np.ndarray,
                              indices: Optional[np.ndarray]) -> None:
        """ベース頂点バッファを作成する"""
        # 既存のバッファを解放
        self.cleanup()

        self._vao = gl.glGenVertexArrays(1)
        gl.glBindVertexArray(self._vao)

        # --- 頂点 VBO ---
        self._vbo = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._vbo)
        gl.glBufferData(
            gl.GL_ARRAY_BUFFER,
            vertices.nbytes,
            vertices.astype(np.float32),
            gl.GL_STATIC_DRAW
        )

        stride = 6 * vertices.itemsize  # 6 floats: x, y, z, r, g, b

        # Location 0: aPos (vec3)
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(
            0, 3, gl.GL_FLOAT, gl.GL_FALSE,
            stride, gl.ctypes.c_void_p(0)
        )

        # Location 1: aColor (vec3)
        gl.glEnableVertexAttribArray(1)
        gl.glVertexAttribPointer(
            1, 3, gl.GL_FLOAT, gl.GL_FALSE,
            stride, gl.ctypes.c_void_p(3 * vertices.itemsize)
        )

        # --- EBO（インデックス使用の場合）---
        if indices is not None and indices.size > 0:
            self._ebo = gl.glGenBuffers(1)
            gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self._ebo)
            gl.glBufferData(
                gl.GL_ELEMENT_ARRAY_BUFFER,
                indices.nbytes,
                indices.astype(np.uint32),
                gl.GL_STATIC_DRAW
            )

        gl.glBindVertexArray(0)

    def _setup_instance_buffer(self, instance_data: np.ndarray) -> None:
        """
        インスタンスVBOを作成し、VAOに属性を登録する

        glVertexAttribDivisor(location, 1) により、
        attribute が1インスタンスごとに進むように設定する。
        """
        if self._vao == 0:
            return

        # --- インスタンス VBO ---
        self._instance_vbo = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._instance_vbo)
        gl.glBufferData(
            gl.GL_ARRAY_BUFFER,
            instance_data.nbytes,
            instance_data,
            gl.GL_DYNAMIC_DRAW  # 動的更新を想定
        )

        stride = self._INSTANCE_STRIDE_FLOATS * instance_data.itemsize  # 7 * 4 = 28 bytes

        gl.glBindVertexArray(self._vao)

        # Location 2: aInstanceOffset (vec3)
        offset_bytes = self._INSTANCE_OFFSET_OFFSET * instance_data.itemsize
        gl.glEnableVertexAttribArray(2)
        gl.glVertexAttribPointer(
            2, 3, gl.GL_FLOAT, gl.GL_FALSE,
            stride, gl.ctypes.c_void_p(offset_bytes)
        )
        gl.glVertexAttribDivisor(2, 1)  # 1インスタンスごとに進める

        # Location 3: aInstanceColor (vec3)
        color_bytes = self._INSTANCE_COLOR_OFFSET * instance_data.itemsize
        gl.glEnableVertexAttribArray(3)
        gl.glVertexAttribPointer(
            3, 3, gl.GL_FLOAT, gl.GL_FALSE,
            stride, gl.ctypes.c_void_p(color_bytes)
        )
        gl.glVertexAttribDivisor(3, 1)

        # Location 4: aInstanceScale (float)
        scale_bytes = self._INSTANCE_SCALE_OFFSET * instance_data.itemsize
        gl.glEnableVertexAttribArray(4)
        gl.glVertexAttribPointer(
            4, 1, gl.GL_FLOAT, gl.GL_FALSE,
            stride, gl.ctypes.c_void_p(scale_bytes)
        )
        gl.glVertexAttribDivisor(4, 1)

        gl.glBindVertexArray(0)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
