"""
BatchRendererクラスのユニットテスト
"""
import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock

from src.graphics.batch_renderer import BatchRenderer, PrimitiveType, RenderBatch


class TestRenderBatch:
    """RenderBatchデータクラスのテスト"""

    def test_render_batch_creation(self):
        """RenderBatchの作成"""
        vertices = np.array([[0, 0, 0, 1, 0, 0]], dtype=np.float32)
        indices = np.array([0, 1, 2], dtype=np.uint32)
        transform = np.eye(4, dtype=np.float32)

        batch = RenderBatch(
            vertices=vertices,
            indices=indices,
            transform=transform
        )

        assert batch.vertices.shape == (1, 6)
        assert batch.indices is not None
        assert batch.indices.shape == (3,)
        assert batch.transform.shape == (4, 4)
        assert batch.vertex_offset == 0
        assert batch.vertex_count == 0
        assert batch.index_offset == 0
        assert batch.index_count == 0

    def test_render_batch_without_indices(self):
        """インデックスなしのRenderBatch"""
        vertices = np.array([[0, 0, 0, 1, 0, 0]], dtype=np.float32)
        transform = np.eye(4, dtype=np.float32)

        batch = RenderBatch(
            vertices=vertices,
            indices=None,
            transform=transform
        )

        assert batch.indices is None


class TestBatchRenderer:
    """BatchRendererクラスのテスト"""

    @pytest.fixture
    def mock_gl(self):
        """OpenGL関数のモック"""
        with patch('src.graphics.batch_renderer.gl') as mock:
            # VAO/VBO/EBO生成のモック
            mock.glGenVertexArrays.return_value = 1
            mock.glGenBuffers.side_effect = [2, 3]  # VBO=2, EBO=3
            yield mock

    def test_batch_renderer_initialization(self):
        """BatchRendererの初期化"""
        renderer = BatchRenderer(PrimitiveType.TRIANGLES)

        assert renderer._primitive_type == PrimitiveType.TRIANGLES
        assert renderer._batches == []
        assert renderer._vao == 0
        assert renderer._vbo == 0
        assert renderer._ebo == 0
        assert renderer._is_dirty is False
        assert renderer._use_indices is False
        assert renderer._total_vertices == 0
        assert renderer._total_indices == 0

    def test_add_geometry_basic(self):
        """ジオメトリの追加（基本）"""
        renderer = BatchRenderer(PrimitiveType.TRIANGLES)

        vertices = np.array([
            [0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
            [1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
            [0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
        ], dtype=np.float32)

        indices = np.array([0, 1, 2], dtype=np.uint32)
        transform = np.eye(4, dtype=np.float32)

        renderer.add_geometry(vertices, indices, transform)

        assert len(renderer._batches) == 1
        assert renderer._is_dirty is True
        assert renderer._use_indices is True
        assert renderer.batch_count == 1

    def test_add_geometry_without_indices(self):
        """インデックスなしのジオメトリ追加"""
        renderer = BatchRenderer(PrimitiveType.POINTS)

        vertices = np.array([
            [0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
        ], dtype=np.float32)

        transform = np.eye(4, dtype=np.float32)

        renderer.add_geometry(vertices, None, transform)

        assert len(renderer._batches) == 1
        assert renderer._batches[0].indices is None

    def test_add_empty_geometry(self):
        """空のジオメトリ追加（無視される）"""
        renderer = BatchRenderer(PrimitiveType.TRIANGLES)

        empty_vertices = np.array([], dtype=np.float32)
        transform = np.eye(4, dtype=np.float32)

        renderer.add_geometry(empty_vertices, None, transform)

        assert len(renderer._batches) == 0

    def test_add_multiple_geometries(self):
        """複数のジオメトリ追加"""
        renderer = BatchRenderer(PrimitiveType.TRIANGLES)

        for i in range(3):
            vertices = np.array([
                [float(i), 0.0, 0.0, 1.0, 0.0, 0.0],
                [float(i+1), 0.0, 0.0, 0.0, 1.0, 0.0],
                [float(i), 1.0, 0.0, 0.0, 0.0, 1.0],
            ], dtype=np.float32)

            indices = np.array([0, 1, 2], dtype=np.uint32)
            transform = np.eye(4, dtype=np.float32)

            renderer.add_geometry(vertices, indices, transform)

        assert renderer.batch_count == 3

    def test_clear(self):
        """バッチのクリア"""
        renderer = BatchRenderer(PrimitiveType.TRIANGLES)

        vertices = np.array([[0, 0, 0, 1, 0, 0]], dtype=np.float32)
        transform = np.eye(4, dtype=np.float32)
        renderer.add_geometry(vertices, None, transform)

        assert len(renderer._batches) == 1

        renderer.clear()

        assert len(renderer._batches) == 0
        assert renderer._is_dirty is True
        assert renderer._total_vertices == 0
        assert renderer._total_indices == 0

    def test_apply_transform_identity(self):
        """Transform適用（単位行列）"""
        renderer = BatchRenderer(PrimitiveType.TRIANGLES)

        vertices = np.array([
            [1.0, 2.0, 3.0, 1.0, 0.0, 0.0],
        ], dtype=np.float32)

        transform = np.eye(4, dtype=np.float32)

        result = renderer._apply_transform(vertices, transform)

        # 単位行列では変換なし
        np.testing.assert_array_almost_equal(result[:, :3], vertices[:, :3])
        np.testing.assert_array_almost_equal(result[:, 3:], vertices[:, 3:])

    def test_apply_transform_translation(self):
        """Transform適用（平行移動）"""
        renderer = BatchRenderer(PrimitiveType.TRIANGLES)

        vertices = np.array([
            [0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
        ], dtype=np.float32)

        # 平行移動行列（x+1, y+2, z+3）
        transform = np.array([
            [1, 0, 0, 1],
            [0, 1, 0, 2],
            [0, 0, 1, 3],
            [0, 0, 0, 1],
        ], dtype=np.float32)

        result = renderer._apply_transform(vertices, transform)

        # 位置が変換される
        expected_pos = np.array([[1.0, 2.0, 3.0]])
        np.testing.assert_array_almost_equal(result[:, :3], expected_pos)

        # 色は変わらない
        np.testing.assert_array_almost_equal(result[:, 3:], vertices[:, 3:])

    def test_apply_transform_scale(self):
        """Transform適用（スケール）"""
        renderer = BatchRenderer(PrimitiveType.TRIANGLES)

        vertices = np.array([
            [1.0, 2.0, 3.0, 1.0, 0.0, 0.0],
        ], dtype=np.float32)

        # スケール行列（2倍）
        transform = np.array([
            [2, 0, 0, 0],
            [0, 2, 0, 0],
            [0, 0, 2, 0],
            [0, 0, 0, 1],
        ], dtype=np.float32)

        result = renderer._apply_transform(vertices, transform)

        # 位置が2倍になる
        expected_pos = np.array([[2.0, 4.0, 6.0]])
        np.testing.assert_array_almost_equal(result[:, :3], expected_pos)

    def test_apply_transform_empty(self):
        """Transform適用（空の配列）"""
        renderer = BatchRenderer(PrimitiveType.TRIANGLES)

        vertices = np.array([], dtype=np.float32).reshape(0, 6)
        transform = np.eye(4, dtype=np.float32)

        result = renderer._apply_transform(vertices, transform)

        assert result.shape == (0, 6)

    def test_combine_indices_single_batch(self):
        """インデックス結合（単一バッチ）"""
        renderer = BatchRenderer(PrimitiveType.TRIANGLES)

        vertices = np.array([
            [0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
            [1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
            [0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
        ], dtype=np.float32)

        indices = np.array([0, 1, 2], dtype=np.uint32)
        transform = np.eye(4, dtype=np.float32)

        renderer.add_geometry(vertices, indices, transform)
        renderer._batches[0].vertex_offset = 0

        combined = renderer._combine_indices()

        assert combined is not None
        np.testing.assert_array_equal(combined, [0, 1, 2])

    def test_combine_indices_multiple_batches(self):
        """インデックス結合（複数バッチ）"""
        renderer = BatchRenderer(PrimitiveType.TRIANGLES)

        # バッチ1: 頂点0-2
        vertices1 = np.array([
            [0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
            [1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
            [0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
        ], dtype=np.float32)
        indices1 = np.array([0, 1, 2], dtype=np.uint32)
        transform = np.eye(4, dtype=np.float32)

        renderer.add_geometry(vertices1, indices1, transform)
        renderer._batches[0].vertex_offset = 0

        # バッチ2: 頂点3-5（オフセット3）
        vertices2 = np.array([
            [2.0, 0.0, 0.0, 1.0, 0.0, 0.0],
            [3.0, 0.0, 0.0, 0.0, 1.0, 0.0],
            [2.0, 1.0, 0.0, 0.0, 0.0, 1.0],
        ], dtype=np.float32)
        indices2 = np.array([0, 1, 2], dtype=np.uint32)

        renderer.add_geometry(vertices2, indices2, transform)
        renderer._batches[1].vertex_offset = 3

        combined = renderer._combine_indices()

        assert combined is not None
        # バッチ2のインデックスはオフセット3が加算される
        expected = np.array([0, 1, 2, 3, 4, 5], dtype=np.uint32)
        np.testing.assert_array_equal(combined, expected)

    def test_combine_indices_no_indices(self):
        """インデックス結合（インデックス使用なし）"""
        renderer = BatchRenderer(PrimitiveType.POINTS)

        vertices = np.array([[0, 0, 0, 1, 0, 0]], dtype=np.float32)
        transform = np.eye(4, dtype=np.float32)

        renderer.add_geometry(vertices, None, transform)

        combined = renderer._combine_indices()

        assert combined is None

    def test_build_without_batches(self):
        """ビルド（バッチなし）"""
        renderer = BatchRenderer(PrimitiveType.TRIANGLES)

        # バッチがない状態でビルド
        renderer.build()

        # 何も起こらない
        assert renderer._total_vertices == 0
        assert renderer._total_indices == 0

    def test_build_not_dirty(self):
        """ビルド（dirtyフラグがfalse）"""
        renderer = BatchRenderer(PrimitiveType.TRIANGLES)

        vertices = np.array([[0, 0, 0, 1, 0, 0]], dtype=np.float32)
        transform = np.eye(4, dtype=np.float32)

        renderer.add_geometry(vertices, None, transform)
        renderer._is_dirty = False  # 強制的にfalseに

        # ビルドが実行されない
        renderer.build()

        assert renderer._total_vertices == 0  # ビルドされていない

    def test_properties(self):
        """プロパティのテスト"""
        renderer = BatchRenderer(PrimitiveType.TRIANGLES)

        assert renderer.batch_count == 0
        assert renderer.total_vertices == 0
        assert renderer.total_indices == 0

        vertices = np.array([
            [0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
            [1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
        ], dtype=np.float32)
        transform = np.eye(4, dtype=np.float32)

        renderer.add_geometry(vertices, None, transform)

        assert renderer.batch_count == 1

    def test_cleanup(self):
        """クリーンアップのテスト"""
        with patch('src.graphics.batch_renderer.gl') as mock_gl:
            renderer = BatchRenderer(PrimitiveType.TRIANGLES)

            # 仮のバッファIDを設定
            renderer._vao = 1
            renderer._vbo = 2
            renderer._ebo = 3

            renderer.cleanup()

            # 各バッファが削除される
            assert mock_gl.glDeleteBuffers.call_count == 2  # VBO, EBO
            assert mock_gl.glDeleteVertexArrays.call_count == 1  # VAO

            # IDがリセットされる
            assert renderer._vao == 0
            assert renderer._vbo == 0
            assert renderer._ebo == 0


class TestBatchRendererIntegration:
    """BatchRendererの統合テスト"""

    def test_full_workflow(self):
        """完全なワークフロー（add → build → properties）"""
        renderer = BatchRenderer(PrimitiveType.TRIANGLES)

        # 複数のジオメトリを追加
        for i in range(3):
            vertices = np.array([
                [float(i), 0.0, 0.0, 1.0, 0.0, 0.0],
                [float(i+1), 0.0, 0.0, 0.0, 1.0, 0.0],
                [float(i), 1.0, 0.0, 0.0, 0.0, 1.0],
            ], dtype=np.float32)

            indices = np.array([0, 1, 2], dtype=np.uint32)

            # 各バッチに異なる平行移動を適用
            transform = np.eye(4, dtype=np.float32)
            transform[0, 3] = float(i * 2)  # X方向にオフセット

            renderer.add_geometry(vertices, indices, transform)

        assert renderer.batch_count == 3
        assert renderer._is_dirty is True

        # ビルド（モックなしでは実際のOpenGL呼び出しが必要）
        # ここではビルド前の状態を確認
        assert len(renderer._batches) == 3
