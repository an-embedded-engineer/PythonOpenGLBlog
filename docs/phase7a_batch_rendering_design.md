# Phase 7a: バッチレンダリング設計書

**作成日**: 2026-01-03
**Phase**: 7a - 高速化（バッチ描画）
**ステータス**: 設計中

## 目次

1. [概要](#概要)
2. [現状分析](#現状分析)
3. [設計方針](#設計方針)
4. [アーキテクチャ設計](#アーキテクチャ設計)
5. [実装ステップ](#実装ステップ)
6. [パフォーマンス目標](#パフォーマンス目標)
7. [教育的ポイント](#教育的ポイント)

---

## 概要

### Phase 7aの目的
複数のオブジェクトを効率的に描画するため、**バッチレンダリング**を実装する。

### 達成目標
- ドローコール数の削減（N個のオブジェクト → 1回のドローコール）
- パフォーマンスの可視化（FPS、ドローコール数、フレームタイム）
- 個別描画とバッチ描画の比較機能

---

## 現状分析

### Phase 6bまでの実装

**描画フロー**:
```python
for object in objects:
    shader.set_mat4("model", object.transform)
    object.draw()  # ← ドローコール発生
```

**問題点**:
1. **ドローコール過多**: オブジェクト数分のドローコール
2. **CPU-GPUボトルネック**: 毎回の同期処理オーバーヘッド
3. **スケーラビリティ**: オブジェクト数が増えると急激に遅くなる

**具体例（Phase 6b Allモード）**:
```python
# app.py の _draw_geometries() メソッド
for obj in self._all_mode_objects:
    self._transform.set_model_identity()
    self._transform.translate_model(obj['pos'][0], obj['pos'][1], obj['pos'][2])
    self._transform.scale_model(obj['scale'], obj['scale'], obj['scale'])
    # ... 回転など
    self._shader.set_mat4("model", self._transform.model)

    # ここでドローコール（例: 10オブジェクト = 10回）
    if obj['type'] == 'cube':
        self._cube_geometry.draw()  # ← glDrawElements()
```

### 既存クラス構造

```
GeometryBase (抽象基底クラス)
├── _vao, _vbo, _ebo (OpenGLバッファ)
├── draw() メソッド
└── サブクラス:
    ├── PointGeometry
    ├── LineGeometry
    ├── TriangleGeometry
    ├── RectangleGeometry
    ├── CubeGeometry
    └── SphereGeometry
```

---

## 設計方針

### 基本コンセプト

**静的バッチング（Static Batching）**:
- 同じ形状の複数インスタンスの頂点データを結合
- CPU側でModel行列を適用して頂点座標を変換
- 結合した頂点データを1つのVBOに格納
- **1回のドローコール**で全オブジェクトを描画

### アプローチの選択理由

| 方式 | 特徴 | Phase 7a | Phase 7b |
|------|------|----------|----------|
| **個別描画** | オブジェクトごとにドローコール | ✅ 既存 | - |
| **静的バッチング** | CPU側でTransform適用、頂点結合 | ✅ Phase 7a | - |
| **インスタンシング** | GPU側でTransform、属性配列使用 | - | ✅ Phase 7b |

**Phase 7aで静的バッチングを選ぶ理由**:
1. 実装が直感的で理解しやすい
2. ドローコール削減の効果を体感できる
3. Phase 7bのインスタンシング導入の布石

### 互換性方針

- **Phase 6bの機能は完全に維持**
- **切り替え可能**: imgui UIで個別描画 ⇔ バッチ描画を切り替え
- **段階的拡張**: 既存コードを壊さず新機能を追加

---

## アーキテクチャ設計

### 新規クラス

#### 1. `RenderBatch` (データクラス)

バッチの1単位を表現。

```python
from dataclasses import dataclass
from typing import Optional
import numpy as np

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
```

#### 2. `BatchRenderer` クラス

複数のジオメトリをまとめて描画。

```python
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
        batch = RenderBatch(
            vertices=vertices,
            indices=indices,
            transform=transform
        )
        self._batches.append(batch)
        self._is_dirty = True

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
        for batch in self._batches:
            transformed_verts = self._apply_transform(batch.vertices, batch.transform)
            transformed_batches.append(transformed_verts)

        # 2. 頂点データを結合
        combined_vertices = np.concatenate(transformed_batches, axis=0)

        # 3. インデックスデータを結合（該当する場合）
        if self._use_indices:
            combined_indices = self._combine_indices()

        # 4. OpenGLバッファを作成
        self._create_buffers(combined_vertices, combined_indices if self._use_indices else None)

        self._is_dirty = False

    def flush(self) -> None:
        """バッチをGPUに転送して描画"""
        if self._is_dirty:
            self.build()

        if self._vao == 0:
            return

        # 1回のドローコール
        gl.glBindVertexArray(self._vao)
        if self._use_indices:
            gl.glDrawElements(self._primitive_type.value, self._total_index_count, gl.GL_UNSIGNED_INT, None)
        else:
            gl.glDrawArrays(self._primitive_type.value, 0, self._total_vertex_count)
        gl.glBindVertexArray(0)

    def clear(self) -> None:
        """バッチをクリア"""
        self._batches.clear()
        self._is_dirty = True

    def _apply_transform(self, vertices: np.ndarray, transform: np.ndarray) -> np.ndarray:
        """
        頂点にTransform行列を適用

        Args:
            vertices: 頂点データ（Nx6: x,y,z,r,g,b）
            transform: 4x4変換行列

        Returns:
            変換後の頂点データ
        """
        # 位置座標のみ取り出し（Nx3）
        positions = vertices[:, :3]
        colors = vertices[:, 3:6]

        # 同次座標に変換（Nx4: x,y,z,1）
        homogeneous = np.hstack([positions, np.ones((len(positions), 1))])

        # 行列変換（transform @ pos^T）^T
        transformed_pos = (transform @ homogeneous.T).T

        # w成分で除算（透視変換対応）
        transformed_pos = transformed_pos[:, :3] / transformed_pos[:, 3:4]

        # 位置+色を結合
        return np.hstack([transformed_pos, colors]).astype(np.float32)
```

### 既存クラスの拡張

#### `GeometryBase` に追加

```python
class GeometryBase(ABC):
    # 既存メソッドは維持...

    def get_vertex_data(self) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        頂点データとインデックスを取得（バッチレンダリング用）

        Returns:
            (vertices, indices): 頂点データ（Nx6）とインデックス（Optional）
        """
        # サブクラスで実装
        # 例: CubeGeometry の場合
        #   vertices: (24, 6) 配列
        #   indices: (36,) 配列
        raise NotImplementedError
```

#### `App` クラスの拡張

```python
class App:
    def __init__(self):
        # 既存の初期化...

        # === バッチレンダリング関連 ===
        self._use_batch_rendering = False  # バッチレンダリング有効/無効

        # プリミティブタイプごとのバッチレンダラー
        self._batch_renderers = {
            PrimitiveType.POINTS: BatchRenderer(PrimitiveType.POINTS),
            PrimitiveType.LINES: BatchRenderer(PrimitiveType.LINES),
            PrimitiveType.TRIANGLES: BatchRenderer(PrimitiveType.TRIANGLES),
        }

        # パフォーマンス計測
        self._draw_call_count = 0
        self._frame_time_ms = 0.0
        self._last_frame_time = 0.0

    def _draw_geometries(self):
        """ジオメトリを描画"""
        if self._use_batch_rendering:
            self._draw_with_batching()
        else:
            self._draw_individual()  # 既存の個別描画

    def _draw_with_batching(self):
        """バッチレンダリングで描画"""
        # 1. バッチをクリア
        for renderer in self._batch_renderers.values():
            renderer.clear()

        # 2. オブジェクトをバッチに追加
        self._draw_call_count = 0
        for obj in self._all_mode_objects:
            # Transform行列を計算
            self._transform.set_model_identity()
            self._transform.translate_model(obj['pos'][0], obj['pos'][1], obj['pos'][2])
            self._transform.scale_model(obj['scale'], obj['scale'], obj['scale'])
            # ... 回転など

            # ジオメトリの頂点データを取得
            geometry = self._get_geometry_by_type(obj['type'])
            vertices, indices = geometry.get_vertex_data()

            # バッチに追加
            renderer = self._batch_renderers[geometry.primitive_type]
            renderer.add_geometry(vertices, indices, self._transform.model)

        # 3. バッチをフラッシュ（描画）
        for renderer in self._batch_renderers.values():
            renderer.flush()
            self._draw_call_count += 1  # バッチごとに1回のドローコール
```

---

## 実装ステップ

### Step 0: パフォーマンス計測基盤の構築
- [ ] `PerformanceManager` クラス作成（`src/utils/performance.py`）
  - [ ] FPS計測機能（平均/最大/最小）
  - [ ] 処理時間計測（with構文対応）
  - [ ] 階層化された統計情報
  - [ ] グローバルインスタンス対応
- [ ] `utils/__init__.py` にエクスポート追加
- [ ] App クラスに統合
  - [ ] `begin_frame()` / `end_frame()` 呼び出し
  - [ ] 描画処理の計測箇所追加
- [ ] imgui パフォーマンス表示UI作成
  - [ ] FPS表示
  - [ ] ドローコール数表示
  - [ ] 処理時間の階層表示
- [ ] 動作確認・テスト

### Step 1: データクラス作成
- [ ] `RenderBatch` dataclass 作成
- [ ] 単体テスト作成

### Step 2: BatchRenderer 実装
- [ ] `BatchRenderer` クラス作成
- [ ] `add_geometry()` 実装
- [ ] `_apply_transform()` 実装（頂点変換）
- [ ] `_combine_vertices()` 実装（頂点結合）
- [ ] `_combine_indices()` 実装（インデックス結合）
- [ ] `build()` 実装（バッファ作成）
- [ ] `flush()` 実装（描画）
- [ ] 単体テスト作成

### Step 3: GeometryBase 拡張
- [ ] `get_vertex_data()` メソッド追加
- [ ] 各ジオメトリクラスに実装
  - [ ] `PointGeometry`
  - [ ] `LineGeometry`
  - [ ] `TriangleGeometry`
  - [ ] `RectangleGeometry`
  - [ ] `CubeGeometry`
  - [ ] `SphereGeometry`
- [ ] 単体テスト更新

### Step 4: App クラス統合
- [ ] `BatchRenderer` インスタンス作成
- [ ] `_use_batch_rendering` フラグ追加
- [ ] `_draw_with_batching()` 実装
- [ ] `_draw_individual()` に既存コードをリファクタ
- [ ] パフォーマンス計測機能追加
  - [ ] ドローコール数カウント
  - [ ] フレームタイム計測

### Step 5: imgui UI追加
- [ ] "Use Batch Rendering" チェックボックス
- [ ] パフォーマンス表示
  - [ ] FPS
  - [ ] ドローコール数
  - [ ] フレームタイム (ms)
- [ ] オブジェクト数調整スライダー

### Step 6: 動作確認
- [ ] 個別描画モードで動作確認
- [ ] バッチレンダリングモードで動作確認
- [ ] 切り替え動作確認
- [ ] パフォーマンス比較

### Step 7: ブログ記事作成
- [ ] 記事下書き作成
- [ ] スクリーンショット撮影
- [ ] コード例の整理

---

## パフォーマンス目標

### テストケース

| オブジェクト数 | 個別描画（ドローコール） | バッチ描画（ドローコール） | 期待される改善 |
|-------------|-------------------|---------------------|------------|
| 10個 | 10回 | 1回 | 10倍削減 |
| 100個 | 100回 | 1回 | 100倍削減 |
| 1000個 | 1000回 | 1回 | 1000倍削減 |

### 計測項目

1. **FPS (Frames Per Second)**
   - 個別描画: ベースライン
   - バッチ描画: 目標 +50%以上

2. **ドローコール数**
   - 個別描画: N回（オブジェクト数）
   - バッチ描画: プリミティブタイプ数（最大3回: POINTS, LINES, TRIANGLES）

3. **フレームタイム**
   - 個別描画: ベースライン
   - バッチ描画: 目標 -30%以上

---

## 教育的ポイント

### 学習目標

1. **ドローコールのコスト理解**
   - CPU-GPU間の同期オーバーヘッド
   - バッチサイズとパフォーマンスの関係

2. **バッチングの利点と欠点**
   - ✅ 利点: ドローコール削減
   - ❌ 欠点: CPU側の頂点変換コスト、メモリ使用量増加

3. **最適化の方法論**
   - 計測 → 分析 → 改善 → 再計測
   - ボトルネックの特定

4. **Phase 7bへの橋渡し**
   - 静的バッチング（CPU変換）の限界
   - インスタンシング（GPU変換）の必要性

### ブログ記事での強調点

- 実際のFPS比較グラフ
- ドローコール数の可視化
- コードの変更点（Before/After）
- パフォーマンス計測の重要性

---

## パフォーマンス計測基盤の設計

### PerformanceManager クラス

参考: `references/performance_manager.py`

**主要機能**:
1. **FPS計測**: 10フレームごとに平均FPSを算出
2. **処理時間計測**: with構文で任意の処理ブロックを計測
3. **階層化統計**: コールスタックで処理の親子関係を記録
4. **UI表示**: 前フレームの統計情報をimguiで表示
5. **ログ出力**: 任意のタイミングで詳細統計を出力

**使用方法**:

```python
# グローバルインスタンス（loggerと同様）
from src.utils import performance_manager

# フレーム開始
performance_manager.begin_frame()

# 処理時間計測
with performance_manager.time_operation("Draw Geometries"):
    with performance_manager.time_operation("Draw Cubes"):
        # 描画処理
        pass
    with performance_manager.time_operation("Draw Spheres"):
        # 描画処理
        pass

# フレーム終了（FPS制限含む）
performance_manager.end_frame()

# FPS取得
fps = performance_manager.get_fps()

# 前フレーム統計取得（imgui表示用）
stats = performance_manager.get_previous_frame_info()
```

**出力例**:

```
=== Performance Stats ===
FPS: 60.0
Frame Time: 16.67ms
Hierarchical Operation Timings:
  Draw Geometries: 12.34ms (children: 10.50ms)
    Draw Cubes: 5.20ms (x10)
    Draw Spheres: 5.30ms (x5)
  Update Camera: 1.23ms
```

---

## 技術メモ

### Transform適用の数学

頂点座標の変換:
```
v' = M × v

where:
  v = [x, y, z, 1]^T  (同次座標)
  M = Model行列（4×4）
  v' = 変換後の座標
```

### バッファサイズの計算

```python
# オブジェクト数: N
# 1オブジェクトの頂点数: V
# 総頂点数: N × V

total_vertices = N * V
buffer_size = total_vertices * 6 * sizeof(float32)  # 位置(3) + 色(3)
```

### Phase 7bとの比較

| 項目 | Phase 7a（静的バッチ） | Phase 7b（インスタンシング） |
|-----|---------------------|--------------------------|
| Transform処理 | CPU | GPU |
| 頂点データ | 結合（N倍） | 元のまま（1倍） |
| ドローコール | 1回 | 1回 |
| メモリ使用量 | 多い | 少ない |
| 適用範囲 | 同一形状の複数インスタンス | 同一形状の大量インスタンス |

---

## 参考資料

- OpenGL Batching Techniques
- OpenGL SuperBible (Batch Rendering章)
- LearnOpenGL.com - Instancing

---

## 変更履歴

- 2026-01-03: 初版作成（Phase 7a開発開始時）
