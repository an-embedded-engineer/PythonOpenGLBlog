"""
ジオメトリモジュールのユニットテスト

BufferManagerを使用してOpenGL依存部分をモック化
"""
import numpy as np
from typing import Tuple

from src.graphics.geometry import (
    PrimitiveType,
    PointGeometry,
    LineGeometry,
    TriangleGeometry,
    RectangleGeometry,
    CubeGeometry,
    SphereGeometry,
)


class MockBufferManager:
    """テスト用のモックBufferManager"""

    def __init__(self) -> None:
        self.create_buffers_called = False
        self.create_indexed_buffers_called = False
        self.delete_buffers_called = False
        self.draw_arrays_called = False
        self.draw_elements_called = False
        self.last_vertices = None
        self.last_indices = None

    def create_buffers(self, vertices: np.ndarray) -> Tuple[int, int, int]:
        """VBO/VAOを作成する（モック）"""
        self.create_buffers_called = True
        self.last_vertices = vertices
        vertex_count = len(vertices) // 6
        return 1, 2, vertex_count  # vao, vbo, vertex_count

    def create_indexed_buffers(self, vertices: np.ndarray, indices: np.ndarray) -> Tuple[int, int, int, int]:
        """VBO/VAO/EBOを作成する（モック）"""
        self.create_indexed_buffers_called = True
        self.last_vertices = vertices
        self.last_indices = indices
        index_count = len(indices)
        return 1, 2, 3, index_count  # vao, vbo, ebo, index_count

    def delete_buffers(self, vao: int, vbo: int, ebo: int) -> None:
        """バッファを削除する（モック）"""
        self.delete_buffers_called = True

    def draw_arrays(self, vao: int, primitive_type: int, vertex_count: int) -> None:
        """配列描画（モック）"""
        self.draw_arrays_called = True

    def draw_elements(self, vao: int, primitive_type: int, index_count: int) -> None:
        """インデックス描画（モック）"""
        self.draw_elements_called = True


class TestPrimitiveType:
    """PrimitiveType列挙型のテスト"""

    def test_points_value(self) -> None:
        """GL_POINTSの値テスト"""
        assert PrimitiveType.POINTS.value == 0

    def test_lines_value(self) -> None:
        """GL_LINESの値テスト"""
        assert PrimitiveType.LINES.value == 1

    def test_triangles_value(self) -> None:
        """GL_TRIANGLESの値テスト"""
        assert PrimitiveType.TRIANGLES.value == 4


class TestPointGeometry:
    """PointGeometryクラスのテスト"""

    def test_init_empty(self) -> None:
        """空の初期化テスト"""
        mock_manager = MockBufferManager()
        geom = PointGeometry(buffer_manager=mock_manager)
        assert geom.primitive_type == PrimitiveType.POINTS
        assert len(geom.points) == 0
        assert not mock_manager.create_buffers_called

    def test_init_with_points(self) -> None:
        """点データありの初期化テスト"""
        mock_manager = MockBufferManager()
        points = [(0.0, 0.0, 0.0, 1.0, 0.0, 0.0), (1.0, 1.0, 1.0, 0.0, 1.0, 0.0)]
        geom = PointGeometry(points=points, buffer_manager=mock_manager)
        assert len(geom.points) == 2
        assert mock_manager.create_buffers_called

    def test_add_point(self) -> None:
        """点追加テスト"""
        mock_manager = MockBufferManager()
        geom = PointGeometry(buffer_manager=mock_manager)
        geom.add_point(1.0, 2.0, 3.0, 1.0, 0.0, 0.0)
        assert len(geom.points) == 1
        assert mock_manager.create_buffers_called

    def test_clear(self) -> None:
        """クリアテスト"""
        mock_manager = MockBufferManager()
        geom = PointGeometry(buffer_manager=mock_manager)
        geom.add_point(1.0, 2.0, 3.0)
        geom.clear()
        assert len(geom.points) == 0
        assert mock_manager.delete_buffers_called


class TestLineGeometry:
    """LineGeometryクラスのテスト"""

    def test_init_empty(self) -> None:
        """空の初期化テスト"""
        mock_manager = MockBufferManager()
        geom = LineGeometry(buffer_manager=mock_manager)
        assert geom.primitive_type == PrimitiveType.LINES
        assert len(geom.lines) == 0

    def test_add_line(self) -> None:
        """線追加テスト"""
        mock_manager = MockBufferManager()
        geom = LineGeometry(buffer_manager=mock_manager)
        geom.add_line(0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0)
        assert len(geom.lines) == 1
        assert mock_manager.create_buffers_called


class TestTriangleGeometry:
    """TriangleGeometryクラスのテスト"""

    def test_init_empty(self) -> None:
        """空の初期化テスト"""
        mock_manager = MockBufferManager()
        geom = TriangleGeometry(buffer_manager=mock_manager)
        assert geom.primitive_type == PrimitiveType.TRIANGLES
        assert len(geom.triangles) == 0

    def test_add_triangle(self) -> None:
        """三角形追加テスト"""
        mock_manager = MockBufferManager()
        geom = TriangleGeometry(buffer_manager=mock_manager)
        geom.add_triangle(0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.5, 1.0, 0.0, 1.0, 0.0, 0.0)
        assert len(geom.triangles) == 1
        assert mock_manager.create_buffers_called


class TestRectangleGeometry:
    """RectangleGeometryクラスのテスト"""

    def test_init_lazy(self) -> None:
        """遅延初期化テスト"""
        mock_manager = MockBufferManager()
        geom = RectangleGeometry(buffer_manager=mock_manager, lazy_init=True)
        assert geom.primitive_type == PrimitiveType.TRIANGLES
        assert not mock_manager.create_indexed_buffers_called

    def test_init_normal(self) -> None:
        """通常初期化テスト"""
        mock_manager = MockBufferManager()
        geom = RectangleGeometry(width=2.0, height=3.0, buffer_manager=mock_manager)
        assert mock_manager.create_indexed_buffers_called
        assert geom._width == 2.0
        assert geom._height == 3.0

    def test_set_size(self) -> None:
        """サイズ変更テスト"""
        mock_manager = MockBufferManager()
        geom = RectangleGeometry(buffer_manager=mock_manager, lazy_init=True)
        geom.set_size(2.0, 3.0)
        assert geom._width == 2.0
        assert geom._height == 3.0
        assert mock_manager.create_indexed_buffers_called

    def test_set_color(self) -> None:
        """色変更テスト"""
        mock_manager = MockBufferManager()
        geom = RectangleGeometry(buffer_manager=mock_manager, lazy_init=True)
        geom.set_color(0.5, 0.6, 0.7)
        assert geom._color == (0.5, 0.6, 0.7)


class TestCubeGeometry:
    """CubeGeometryクラスのテスト"""

    def test_init_lazy(self) -> None:
        """遅延初期化テスト"""
        mock_manager = MockBufferManager()
        geom = CubeGeometry(buffer_manager=mock_manager, lazy_init=True)
        assert geom.primitive_type == PrimitiveType.TRIANGLES
        assert not mock_manager.create_indexed_buffers_called

    def test_init_normal(self) -> None:
        """通常初期化テスト"""
        mock_manager = MockBufferManager()
        geom = CubeGeometry(size=2.0, buffer_manager=mock_manager)
        assert mock_manager.create_indexed_buffers_called
        assert geom._size == 2.0
        # 8頂点 × 6 floats/vertex = 48 floats
        assert mock_manager.last_vertices is not None
        assert len(mock_manager.last_vertices) == 48
        # 6面 × 2三角形 × 3インデックス = 36インデックス
        assert mock_manager.last_indices is not None
        assert len(mock_manager.last_indices) == 36

    def test_set_size(self) -> None:
        """サイズ変更テスト"""
        mock_manager = MockBufferManager()
        geom = CubeGeometry(buffer_manager=mock_manager, lazy_init=True)
        geom.set_size(2.0)
        assert geom._size == 2.0


class TestSphereGeometry:
    """SphereGeometryクラスのテスト"""

    def test_init_lazy(self) -> None:
        """遅延初期化テスト"""
        mock_manager = MockBufferManager()
        geom = SphereGeometry(buffer_manager=mock_manager, lazy_init=True)
        assert geom.primitive_type == PrimitiveType.TRIANGLES
        assert not mock_manager.create_indexed_buffers_called

    def test_init_custom(self) -> None:
        """カスタム初期化テスト"""
        mock_manager = MockBufferManager()
        geom = SphereGeometry(radius=2.0, segments=16, rings=8, buffer_manager=mock_manager)
        assert geom._radius == 2.0
        assert geom._segments == 16
        assert geom._rings == 8
        assert mock_manager.create_indexed_buffers_called
        # (rings+1) * (segments+1) 頂点 × 6 floats/vertex
        expected_vertices = (8 + 1) * (16 + 1) * 6
        assert mock_manager.last_vertices is not None
        assert len(mock_manager.last_vertices) == expected_vertices
        # rings * segments * 2三角形 * 3インデックス
        expected_indices = 8 * 16 * 2 * 3
        assert mock_manager.last_indices is not None
        assert len(mock_manager.last_indices) == expected_indices

    def test_segments_minimum(self) -> None:
        """セグメント数の最小値テスト"""
        mock_manager = MockBufferManager()
        geom = SphereGeometry(segments=1, buffer_manager=mock_manager, lazy_init=True)
        assert geom._segments >= 3

    def test_rings_minimum(self) -> None:
        """リング数の最小値テスト"""
        mock_manager = MockBufferManager()
        geom = SphereGeometry(rings=1, buffer_manager=mock_manager, lazy_init=True)
        assert geom._rings >= 2
