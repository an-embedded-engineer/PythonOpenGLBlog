"""
ジオメトリモジュール

基本形状（点・線・三角形）の描画を提供
"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Tuple, Optional, Protocol

import numpy as np
import OpenGL.GL as gl

from src.utils.logger import logger


class BufferManager(Protocol):
    """
    バッファ管理インターフェース

    OpenGL依存部分を抽象化し、テスト可能にする
    """

    def create_buffers(self, vertices: np.ndarray) -> Tuple[int, int, int]:
        """
        VBO/VAOを作成する

        Args:
            vertices: 頂点データ

        Returns:
            (vao, vbo, vertex_count)
        """
        ...

    def create_indexed_buffers(self, vertices: np.ndarray, indices: np.ndarray) -> Tuple[int, int, int, int]:
        """
        VBO/VAO/EBOを作成する

        Args:
            vertices: 頂点データ
            indices: インデックスデータ

        Returns:
            (vao, vbo, ebo, index_count)
        """
        ...

    def delete_buffers(self, vao: int, vbo: int, ebo: int) -> None:
        """バッファを削除する"""
        ...

    def draw_arrays(self, vao: int, primitive_type: int, vertex_count: int) -> None:
        """配列描画"""
        ...

    def draw_elements(self, vao: int, primitive_type: int, index_count: int) -> None:
        """インデックス描画"""
        ...


class OpenGLBufferManager:
    """OpenGLバッファマネージャー（実装）"""

    def create_buffers(self, vertices: np.ndarray) -> Tuple[int, int, int]:
        """VBO/VAOを作成する"""
        vao = gl.glGenVertexArrays(1)
        gl.glBindVertexArray(vao)

        vbo = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices, gl.GL_STATIC_DRAW)

        stride = 6 * vertices.itemsize
        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, stride, None)
        gl.glEnableVertexAttribArray(0)

        import ctypes
        offset = 3 * vertices.itemsize
        gl.glVertexAttribPointer(1, 3, gl.GL_FLOAT, gl.GL_FALSE, stride, ctypes.c_void_p(offset))
        gl.glEnableVertexAttribArray(1)

        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glBindVertexArray(0)

        vertex_count = len(vertices) // 6
        return vao, vbo, vertex_count

    def create_indexed_buffers(self, vertices: np.ndarray, indices: np.ndarray) -> Tuple[int, int, int, int]:
        """VBO/VAO/EBOを作成する"""
        vao = gl.glGenVertexArrays(1)
        gl.glBindVertexArray(vao)

        vbo = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices, gl.GL_STATIC_DRAW)

        ebo = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, ebo)
        gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, gl.GL_STATIC_DRAW)

        stride = 6 * vertices.itemsize
        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, stride, None)
        gl.glEnableVertexAttribArray(0)

        import ctypes
        offset = 3 * vertices.itemsize
        gl.glVertexAttribPointer(1, 3, gl.GL_FLOAT, gl.GL_FALSE, stride, ctypes.c_void_p(offset))
        gl.glEnableVertexAttribArray(1)

        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glBindVertexArray(0)

        index_count = len(indices)
        return vao, vbo, ebo, index_count

    def delete_buffers(self, vao: int, vbo: int, ebo: int) -> None:
        """バッファを削除する"""
        if ebo:
            gl.glDeleteBuffers(1, [ebo])
        if vbo:
            gl.glDeleteBuffers(1, [vbo])
        if vao:
            gl.glDeleteVertexArrays(1, [vao])

    def draw_arrays(self, vao: int, primitive_type: int, vertex_count: int) -> None:
        """配列描画"""
        gl.glBindVertexArray(vao)
        gl.glDrawArrays(primitive_type, 0, vertex_count)
        gl.glBindVertexArray(0)

    def draw_elements(self, vao: int, primitive_type: int, index_count: int) -> None:
        """インデックス描画"""
        gl.glBindVertexArray(vao)
        gl.glDrawElements(primitive_type, index_count, gl.GL_UNSIGNED_INT, None)
        gl.glBindVertexArray(0)


class PrimitiveType(Enum):
    """描画プリミティブタイプ"""
    POINTS = gl.GL_POINTS
    LINES = gl.GL_LINES
    LINE_STRIP = gl.GL_LINE_STRIP
    LINE_LOOP = gl.GL_LINE_LOOP
    TRIANGLES = gl.GL_TRIANGLES
    TRIANGLE_STRIP = gl.GL_TRIANGLE_STRIP
    TRIANGLE_FAN = gl.GL_TRIANGLE_FAN


class GeometryBase(ABC):
    """
    ジオメトリの基底クラス

    VBO/VAOを管理し、描画機能を提供する抽象クラス
    """

    # デフォルトのバッファマネージャー（OpenGL実装）
    _default_buffer_manager: Optional[BufferManager] = None

    def __init__(self, buffer_manager: Optional[BufferManager] = None) -> None:
        """
        ジオメトリを初期化する

        Args:
            buffer_manager: バッファマネージャー（Noneの場合はデフォルトを使用）
        """
        self._vao: int = 0
        self._vbo: int = 0
        self._ebo: int = 0
        self._vertex_count: int = 0
        self._index_count: int = 0
        self._is_initialized: bool = False
        self._use_indices: bool = False

        # バッファマネージャーの設定
        if buffer_manager is None:
            if GeometryBase._default_buffer_manager is None:
                GeometryBase._default_buffer_manager = OpenGLBufferManager()
            self._buffer_manager = GeometryBase._default_buffer_manager
        else:
            self._buffer_manager = buffer_manager

    @property
    @abstractmethod
    def primitive_type(self) -> PrimitiveType:
        """描画プリミティブタイプを取得"""
        pass

    @property
    def vertex_count(self) -> int:
        """頂点数を取得"""
        return self._vertex_count

    @property
    def index_count(self) -> int:
        """インデックス数を取得"""
        return self._index_count

    @property
    def is_initialized(self) -> bool:
        """初期化済みかどうか"""
        return self._is_initialized

    def _create_buffers(self, vertices: np.ndarray) -> None:
        """
        VBO/VAOを作成する

        Args:
            vertices: 頂点データ（位置x,y,z + 色r,g,b）
        """
        if self._is_initialized:
            self._delete_buffers()

        self._vao, self._vbo, self._vertex_count = self._buffer_manager.create_buffers(vertices)
        self._is_initialized = True
        self._use_indices = False

    def _create_indexed_buffers(self, vertices: np.ndarray, indices: np.ndarray) -> None:
        """
        VBO/VAO/EBOを作成する（インデックス付き描画用）

        Args:
            vertices: 頂点データ（位置x,y,z + 色r,g,b）
            indices: インデックスデータ
        """
        if self._is_initialized:
            self._delete_buffers()

        self._vao, self._vbo, self._ebo, self._index_count = self._buffer_manager.create_indexed_buffers(
            vertices, indices
        )
        self._vertex_count = len(vertices) // 6
        self._is_initialized = True
        self._use_indices = True

    def _delete_buffers(self) -> None:
        """VBO/VAO/EBOを削除する"""
        if self._is_initialized:
            self._buffer_manager.delete_buffers(self._vao, self._vbo, self._ebo)
            self._vao = 0
            self._vbo = 0
            self._ebo = 0
        self._is_initialized = False
        self._vertex_count = 0
        self._index_count = 0
        self._use_indices = False

    def draw(self) -> None:
        """ジオメトリを描画する"""
        if not self._is_initialized:
            return

        if self._use_indices:
            self._buffer_manager.draw_elements(self._vao, self.primitive_type.value, self._index_count)
        else:
            self._buffer_manager.draw_arrays(self._vao, self.primitive_type.value, self._vertex_count)

    @abstractmethod
    def get_vertex_data(self) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        バッチレンダリング用の頂点データを取得

        Returns:
            (vertices, indices): 頂点データとインデックスデータ（インデックス不使用時はNone）
            vertices: Nx6 array (x,y,z,r,g,b)
            indices: インデックス配列（Optional）
        """
        pass

    def cleanup(self) -> None:
        """リソースを解放する"""
        self._delete_buffers()

    def __del__(self) -> None:
        """デストラクタ"""
        # OpenGLコンテキストがまだ有効な場合のみクリーンアップ
        # Note: プログラム終了時はコンテキストが無効な場合がある
        pass


class PointGeometry(GeometryBase):
    """
    点ジオメトリクラス

    GL_POINTSを使用して点を描画
    """

    def __init__(
        self,
        points: Optional[List[Tuple[float, float, float, float, float, float]]] = None,
        buffer_manager: Optional[BufferManager] = None
    ) -> None:
        """
        点ジオメトリを初期化する

        Args:
            points: 点のリスト [(x, y, z, r, g, b), ...]
            buffer_manager: バッファマネージャー（テスト用）
        """
        super().__init__(buffer_manager)
        self._points: List[Tuple[float, float, float, float, float, float]] = []
        self._point_size: float = 5.0

        if points:
            self._points = list(points)
            self._update_buffers()

        logger.info(f"PointGeometry initialized with {len(self._points)} points")

    @property
    def primitive_type(self) -> PrimitiveType:
        return PrimitiveType.POINTS

    @property
    def point_size(self) -> float:
        """点のサイズを取得"""
        return self._point_size

    def set_point_size(self, size: float) -> None:
        """点のサイズを設定"""
        self._point_size = max(1.0, size)

    @property
    def points(self) -> List[Tuple[float, float, float, float, float, float]]:
        """点のリストを取得"""
        return self._points.copy()

    def add_point(self, x: float, y: float, z: float, r: float = 1.0, g: float = 1.0, b: float = 1.0) -> None:
        """
        点を追加する

        Args:
            x, y, z: 位置
            r, g, b: 色（0.0〜1.0）
        """
        self._points.append((x, y, z, r, g, b))
        self._update_buffers()

    def clear(self) -> None:
        """すべての点をクリアする"""
        self._points.clear()
        self._delete_buffers()

    def _update_buffers(self) -> None:
        """バッファを更新する"""
        if not self._points:
            self._delete_buffers()
            return

        vertices = np.array(self._points, dtype=np.float32).flatten()
        self._create_buffers(vertices)

    def get_vertex_data(self) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """バッチレンダリング用の頂点データを取得"""
        if not self._points:
            return np.array([], dtype=np.float32).reshape(0, 6), None

        vertices = np.array(self._points, dtype=np.float32)
        return vertices, None

    def draw(self) -> None:
        """点を描画する"""
        if not self._is_initialized:
            return

        # 点のサイズを設定
        gl.glPointSize(self._point_size)

        super().draw()


class LineGeometry(GeometryBase):
    """
    線ジオメトリクラス

    GL_LINESを使用して線分を描画
    """

    def __init__(
        self,
        lines: Optional[List[Tuple[
            Tuple[float, float, float, float, float, float],
            Tuple[float, float, float, float, float, float]
        ]]] = None,
        buffer_manager: Optional[BufferManager] = None
    ) -> None:
        """
        線ジオメトリを初期化する

        Args:
            lines: 線分のリスト [((x1,y1,z1,r1,g1,b1), (x2,y2,z2,r2,g2,b2)), ...]
            buffer_manager: バッファマネージャー（テスト用）
        """
        super().__init__(buffer_manager)
        self._lines: List[Tuple[
            Tuple[float, float, float, float, float, float],
            Tuple[float, float, float, float, float, float]
        ]] = []
        self._line_width: float = 1.0

        if lines:
            self._lines = list(lines)
            self._update_buffers()

        logger.info(f"LineGeometry initialized with {len(self._lines)} lines")

    @property
    def primitive_type(self) -> PrimitiveType:
        return PrimitiveType.LINES

    @property
    def line_width(self) -> float:
        """線の太さを取得"""
        return self._line_width

    def set_line_width(self, width: float) -> None:
        """線の太さを設定"""
        self._line_width = max(1.0, width)

    @property
    def lines(self) -> List[Tuple[
        Tuple[float, float, float, float, float, float],
        Tuple[float, float, float, float, float, float]
    ]]:
        """線分のリストを取得"""
        return self._lines.copy()

    def add_line(
        self,
        x1: float, y1: float, z1: float,
        x2: float, y2: float, z2: float,
        r: float = 1.0, g: float = 1.0, b: float = 1.0
    ) -> None:
        """
        線分を追加する（単色）

        Args:
            x1, y1, z1: 始点
            x2, y2, z2: 終点
            r, g, b: 色（0.0〜1.0）
        """
        self._lines.append((
            (x1, y1, z1, r, g, b),
            (x2, y2, z2, r, g, b)
        ))
        self._update_buffers()

    def add_line_colored(
        self,
        x1: float, y1: float, z1: float, r1: float, g1: float, b1: float,
        x2: float, y2: float, z2: float, r2: float, g2: float, b2: float
    ) -> None:
        """
        線分を追加する（グラデーション）

        Args:
            x1, y1, z1, r1, g1, b1: 始点の位置と色
            x2, y2, z2, r2, g2, b2: 終点の位置と色
        """
        self._lines.append((
            (x1, y1, z1, r1, g1, b1),
            (x2, y2, z2, r2, g2, b2)
        ))
        self._update_buffers()

    def clear(self) -> None:
        """すべての線分をクリアする"""
        self._lines.clear()
        self._delete_buffers()

    def _update_buffers(self) -> None:
        """バッファを更新する"""
        if not self._lines:
            self._delete_buffers()
            return

        # 線分を頂点配列に変換
        vertices = []
        for p1, p2 in self._lines:
            vertices.extend(p1)
            vertices.extend(p2)

        vertices = np.array(vertices, dtype=np.float32)
        self._create_buffers(vertices)
    def get_vertex_data(self) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """バッチレンダリング用の頂点データを取得"""
        if not self._lines:
            return np.array([], dtype=np.float32).reshape(0, 6), None

        # 線を頂点配列に変換
        vertices = []
        for v1, v2 in self._lines:
            vertices.extend(v1)
            vertices.extend(v2)

        vertices = np.array(vertices, dtype=np.float32).reshape(-1, 6)
        return vertices, None
    def draw(self) -> None:
        """線分を描画する"""
        if not self._is_initialized:
            return

        # 線の太さを設定
        # Note: macOS Core Profileでは1.0より大きい値はサポートされない場合がある
        try:
            gl.glLineWidth(self._line_width)
        except gl.GLError:
            gl.glLineWidth(1.0)

        super().draw()


class TriangleGeometry(GeometryBase):
    """
    三角形ジオメトリクラス

    GL_TRIANGLESを使用して三角形を描画
    """

    def __init__(
        self,
        triangles: Optional[List[Tuple[
            Tuple[float, float, float, float, float, float],
            Tuple[float, float, float, float, float, float],
            Tuple[float, float, float, float, float, float]
        ]]] = None,
        buffer_manager: Optional[BufferManager] = None
    ) -> None:
        """
        三角形ジオメトリを初期化する

        Args:
            triangles: 三角形のリスト [((v1), (v2), (v3)), ...]
                       各頂点は (x, y, z, r, g, b)
            buffer_manager: バッファマネージャー（テスト用）
        """
        super().__init__(buffer_manager)
        self._triangles: List[Tuple[
            Tuple[float, float, float, float, float, float],
            Tuple[float, float, float, float, float, float],
            Tuple[float, float, float, float, float, float]
        ]] = []

        if triangles:
            self._triangles = list(triangles)
            self._update_buffers()

        logger.info(f"TriangleGeometry initialized with {len(self._triangles)} triangles")

    @property
    def primitive_type(self) -> PrimitiveType:
        return PrimitiveType.TRIANGLES

    @property
    def triangles(self) -> List[Tuple[
        Tuple[float, float, float, float, float, float],
        Tuple[float, float, float, float, float, float],
        Tuple[float, float, float, float, float, float]
    ]]:
        """三角形のリストを取得"""
        return self._triangles.copy()

    def add_triangle(
        self,
        x1: float, y1: float, z1: float,
        x2: float, y2: float, z2: float,
        x3: float, y3: float, z3: float,
        r: float = 1.0, g: float = 1.0, b: float = 1.0
    ) -> None:
        """
        三角形を追加する（単色）

        Args:
            x1, y1, z1: 頂点1
            x2, y2, z2: 頂点2
            x3, y3, z3: 頂点3
            r, g, b: 色（0.0〜1.0）
        """
        self._triangles.append((
            (x1, y1, z1, r, g, b),
            (x2, y2, z2, r, g, b),
            (x3, y3, z3, r, g, b)
        ))
        self._update_buffers()

    def add_triangle_colored(
        self,
        x1: float, y1: float, z1: float, r1: float, g1: float, b1: float,
        x2: float, y2: float, z2: float, r2: float, g2: float, b2: float,
        x3: float, y3: float, z3: float, r3: float, g3: float, b3: float
    ) -> None:
        """
        三角形を追加する（頂点ごとに色指定）

        Args:
            x1, y1, z1, r1, g1, b1: 頂点1の位置と色
            x2, y2, z2, r2, g2, b2: 頂点2の位置と色
            x3, y3, z3, r3, g3, b3: 頂点3の位置と色
        """
        self._triangles.append((
            (x1, y1, z1, r1, g1, b1),
            (x2, y2, z2, r2, g2, b2),
            (x3, y3, z3, r3, g3, b3)
        ))
        self._update_buffers()

    def clear(self) -> None:
        """すべての三角形をクリアする"""
        self._triangles.clear()
        self._delete_buffers()

    def _update_buffers(self) -> None:
        """バッファを更新する"""
        if not self._triangles:
            self._delete_buffers()
            return

        # 三角形を頂点配列に変換
        vertices = []
        for v1, v2, v3 in self._triangles:
            vertices.extend(v1)
            vertices.extend(v2)
            vertices.extend(v3)

        vertices = np.array(vertices, dtype=np.float32)
        self._create_buffers(vertices)

    def get_vertex_data(self) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """バッチレンダリング用の頂点データを取得"""
        if not self._triangles:
            return np.array([], dtype=np.float32).reshape(0, 6), None

        # 三角形を頂点配列に変換
        vertices = []
        for v1, v2, v3 in self._triangles:
            vertices.extend(v1)
            vertices.extend(v2)
            vertices.extend(v3)

        vertices = np.array(vertices, dtype=np.float32).reshape(-1, 6)
        return vertices, None


class RectangleGeometry(GeometryBase):
    """
    四角形ジオメトリクラス

    EBO（インデックスバッファ）を使用して四角形を描画
    """

    def __init__(
        self,
        width: float = 1.0,
        height: float = 1.0,
        r: float = 1.0,
        g: float = 1.0,
        b: float = 1.0,
        buffer_manager: Optional[BufferManager] = None,
        lazy_init: bool = False
    ) -> None:
        """
        四角形ジオメトリを初期化する

        Args:
            width: 幅
            height: 高さ
            r, g, b: 色（0.0〜1.0）
            buffer_manager: バッファマネージャー（テスト用）
            lazy_init: True の場合、バッファ作成を遅延（テスト用）
        """
        super().__init__(buffer_manager)
        self._width = width
        self._height = height
        self._color = (r, g, b)

        if not lazy_init:
            self._update_buffers()

        logger.info(f"RectangleGeometry initialized: {width}x{height}")

    @property
    def primitive_type(self) -> PrimitiveType:
        return PrimitiveType.TRIANGLES

    def set_size(self, width: float, height: float) -> None:
        """サイズを変更"""
        self._width = width
        self._height = height
        self._update_buffers()

    def set_color(self, r: float, g: float, b: float) -> None:
        """色を変更"""
        self._color = (r, g, b)
        self._update_buffers()

    def set_random_colors(self) -> None:
        """各頂点にランダムな色を設定（グラデーション効果）"""
        import random
        w = self._width / 2.0
        h = self._height / 2.0

        # 各頂点に異なるランダム色を設定
        vertices = np.array([
            # 位置           色
            -w, -h, 0.0,  random.random(), random.random(), random.random(),  # 左下
             w, -h, 0.0,  random.random(), random.random(), random.random(),  # 右下
             w,  h, 0.0,  random.random(), random.random(), random.random(),  # 右上
            -w,  h, 0.0,  random.random(), random.random(), random.random(),  # 左上
        ], dtype=np.float32)

        indices = np.array([
            0, 1, 2,
            2, 3, 0,
        ], dtype=np.uint32)

        self._create_indexed_buffers(vertices, indices)

    def _update_buffers(self) -> None:
        """バッファを更新する"""
        w = self._width / 2.0
        h = self._height / 2.0
        r, g, b = self._color

        # 頂点データ（4頂点）
        vertices = np.array([
            # 位置           色
            -w, -h, 0.0,  r, g, b,  # 左下
             w, -h, 0.0,  r, g, b,  # 右下
             w,  h, 0.0,  r, g, b,  # 右上
            -w,  h, 0.0,  r, g, b,  # 左上
        ], dtype=np.float32)

        # インデックスデータ（2つの三角形）
        indices = np.array([
            0, 1, 2,  # 三角形1（左下、右下、右上）
            2, 3, 0,  # 三角形2（右上、左上、左下）
        ], dtype=np.uint32)

        self._create_indexed_buffers(vertices, indices)

    def get_vertex_data(self) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """バッチレンダリング用の頂点データを取得"""
        w = self._width / 2.0
        h = self._height / 2.0
        r, g, b = self._color

        # 頂点データ（4頂点）
        vertices = np.array([
            # 位置           色
            -w, -h, 0.0,  r, g, b,  # 左下
             w, -h, 0.0,  r, g, b,  # 右下
             w,  h, 0.0,  r, g, b,  # 右上
            -w,  h, 0.0,  r, g, b,  # 左上
        ], dtype=np.float32).reshape(4, 6)

        # インデックスデータ
        indices = np.array([
            0, 1, 2,
            2, 3, 0,
        ], dtype=np.uint32)

        return vertices, indices


class CubeGeometry(GeometryBase):
    """
    立方体ジオメトリクラス

    EBO（インデックスバッファ）を使用して立方体を描画
    """

    def __init__(
        self,
        size: float = 1.0,
        r: float = 1.0,
        g: float = 1.0,
        b: float = 1.0,
        buffer_manager: Optional[BufferManager] = None,
        lazy_init: bool = False
    ) -> None:
        """
        立方体ジオメトリを初期化する

        Args:
            size: 一辺の長さ
            r, g, b: 色（0.0〜1.0）
            buffer_manager: バッファマネージャー（テスト用）
            lazy_init: True の場合、バッファ作成を遅延（テスト用）
        """
        super().__init__(buffer_manager)
        self._size = size
        self._color = (r, g, b)

        if not lazy_init:
            self._update_buffers()

        logger.info(f"CubeGeometry initialized: size={size}")

    @property
    def primitive_type(self) -> PrimitiveType:
        return PrimitiveType.TRIANGLES

    def set_size(self, size: float) -> None:
        """サイズを変更"""
        self._size = size
        self._update_buffers()

    def set_color(self, r: float, g: float, b: float) -> None:
        """色を変更"""
        self._color = (r, g, b)
        self._update_buffers()

    def set_random_colors(self) -> None:
        """各頂点にランダムな色を設定（グラデーション効果）"""
        import random
        s = self._size / 2.0

        # 8頂点にそれぞれ異なるランダム色を設定
        vertices = np.array([
            # 位置              色
            -s, -s,  s,  random.random(), random.random(), random.random(),  # 0
             s, -s,  s,  random.random(), random.random(), random.random(),  # 1
             s,  s,  s,  random.random(), random.random(), random.random(),  # 2
            -s,  s,  s,  random.random(), random.random(), random.random(),  # 3
            -s, -s, -s,  random.random(), random.random(), random.random(),  # 4
             s, -s, -s,  random.random(), random.random(), random.random(),  # 5
             s,  s, -s,  random.random(), random.random(), random.random(),  # 6
            -s,  s, -s,  random.random(), random.random(), random.random(),  # 7
        ], dtype=np.float32)

        indices = np.array([
            0, 1, 2, 0, 2, 3,  # 前面
            5, 4, 7, 5, 7, 6,  # 背面
            4, 0, 3, 4, 3, 7,  # 左面
            1, 5, 6, 1, 6, 2,  # 右面
            3, 2, 6, 3, 6, 7,  # 上面
            4, 5, 1, 4, 1, 0,  # 底面
        ], dtype=np.uint32)

        self._create_indexed_buffers(vertices, indices)

    def _update_buffers(self) -> None:
        """バッファを更新する"""
        s = self._size / 2.0
        r, g, b = self._color

        # 立方体の8頂点
        vertices = np.array([
            # 位置           色
            # 前面（Z+）
            -s, -s,  s,  r, g, b,  # 0: 左下前
             s, -s,  s,  r, g, b,  # 1: 右下前
             s,  s,  s,  r, g, b,  # 2: 右上前
            -s,  s,  s,  r, g, b,  # 3: 左上前
            # 背面（Z-）
            -s, -s, -s,  r, g, b,  # 4: 左下後
             s, -s, -s,  r, g, b,  # 5: 右下後
             s,  s, -s,  r, g, b,  # 6: 右上後
            -s,  s, -s,  r, g, b,  # 7: 左上後
        ], dtype=np.float32)

        # インデックスデータ（6面 × 2三角形 = 12三角形 = 36インデックス）
        indices = np.array([
            # 前面（Z+）
            0, 1, 2,  2, 3, 0,
            # 背面（Z-）
            5, 4, 7,  7, 6, 5,
            # 左面（X-）
            4, 0, 3,  3, 7, 4,
            # 右面（X+）
            1, 5, 6,  6, 2, 1,
            # 上面（Y+）
            3, 2, 6,  6, 7, 3,
            # 下面（Y-）
            4, 5, 1,  1, 0, 4,
        ], dtype=np.uint32)

        self._create_indexed_buffers(vertices, indices)

    def get_vertex_data(self) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """バッチレンダリング用の頂点データを取得"""
        s = self._size / 2.0
        r, g, b = self._color

        # 立方体の8頂点
        vertices = np.array([
            # 位置           色
            # 前面（Z+）
            -s, -s,  s,  r, g, b,  # 0: 左下前
             s, -s,  s,  r, g, b,  # 1: 右下前
             s,  s,  s,  r, g, b,  # 2: 右上前
            -s,  s,  s,  r, g, b,  # 3: 左上前
            # 背面（Z-）
            -s, -s, -s,  r, g, b,  # 4: 左下後
             s, -s, -s,  r, g, b,  # 5: 右下後
             s,  s, -s,  r, g, b,  # 6: 右上後
            -s,  s, -s,  r, g, b,  # 7: 左上後
        ], dtype=np.float32).reshape(8, 6)

        # インデックスデータ
        indices = np.array([
            # 前面（Z+）
            0, 1, 2,  2, 3, 0,
            # 背面（Z-）
            5, 4, 7,  7, 6, 5,
            # 左面（X-）
            4, 0, 3,  3, 7, 4,
            # 右面（X+）
            1, 5, 6,  6, 2, 1,
            # 上面（Y+）
            3, 2, 6,  6, 7, 3,
            # 下面（Y-）
            4, 5, 1,  1, 0, 4,
        ], dtype=np.uint32)

        return vertices, indices


class SphereGeometry(GeometryBase):
    """
    球体ジオメトリクラス

    経度・緯度分割により球体を生成し、EBOを使用して描画
    """

    def __init__(
        self,
        radius: float = 1.0,
        segments: int = 32,
        rings: int = 16,
        r: float = 1.0,
        g: float = 1.0,
        b: float = 1.0,
        buffer_manager: Optional[BufferManager] = None,
        lazy_init: bool = False
    ) -> None:
        """
        球体ジオメトリを初期化する

        Args:
            radius: 半径
            segments: 経度方向の分割数
            rings: 緯度方向の分割数
            r, g, b: 色（0.0〜1.0）
            buffer_manager: バッファマネージャー（テスト用）
            lazy_init: True の場合、バッファ作成を遅延（テスト用）
        """
        super().__init__(buffer_manager)
        self._radius = radius
        self._segments = max(3, segments)
        self._rings = max(2, rings)
        self._color = (r, g, b)

        if not lazy_init:
            self._update_buffers()

        logger.info(f"SphereGeometry initialized: radius={radius}, segments={segments}, rings={rings}")

    @property
    def primitive_type(self) -> PrimitiveType:
        return PrimitiveType.TRIANGLES

    def set_radius(self, radius: float) -> None:
        """半径を変更"""
        self._radius = radius
        self._update_buffers()

    def set_color(self, r: float, g: float, b: float) -> None:
        """色を変更"""
        self._color = (r, g, b)
        self._update_buffers()

    def set_random_colors(self) -> None:
        """各頂点にランダムな色を設定（グラデーション効果）"""
        import random
        vertices = []
        indices = []

        # 頂点生成（各頂点にランダム色）
        for ring in range(self._rings + 1):
            theta = np.pi * ring / self._rings
            sin_theta = np.sin(theta)
            cos_theta = np.cos(theta)

            for segment in range(self._segments + 1):
                phi = 2.0 * np.pi * segment / self._segments
                sin_phi = np.sin(phi)
                cos_phi = np.cos(phi)

                x = self._radius * sin_theta * cos_phi
                y = self._radius * cos_theta
                z = self._radius * sin_theta * sin_phi

                # 各頂点にランダム色を設定
                vertices.extend([x, y, z, random.random(), random.random(), random.random()])

        # インデックス生成
        for ring in range(self._rings):
            for segment in range(self._segments):
                first = ring * (self._segments + 1) + segment
                second = first + self._segments + 1

                indices.extend([first, second, first + 1])
                indices.extend([second, second + 1, first + 1])

        vertices = np.array(vertices, dtype=np.float32)
        indices = np.array(indices, dtype=np.uint32)

        self._create_indexed_buffers(vertices, indices)

    def _update_buffers(self) -> None:
        """バッファを更新する"""
        r, g, b = self._color
        vertices = []
        indices = []

        # 頂点生成
        for ring in range(self._rings + 1):
            theta = np.pi * ring / self._rings  # 緯度角（0〜π）
            sin_theta = np.sin(theta)
            cos_theta = np.cos(theta)

            for segment in range(self._segments + 1):
                phi = 2.0 * np.pi * segment / self._segments  # 経度角（0〜2π）
                sin_phi = np.sin(phi)
                cos_phi = np.cos(phi)

                # 球面座標から直交座標へ変換
                x = self._radius * sin_theta * cos_phi
                y = self._radius * cos_theta
                z = self._radius * sin_theta * sin_phi

                vertices.extend([x, y, z, r, g, b])

        # インデックス生成
        for ring in range(self._rings):
            for segment in range(self._segments):
                # 現在のリングの頂点インデックス
                first = ring * (self._segments + 1) + segment
                second = first + self._segments + 1

                # 三角形1
                indices.extend([first, second, first + 1])
                # 三角形2
                indices.extend([second, second + 1, first + 1])

        vertices = np.array(vertices, dtype=np.float32)
        indices = np.array(indices, dtype=np.uint32)

        self._create_indexed_buffers(vertices, indices)

    def get_vertex_data(self) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """バッチレンダリング用の頂点データを取得"""
        r, g, b = self._color
        vertices = []
        indices = []

        # 頂点生成
        for ring in range(self._rings + 1):
            theta = np.pi * ring / self._rings
            sin_theta = np.sin(theta)
            cos_theta = np.cos(theta)

            for segment in range(self._segments + 1):
                phi = 2.0 * np.pi * segment / self._segments
                sin_phi = np.sin(phi)
                cos_phi = np.cos(phi)

                x = self._radius * sin_theta * cos_phi
                y = self._radius * cos_theta
                z = self._radius * sin_theta * sin_phi

                vertices.extend([x, y, z, r, g, b])

        # インデックス生成
        for ring in range(self._rings):
            for segment in range(self._segments):
                first = ring * (self._segments + 1) + segment
                second = first + self._segments + 1

                indices.extend([first, second, first + 1])
                indices.extend([second, second + 1, first + 1])

        vertices = np.array(vertices, dtype=np.float32).reshape(-1, 6)
        indices = np.array(indices, dtype=np.uint32)

        return vertices, indices
