"""
PerformanceManagerクラスのテスト
"""
import time
import pytest

from src.utils.performance import PerformanceManager


def test_performance_manager_initialization():
    """初期化のテスト"""
    perf = PerformanceManager(target_fps=60.0)
    assert perf.target_fps == 60.0
    assert perf.get_fps() == 0.0
    assert perf.get_draw_call_count() == 0


def test_fps_calculation():
    """FPS計算のテスト"""
    perf = PerformanceManager(target_fps=60.0)
    
    # 複数フレームをシミュレート
    for _ in range(15):
        perf.begin_frame()
        time.sleep(0.016)  # 約60FPS
        perf.end_frame()
    
    fps = perf.get_fps()
    assert 50 < fps < 70  # 許容範囲


def test_operation_timing():
    """操作時間計測のテスト"""
    perf = PerformanceManager()
    perf.begin_frame()
    
    # 処理時間を計測
    with perf.time_operation("Test Operation"):
        time.sleep(0.01)  # 10ms
    
    stats = perf.get_previous_frame_info()
    perf.end_frame()
    
    # タイミング情報が記録されているか確認
    # （end_frame後に前フレーム情報が更新される）
    perf.begin_frame()
    perf.end_frame()
    stats = perf.get_previous_frame_info()
    assert "Test Operation" in stats.timing_stats
    assert stats.timing_stats["Test Operation"] > 0.009  # 約10ms


def test_hierarchical_timing():
    """階層化された時間計測のテスト"""
    perf = PerformanceManager()
    perf.begin_frame()
    
    # 階層化された操作
    with perf.time_operation("Parent"):
        time.sleep(0.005)
        with perf.time_operation("Child1"):
            time.sleep(0.003)
        with perf.time_operation("Child2"):
            time.sleep(0.003)
    
    perf.end_frame()
    
    # 前フレーム情報を取得
    stats = perf.get_previous_frame_info()
    
    # 階層構造が正しいか確認
    assert 'Parent' in stats.hierarchical_stats
    parent_node = stats.hierarchical_stats['Parent']
    assert 'children' in parent_node
    assert 'Child1' in parent_node['children']
    assert 'Child2' in parent_node['children']


def test_draw_call_count():
    """ドローコール数のテスト"""
    perf = PerformanceManager()
    
    perf.set_draw_call_count(10)
    assert perf.get_draw_call_count() == 10
    
    perf.set_draw_call_count(0)
    assert perf.get_draw_call_count() == 0


def test_fps_stats():
    """FPS統計のテスト"""
    perf = PerformanceManager()
    
    # 複数フレームをシミュレート
    for _ in range(20):
        perf.begin_frame()
        time.sleep(0.016)
        perf.end_frame()
    
    fps_stats = perf.get_fps_stats()
    assert 'average' in fps_stats
    assert 'max' in fps_stats
    assert 'min' in fps_stats
    assert fps_stats['average'] > 0


def test_reset():
    """リセット機能のテスト"""
    perf = PerformanceManager()
    
    # データを生成
    for _ in range(5):
        perf.begin_frame()
        with perf.time_operation("Test"):
            time.sleep(0.01)
        perf.end_frame()
    
    # リセット
    perf.reset()
    
    assert perf.get_fps() == 0.0
    assert perf.get_draw_call_count() == 0
    fps_stats = perf.get_fps_stats()
    assert fps_stats['average'] == 0.0


def test_print_stats(capsys):
    """統計出力のテスト"""
    perf = PerformanceManager()
    
    perf.begin_frame()
    with perf.time_operation("Test Operation"):
        time.sleep(0.01)
    perf.end_frame()
    
    # ログ出力（エラーが出ないことを確認）
    perf.print_stats(hierarchical=True)
    perf.print_stats(hierarchical=False, sort_by_time=True)
