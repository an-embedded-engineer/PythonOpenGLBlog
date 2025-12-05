"""
ジオメトリモジュール

基本形状（点・線・三角形）の描画を提供
"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Tuple, Optional

import numpy as np
import OpenGL.GL as gl

from src.utils.logger import logger


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

    def __init__(self) -> None:
        """ジオメトリを初期化する"""
        self._vao: int = 0
        self._vbo: int = 0
        self._vertex_count: int = 0
        self._is_initialized: bool = False

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
        import ctypes
        offset = 3 * vertices.itemsize
        gl.glVertexAttribPointer(1, 3, gl.GL_FLOAT, gl.GL_FALSE, stride, ctypes.c_void_p(offset))
        gl.glEnableVertexAttribArray(1)

        # バインド解除
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glBindVertexArray(0)

        self._vertex_count = len(vertices) // 6
        self._is_initialized = True

    def _delete_buffers(self) -> None:
        """VBO/VAOを削除する"""
        if self._vbo:
            gl.glDeleteBuffers(1, [self._vbo])
            self._vbo = 0
        if self._vao:
            gl.glDeleteVertexArrays(1, [self._vao])
            self._vao = 0
        self._is_initialized = False
        self._vertex_count = 0

    def draw(self) -> None:
        """ジオメトリを描画する"""
        if not self._is_initialized:
            return

        gl.glBindVertexArray(self._vao)
        gl.glDrawArrays(self.primitive_type.value, 0, self._vertex_count)
        gl.glBindVertexArray(0)

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

    def __init__(self, points: Optional[List[Tuple[float, float, float, float, float, float]]] = None) -> None:
        """
        点ジオメトリを初期化する

        Args:
            points: 点のリスト [(x, y, z, r, g, b), ...]
        """
        super().__init__()
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

    def __init__(self, lines: Optional[List[Tuple[
        Tuple[float, float, float, float, float, float],
        Tuple[float, float, float, float, float, float]
    ]]] = None) -> None:
        """
        線ジオメトリを初期化する

        Args:
            lines: 線分のリスト [((x1,y1,z1,r1,g1,b1), (x2,y2,z2,r2,g2,b2)), ...]
        """
        super().__init__()
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

    def __init__(self, triangles: Optional[List[Tuple[
        Tuple[float, float, float, float, float, float],
        Tuple[float, float, float, float, float, float],
        Tuple[float, float, float, float, float, float]
    ]]] = None) -> None:
        """
        三角形ジオメトリを初期化する

        Args:
            triangles: 三角形のリスト [((v1), (v2), (v3)), ...]
                       各頂点は (x, y, z, r, g, b)
        """
        super().__init__()
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
