"""
パフォーマンス管理モジュール

FPS計測と処理時間測定を行う
"""
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from src.utils.logger import logger


@dataclass
class PerformanceStats:
    """パフォーマンス統計情報"""
    fps: float = 0.0
    frame_time_ms: float = 0.0
    target_fps: float = 60.0
    timing_stats: Dict[str, float] = field(default_factory=dict)
    hierarchical_stats: Dict[str, Dict] = field(default_factory=dict)


class PerformanceManager:
    """
    パフォーマンス管理クラス
    
    FPS計測と処理時間測定を提供する
    """

    def __init__(self, target_fps: float = 60.0) -> None:
        """
        初期化
        
        Args:
            target_fps: 目標FPS（表示用）
        """
        self.target_fps = target_fps
        
        # FPS計測
        self._last_frame_time = time.time()
        self._frame_count = 0
        self._fps_accumulator = 0.0
        self._current_fps = 0.0
        
        # FPS統計（平均/最大/最小）
        self._fps_history: List[float] = []
        self._fps_history_max_size = 60  # 1秒分の履歴
        
        # 処理時間計測
        self._timing_stats: Dict[str, float] = {}
        self._hierarchical_stats: Dict[str, Dict] = {}
        self._operation_stack: List[str] = []
        self._execution_order: List[str] = []
        
        # 前フレーム情報（imgui表示用）
        self._previous_frame_stats = PerformanceStats()
        
        # ドローコール数（外部から設定）
        self._draw_call_count = 0

    def begin_frame(self) -> None:
        """フレーム開始時の処理"""
        current_time = time.time()
        frame_time = current_time - self._last_frame_time
        
        # FPS計算
        self._frame_count += 1
        self._fps_accumulator += frame_time
        
        # 10フレームごとにFPS更新
        if self._frame_count >= 10:
            if self._fps_accumulator > 0.0:
                self._current_fps = self._frame_count / self._fps_accumulator
                
                # FPS履歴に追加
                self._fps_history.append(self._current_fps)
                if len(self._fps_history) > self._fps_history_max_size:
                    self._fps_history.pop(0)
            else:
                self._current_fps = self.target_fps
            
            self._frame_count = 0
            self._fps_accumulator = 0.0
        
        self._last_frame_time = current_time
        
        # 統計をクリア
        self._hierarchical_stats.clear()
        self._execution_order.clear()
        self._operation_stack.clear()

    def end_frame(self) -> None:
        """フレーム終了時の処理"""
        # 前フレーム情報を保存（imgui表示用）
        self._previous_frame_stats = PerformanceStats(
            fps=self._current_fps,
            frame_time_ms=self.get_frame_time() * 1000,
            target_fps=self.target_fps,
            timing_stats=self._timing_stats.copy(),
            hierarchical_stats=self._copy_hierarchical_stats()
        )

    def time_operation(self, operation_name: str):
        """
        操作の実行時間を測定するコンテキストマネージャ
        
        Args:
            operation_name: 操作名
            
        Returns:
            OperationTimer
            
        Example:
            with performance_manager.time_operation("Draw Cubes"):
                draw_cubes()
        """
        return OperationTimer(self, operation_name)

    def _begin_operation(self, operation_name: str) -> None:
        """階層化された操作開始（内部用）"""
        self._operation_stack.append(operation_name)

    def _end_operation(self, operation_name: str, elapsed_time: float) -> None:
        """階層化された操作終了（内部用）"""
        # 階層化された統計を更新
        self._update_hierarchical_stats(operation_name, elapsed_time)
        
        # スタックから操作を取り除く
        if self._operation_stack and self._operation_stack[-1] == operation_name:
            self._operation_stack.pop()
        
        # フラットな統計も保持
        self._timing_stats[operation_name] = elapsed_time

    def _update_hierarchical_stats(self, operation_name: str, elapsed_time: float) -> None:
        """階層化された統計を更新"""
        current_path = self._operation_stack.copy()
        
        # 実行順序を記録
        path_key = " -> ".join(current_path)
        if path_key not in self._execution_order:
            self._execution_order.append(path_key)
        
        # 階層データ構造を更新
        current_node = self._hierarchical_stats
        for i, path_part in enumerate(current_path):
            if path_part not in current_node:
                current_node[path_part] = {
                    'time': 0.0,
                    'children': {},
                    'call_count': 0,
                    'is_leaf': i == len(current_path) - 1,
                    'execution_order': len(self._execution_order) - 1
                }
            
            if i == len(current_path) - 1:
                # リーフノード：時間を更新
                current_node[path_part]['time'] = elapsed_time
                current_node[path_part]['call_count'] += 1
                current_node[path_part]['is_leaf'] = True
            else:
                # 中間ノード：子への移動のみ
                current_node[path_part]['is_leaf'] = False
                current_node = current_node[path_part]['children']

    def _copy_hierarchical_stats(self) -> Dict[str, Dict]:
        """階層化された統計の深いコピーを作成"""
        def copy_node(node):
            return {
                'time': node['time'],
                'children': {k: copy_node(v) for k, v in node['children'].items()},
                'call_count': node['call_count'],
                'is_leaf': node['is_leaf'],
                'execution_order': node.get('execution_order', 0)
            }
        
        return {k: copy_node(v) for k, v in self._hierarchical_stats.items()}

    def get_fps(self) -> float:
        """現在のFPSを取得"""
        return self._current_fps

    def get_frame_time(self) -> float:
        """現在のフレーム時間（秒）を取得"""
        return 1.0 / self._current_fps if self._current_fps > 0 else 0.0

    def get_fps_stats(self) -> Dict[str, float]:
        """
        FPS統計を取得（平均/最大/最小）
        
        Returns:
            {'average': float, 'max': float, 'min': float}
        """
        if not self._fps_history:
            return {'average': 0.0, 'max': 0.0, 'min': 0.0}
        
        return {
            'average': sum(self._fps_history) / len(self._fps_history),
            'max': max(self._fps_history),
            'min': min(self._fps_history)
        }

    def get_previous_frame_info(self) -> PerformanceStats:
        """前フレームの統計情報を取得（imgui表示用）"""
        return self._previous_frame_stats

    def set_draw_call_count(self, count: int) -> None:
        """ドローコール数を設定"""
        self._draw_call_count = count

    def get_draw_call_count(self) -> int:
        """ドローコール数を取得"""
        return self._draw_call_count

    def print_stats(self, hierarchical: bool = True, sort_by_time: bool = False) -> None:
        """
        パフォーマンス統計をログ出力
        
        Args:
            hierarchical: 階層表示（True）またはフラット表示（False）
            sort_by_time: 時間順でソート（フラット表示のみ有効）
        """
        # 前フレームの統計を使用
        stats = self._previous_frame_stats
        
        logger.info("\n=== Performance Stats ===")
        logger.info(f"FPS: {stats.fps:.1f}")
        logger.info(f"Frame Time: {stats.frame_time_ms:.2f}ms")
        logger.info(f"Draw Calls: {self._draw_call_count}")
        
        # FPS統計
        fps_stats = self.get_fps_stats()
        logger.info(f"FPS Stats - Avg: {fps_stats['average']:.1f}, "
                   f"Max: {fps_stats['max']:.1f}, Min: {fps_stats['min']:.1f}")
        
        if hierarchical and stats.hierarchical_stats:
            logger.info("\nHierarchical Operation Timings:")
            self._print_hierarchical_stats(stats.hierarchical_stats, 0)
        else:
            logger.info("\nFlat Operation Timings:")
            if sort_by_time:
                sorted_stats = sorted(stats.timing_stats.items(), 
                                    key=lambda x: x[1], reverse=True)
            else:
                sorted_stats = stats.timing_stats.items()
            
            for operation, time_s in sorted_stats:
                percentage = (time_s / stats.frame_time_ms * 1000 * 100) if stats.frame_time_ms > 0 else 0
                logger.info(f"  {operation}: {time_s*1000:.2f}ms ({percentage:.1f}%)")
        
        logger.info("=" * 25)

    def _print_hierarchical_stats(self, stats_node: Dict, depth: int) -> None:
        """階層化された統計をログ出力"""
        indent = "  " * (depth + 1)
        
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
                logger.info(f"{indent}{display_text}")
            else:
                # 中間ノード
                total_children_time = self._calculate_total_children_time(children)
                total_children_ms = total_children_time * 1000
                logger.info(f"{indent}{node_name}: {timing_ms:.2f}ms "
                          f"(children: {total_children_ms:.2f}ms)")
                # 再帰的に子ノードを出力
                self._print_hierarchical_stats(children, depth + 1)

    def _calculate_total_children_time(self, children: Dict) -> float:
        """子ノードの合計時間を計算"""
        total_time = 0.0
        for child_data in children.values():
            if len(child_data['children']) == 0:
                total_time += child_data['time']
            else:
                total_time += self._calculate_total_children_time(child_data['children'])
        return total_time

    def reset(self) -> None:
        """統計情報をリセット"""
        self._fps_history.clear()
        self._timing_stats.clear()
        self._hierarchical_stats.clear()
        self._execution_order.clear()
        self._operation_stack.clear()
        self._frame_count = 0
        self._fps_accumulator = 0.0
        self._current_fps = 0.0
        self._draw_call_count = 0
        self._last_frame_time = time.time()


class OperationTimer:
    """操作時間測定用コンテキストマネージャ"""

    def __init__(self, perf_manager: PerformanceManager, operation_name: str):
        """
        初期化
        
        Args:
            perf_manager: PerformanceManagerインスタンス
            operation_name: 操作名
        """
        self._perf_manager = perf_manager
        self._operation_name = operation_name
        self._start_time = 0.0

    def __enter__(self):
        """コンテキストマネージャの開始"""
        self._perf_manager._begin_operation(self._operation_name)
        self._start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャの終了"""
        elapsed = time.time() - self._start_time
        self._perf_manager._end_operation(self._operation_name, elapsed)
        return False


# グローバルインスタンス（loggerと同様）
performance_manager = PerformanceManager()
