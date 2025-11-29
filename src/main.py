
"""
PythonOpenGL - Phase 4a: シェーダー基礎（頂点編）
"""
import logging

# imguiとGLFWのimport順による警告を防ぐため、ここでimportする
from imgui_bundle import imgui
import glfw

from src.core import App
from src.utils import setup_logger, FORCE, TIME, TRACE


# ログ設定（DEBUG, INFO, WARNING, ERROR から選択）
LOG_LEVEL = logging.INFO
LOG_TO_FILE = True  # ファイルにログを出力する場合はTrue

# 特定レベルのみ出力する場合は allowed_levels を使用
# 例: FORCE, INFO, TIME のみ出力
# ALLOWED_LEVELS = [FORCE, logging.INFO, TIME]


def main() -> None:
    """メイン関数"""
    # ロガーの設定
    # 通常モード: 指定レベル以上を出力
    setup_logger(level=LOG_LEVEL, log_to_file=LOG_TO_FILE, log_dir="logs")

    # ORモード: 特定レベルのみ出力する場合
    # setup_logger(allowed_levels=ALLOWED_LEVELS, log_to_file=LOG_TO_FILE, log_dir="logs")

    app = App()
    app.run()


if __name__ == '__main__':
    main()
