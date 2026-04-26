"""
InstanceRendererクラスのユニットテスト
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock, call


class TestInstanceRendererInit:
    """InstanceRenderer初期化のテスト（OpenGLなし）"""

    def test_initialization(self):
        """初期化時の状態確認"""
        from src.graphics.instance_renderer import InstanceRenderer
        renderer = InstanceRenderer()

        assert renderer._vao == 0
        assert renderer._vbo == 0
        assert renderer._ebo == 0
        assert renderer._instance_vbo == 0
        assert renderer._vertex_count == 0
        assert renderer._index_count == 0
        assert renderer._instance_count == 0
        assert renderer._use_indices is False

    def test_properties_initial(self):
        """初期プロパティ値の確認"""
        from src.graphics.instance_renderer import InstanceRenderer
        renderer = InstanceRenderer()

        assert renderer.instance_count == 0
        assert renderer.vertex_count == 0
        assert renderer.index_count == 0


class TestInstanceRendererPackData:
    """_pack_instance_data のテスト（OpenGLなし）"""

    def test_pack_basic(self):
        """基本的なパッキング"""
        from src.graphics.instance_renderer import InstanceRenderer
        renderer = InstanceRenderer()

        offsets = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], dtype=np.float32)
        colors = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=np.float32)
        scales = np.array([0.5, 0.8], dtype=np.float32)

        data = renderer._pack_instance_data(offsets, colors, scales)

        assert data.shape == (2, 7)
        assert data.dtype == np.float32

        # 1番目のインスタンス
        np.testing.assert_array_almost_equal(data[0, :3], [1.0, 2.0, 3.0])  # offset
        np.testing.assert_array_almost_equal(data[0, 3:6], [1.0, 0.0, 0.0])  # color
        assert data[0, 6] == pytest.approx(0.5)  # scale

        # 2番目のインスタンス
        np.testing.assert_array_almost_equal(data[1, :3], [4.0, 5.0, 6.0])  # offset
        np.testing.assert_array_almost_equal(data[1, 3:6], [0.0, 1.0, 0.0])  # color
        assert data[1, 6] == pytest.approx(0.8)  # scale

    def test_pack_single_instance(self):
        """1インスタンスのパッキング"""
        from src.graphics.instance_renderer import InstanceRenderer
        renderer = InstanceRenderer()

        offsets = np.array([[0.0, 0.0, 0.0]], dtype=np.float32)
        colors = np.array([[1.0, 1.0, 1.0]], dtype=np.float32)
        scales = np.array([1.0], dtype=np.float32)

        data = renderer._pack_instance_data(offsets, colors, scales)

        assert data.shape == (1, 7)

    def test_pack_scales_2d_input(self):
        """2D配列のスケール入力でも動作する"""
        from src.graphics.instance_renderer import InstanceRenderer
        renderer = InstanceRenderer()

        offsets = np.array([[0.0, 0.0, 0.0]], dtype=np.float32)
        colors = np.array([[1.0, 0.0, 0.0]], dtype=np.float32)
        scales_2d = np.array([[1.0]], dtype=np.float32)  # (N, 1)

        data = renderer._pack_instance_data(offsets, colors, scales_2d)

        assert data.shape == (1, 7)
        assert data[0, 6] == pytest.approx(1.0)

    def test_pack_large_instances(self):
        """大量インスタンスのパッキング"""
        from src.graphics.instance_renderer import InstanceRenderer
        renderer = InstanceRenderer()

        n = 1000
        offsets = np.random.rand(n, 3).astype(np.float32)
        colors = np.random.rand(n, 3).astype(np.float32)
        scales = np.random.rand(n).astype(np.float32)

        data = renderer._pack_instance_data(offsets, colors, scales)

        assert data.shape == (n, 7)
        assert data.dtype == np.float32


class TestInstanceRendererConstants:
    """定数の確認"""

    def test_stride_and_offsets(self):
        """インスタンスVBOのストライドとオフセット定数の確認"""
        from src.graphics.instance_renderer import InstanceRenderer

        assert InstanceRenderer._INSTANCE_STRIDE_FLOATS == 7
        assert InstanceRenderer._INSTANCE_OFFSET_OFFSET == 0
        assert InstanceRenderer._INSTANCE_COLOR_OFFSET == 3
        assert InstanceRenderer._INSTANCE_SCALE_OFFSET == 6


class TestInstanceRendererWithMockedGL:
    """OpenGLをモックしたInstanceRendererのテスト"""

    @pytest.fixture
    def mock_gl(self):
        """OpenGL関数のモック"""
        with patch('src.graphics.instance_renderer.gl') as mock:
            mock.glGenVertexArrays.return_value = 1
            mock.glGenBuffers.side_effect = [2, 0, 3]  # vbo=2, instance_vbo=3
            yield mock

    def test_set_geometry_without_indices(self, mock_gl):
        """インデックスなしのジオメトリ設定"""
        from src.graphics.instance_renderer import InstanceRenderer
        renderer = InstanceRenderer()

        vertices = np.array([
            [0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
            [1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
            [0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
        ], dtype=np.float32)

        renderer.set_geometry(vertices, None)

        assert renderer.vertex_count == 3
        assert renderer._use_indices is False
        assert renderer.index_count == 0

    def test_set_geometry_with_indices(self, mock_gl):
        """インデックスありのジオメトリ設定"""
        from src.graphics.instance_renderer import InstanceRenderer
        mock_gl.glGenBuffers.side_effect = [2, 3]  # vbo=2, ebo=3

        renderer = InstanceRenderer()

        vertices = np.array([
            [0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
            [1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
            [0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
        ], dtype=np.float32)
        indices = np.array([0, 1, 2], dtype=np.uint32)

        renderer.set_geometry(vertices, indices)

        assert renderer.vertex_count == 3
        assert renderer._use_indices is True
        assert renderer.index_count == 3

    def test_set_geometry_empty_vertices(self, mock_gl):
        """空の頂点データは無視される"""
        from src.graphics.instance_renderer import InstanceRenderer
        renderer = InstanceRenderer()

        empty = np.array([], dtype=np.float32)
        renderer.set_geometry(empty, None)

        assert renderer.vertex_count == 0
        # glGenVertexArrays は呼ばれない（早期リターン）
        mock_gl.glGenVertexArrays.assert_not_called()

    def test_set_instances(self):
        """インスタンスデータの設定"""
        from src.graphics.instance_renderer import InstanceRenderer

        with patch('src.graphics.instance_renderer.gl') as mock_gl:
            mock_gl.glGenVertexArrays.return_value = 1
            mock_gl.glGenBuffers.side_effect = [2, 3, 4]  # vbo, ebo(skip), instance_vbo

            renderer = InstanceRenderer()

            # まずジオメトリを設定（VAO が必要）
            vertices = np.array([
                [0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
            ], dtype=np.float32)
            renderer.set_geometry(vertices, None)
            renderer._vao = 1  # VAO が設定されていることを確認

            # インスタンスデータ設定
            mock_gl.glGenBuffers.side_effect = [10]  # instance_vbo
            offsets = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]], dtype=np.float32)
            colors = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=np.float32)
            scales = np.array([1.0, 0.5], dtype=np.float32)
            renderer.set_instances(offsets, colors, scales)

            assert renderer.instance_count == 2

    def test_draw_calls_instanced(self):
        """draw() が glDrawElementsInstanced を呼ぶ"""
        from src.graphics.instance_renderer import InstanceRenderer

        with patch('src.graphics.instance_renderer.gl') as mock_gl:
            renderer = InstanceRenderer()
            renderer._vao = 1
            renderer._use_indices = True
            renderer._index_count = 36
            renderer._instance_count = 100

            renderer.draw()

            mock_gl.glBindVertexArray.assert_any_call(1)
            mock_gl.glDrawElementsInstanced.assert_called_once_with(
                mock_gl.GL_TRIANGLES,
                36,
                mock_gl.GL_UNSIGNED_INT,
                None,
                100
            )

    def test_draw_calls_arrays_instanced(self):
        """インデックスなし: draw() が glDrawArraysInstanced を呼ぶ"""
        from src.graphics.instance_renderer import InstanceRenderer

        with patch('src.graphics.instance_renderer.gl') as mock_gl:
            renderer = InstanceRenderer()
            renderer._vao = 1
            renderer._use_indices = False
            renderer._vertex_count = 3
            renderer._instance_count = 50

            renderer.draw()

            mock_gl.glDrawArraysInstanced.assert_called_once_with(
                mock_gl.GL_TRIANGLES,
                0,
                3,
                50
            )

    def test_draw_skips_when_no_vao(self):
        """VAO が 0 の場合は描画しない"""
        from src.graphics.instance_renderer import InstanceRenderer

        with patch('src.graphics.instance_renderer.gl') as mock_gl:
            renderer = InstanceRenderer()
            renderer._vao = 0
            renderer._instance_count = 100

            renderer.draw()

            mock_gl.glBindVertexArray.assert_not_called()

    def test_draw_skips_when_no_instances(self):
        """インスタンス数が 0 の場合は描画しない"""
        from src.graphics.instance_renderer import InstanceRenderer

        with patch('src.graphics.instance_renderer.gl') as mock_gl:
            renderer = InstanceRenderer()
            renderer._vao = 1
            renderer._instance_count = 0

            renderer.draw()

            mock_gl.glBindVertexArray.assert_not_called()

    def test_cleanup(self):
        """cleanup() でOpenGLリソースを解放する"""
        from src.graphics.instance_renderer import InstanceRenderer

        with patch('src.graphics.instance_renderer.gl') as mock_gl:
            renderer = InstanceRenderer()
            renderer._vao = 1
            renderer._vbo = 2
            renderer._ebo = 3
            renderer._instance_vbo = 4

            renderer.cleanup()

            # 各バッファが解放される
            mock_gl.glDeleteBuffers.assert_any_call(1, [4])  # instance_vbo
            mock_gl.glDeleteBuffers.assert_any_call(1, [3])  # ebo
            mock_gl.glDeleteBuffers.assert_any_call(1, [2])  # vbo
            mock_gl.glDeleteVertexArrays.assert_called_once_with(1, [1])

            assert renderer._vao == 0
            assert renderer._vbo == 0
            assert renderer._ebo == 0
            assert renderer._instance_vbo == 0

    def test_cleanup_skips_zero_handles(self):
        """ハンドルが 0 のリソースは解放しない"""
        from src.graphics.instance_renderer import InstanceRenderer

        with patch('src.graphics.instance_renderer.gl') as mock_gl:
            renderer = InstanceRenderer()
            # すべて 0 のまま

            renderer.cleanup()

            mock_gl.glDeleteBuffers.assert_not_called()
            mock_gl.glDeleteVertexArrays.assert_not_called()

    def test_update_instances_same_count(self):
        """同数インスタンスの更新は glBufferSubData を使う"""
        from src.graphics.instance_renderer import InstanceRenderer

        with patch('src.graphics.instance_renderer.gl') as mock_gl:
            renderer = InstanceRenderer()
            renderer._instance_vbo = 10
            renderer._instance_count = 2

            offsets = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]], dtype=np.float32)
            colors = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=np.float32)
            scales = np.array([1.0, 0.5], dtype=np.float32)

            renderer.update_instances(offsets, colors, scales)

            mock_gl.glBindBuffer.assert_any_call(mock_gl.GL_ARRAY_BUFFER, 10)
            mock_gl.glBufferSubData.assert_called_once()

    def test_update_instances_different_count(self):
        """インスタンス数変更は glBufferData を使う"""
        from src.graphics.instance_renderer import InstanceRenderer

        with patch('src.graphics.instance_renderer.gl') as mock_gl:
            renderer = InstanceRenderer()
            renderer._instance_vbo = 10
            renderer._instance_count = 2  # 今は2個

            # 3個に変更
            offsets = np.zeros((3, 3), dtype=np.float32)
            colors = np.zeros((3, 3), dtype=np.float32)
            scales = np.ones(3, dtype=np.float32)

            renderer.update_instances(offsets, colors, scales)

            mock_gl.glBufferData.assert_called_once()
            assert renderer.instance_count == 3
