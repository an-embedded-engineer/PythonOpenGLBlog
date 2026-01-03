"""
バッチレンダリングモジュール

複数のジオメトリを1回のドローコールで描画するためのクラス群
"""

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum
import numpy as np
import OpenGL.GL as gl


class PrimitiveType(Enum):
    """OpenGLプリミティブタイプ"""
    POINTS = gl.GL_POINTS
    LINES = gl.GL_LINES
    TRIANGLES = gl.GL_TRIANGLES


@dataclass
class RenderBatch:
    """
    レンダリングバッチ情報

    1つのジオメトリインスタンスの描画情報を保持
    """
    vertices: np.ndarray           # 頂点データ（位置+色）
    indices: Optional[np.ndarray]  # インデックスデータ（Noneの場合は非インデックス描画）
    transform: np.ndarray          # Model変換行列（4x4）
    vertex_offset: int = 0         # 結合後のバッファ内オフセット
    vertex_count: int = 0          # 頂点数
    index_offset: int = 0          # インデックスオフセット
    index_count: int = 0           # インデックス数


class BatchRenderer:
    """
    バッチレンダリングクラス

    同じプリミティブタイプの複数オブジェクトを
    1回のドローコールで描画する
    """

    def __init__(self, primitive_type: PrimitiveType):
        """
        Args:
            primitive_type: 描画プリミティブ（TRIANGLES, POINTS, LINES等）
        """
        self._primitive_type = primitive_type
        self._batches: List[RenderBatch] = []
        self._vao: int = 0
        self._vbo: int = 0
        self._ebo: int = 0
        self._is_dirty: bool = False
        self._use_indices: bool = False
        self._total_vertices: int = 0
        self._total_indices: int = 0

    def add_geometry(self,
                     vertices: np.ndarray,
                     indices: Optional[np.ndarray],
                     transform: np.ndarray) -> None:
        """
        ジオメトリをバッチに追加

        Args:
            vertices: 頂点データ（Nx6: x,y,z,r,g,b）
            indices: インデックスデータ（Optional）
            transform: Model変換行列（4x4）
        """
        if vertices.size == 0:
            return

        batch = RenderBatch(
            vertices=vertices.copy(),
            indices=indices.copy() if indices is not None else None,
            transform=transform.copy(),
            vertex_count=len(vertices)
        )

        # インデックス使用の判定
        if indices is not None:
            self._use_indices = True
            batch.index_count = len(indices)

        self._batches.append(batch)
        self._is_dirty = True

    def clear(self) -> None:
        """バッチをクリア"""
        self._batches.clear()
        self._is_dirty = True
        self._total_vertices = 0
        self._total_indices = 0

    def build(self) -> None:
        """
        バッチをビルド（頂点データ結合、バッファ作成）

        Transform行列を適用して頂点座標を変換し、
        すべてのジオメトリの頂点を1つの配列に結合する
        """
        if not self._batches or not self._is_dirty:
            return

        # 1. すべての頂点にTransformを適用
        transformed_batches = []
        vertex_offset = 0

        for batch in self._batches:
            transformed_verts = self._apply_transform(batch.vertices, batch.transform)
            transformed_batches.append(transformed_verts)

            # オフセット情報を記録
            batch.vertex_offset = vertex_offset
            vertex_offset += batch.vertex_count

        # 2. 頂点データを結合
        if transformed_batches:
            combined_vertices = np.concatenate(transformed_batches, axis=0)
            self._total_vertices = len(combined_vertices)
        else:
            combined_vertices = np.array([], dtype=np.float32)
            self._total_vertices = 0

        # 3. インデックスデータを結合（該当する場合）
        combined_indices = None
        if self._use_indices:
            combined_indices = self._combine_indices()
            self._total_indices = len(combined_indices) if combined_indices is not None else 0

        # 4. OpenGLバッファを作成
        self._create_buffers(combined_vertices, combined_indices)

        self._is_dirty = False

    def flush(self) -> None:
        """バッチをGPUに転送して描画"""
        if self._is_dirty:
            self.build()

        if self._vao == 0 or self._total_vertices == 0:
            return

        gl.glBindVertexArray(self._vao)

        if self._use_indices and self._total_indices > 0:
            gl.glDrawElements(
                self._primitive_type.value,
                self._total_indices,
                gl.GL_UNSIGNED_INT,
                None
            )
        else:
            gl.glDrawArrays(
                self._primitive_type.value,
                0,
                self._total_vertices
            )

        gl.glBindVertexArray(0)

    def cleanup(self) -> None:
        """OpenGLリソースを解放"""
        if self._vbo != 0:
            gl.glDeleteBuffers(1, [self._vbo])
            self._vbo = 0

        if self._ebo != 0:
            gl.glDeleteBuffers(1, [self._ebo])
            self._ebo = 0

        if self._vao != 0:
            gl.glDeleteVertexArrays(1, [self._vao])
            self._vao = 0

    def _apply_transform(self, vertices: np.ndarray, transform: np.ndarray) -> np.ndarray:
        """
        頂点データにTransform行列を適用

        Args:
            vertices: 頂点データ（Nx6: x,y,z,r,g,b）
            transform: Model変換行列（4x4）

        Returns:
            変換後の頂点データ
        """
        if vertices.size == 0:
            return vertices

        # 位置（xyz）と色（rgb）を分離
        positions = vertices[:, :3]  # (N, 3)
        colors = vertices[:, 3:6]    # (N, 3)

        # 同次座標に変換（w=1を追加）
        positions_homogeneous = np.hstack([positions, np.ones((len(positions), 1))])  # (N, 4)

        # Transform行列を適用（行列積）
        # (4, 4) @ (N, 4).T = (4, N) -> .T = (N, 4)
        transformed_positions = (transform @ positions_homogeneous.T).T

        # 同次座標から3D座標に戻す（wで除算）
        transformed_positions = transformed_positions[:, :3] / transformed_positions[:, 3:4]

        # 位置と色を再結合
        result = np.hstack([transformed_positions, colors])

        return result.astype(np.float32)

    def _combine_indices(self) -> Optional[np.ndarray]:
        """
        各バッチのインデックスを結合

        各バッチの頂点オフセットを考慮してインデックスを調整

        Returns:
            結合されたインデックス配列
        """
        if not self._use_indices:
            return None

        combined = []

        for batch in self._batches:
            if batch.indices is not None:
                # 頂点オフセットを加算
                adjusted_indices = batch.indices + batch.vertex_offset
                combined.append(adjusted_indices)

        if combined:
            return np.concatenate(combined, axis=0).astype(np.uint32)

        return None

    def _create_buffers(self, vertices: np.ndarray, indices: Optional[np.ndarray]) -> None:
        """
        OpenGLバッファを作成

        Args:
            vertices: 結合された頂点データ
            indices: 結合されたインデックスデータ（Optional）
        """
        # 既存のバッファを削除
        self.cleanup()

        if vertices.size == 0:
            return

        # VAO作成
        self._vao = gl.glGenVertexArrays(1)
        gl.glBindVertexArray(self._vao)

        # VBO作成
        self._vbo = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._vbo)
        gl.glBufferData(
            gl.GL_ARRAY_BUFFER,
            vertices.nbytes,
            vertices,
            gl.GL_STATIC_DRAW
        )

        # 頂点属性設定
        stride = 6 * vertices.itemsize  # 6 floats per vertex (x,y,z,r,g,b)

        # 位置属性 (location=0)
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, stride, gl.ctypes.c_void_p(0))

        # 色属性 (location=1)
        gl.glEnableVertexAttribArray(1)
        gl.glVertexAttribPointer(1, 3, gl.GL_FLOAT, gl.GL_FALSE, stride, gl.ctypes.c_void_p(3 * vertices.itemsize))

        # EBO作成（インデックス使用の場合）
        if indices is not None and indices.size > 0:
            self._ebo = gl.glGenBuffers(1)
            gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self._ebo)
            gl.glBufferData(
                gl.GL_ELEMENT_ARRAY_BUFFER,
                indices.nbytes,
                indices,
                gl.GL_STATIC_DRAW
            )

        gl.glBindVertexArray(0)

    @property
    def batch_count(self) -> int:
        """バッチ内のジオメトリ数"""
        return len(self._batches)

    @property
    def total_vertices(self) -> int:
        """総頂点数"""
        return self._total_vertices

    @property
    def total_indices(self) -> int:
        """総インデックス数"""
        return self._total_indices

    def __del__(self):
        """デストラクタ"""
        self.cleanup()
