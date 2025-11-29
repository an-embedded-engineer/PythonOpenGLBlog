"""
ロギングモジュール
"""
import logging
import sys
from datetime import datetime
from pathlib import Path


# カスタムログレベルの定義
FORCE = 60   # CRITICAL(50)より上：常に出力
TIME = 25    # INFO(20)とWARNING(30)の間：処理時間計測用
TRACE = 5    # DEBUG(10)より下：関数トレース用

# ログレベル名の登録
logging.addLevelName(FORCE, "FORCE")
logging.addLevelName(TIME, "TIME")
logging.addLevelName(TRACE, "TRACE")


def _force(self, message, *args, **kwargs):
    """FORCEレベルのログを出力"""
    if self.isEnabledFor(FORCE):
        self._log(FORCE, message, args, **kwargs)


def _time(self, message, *args, **kwargs):
    """TIMEレベルのログを出力"""
    if self.isEnabledFor(TIME):
        self._log(TIME, message, args, **kwargs)


def _trace(self, message, *args, **kwargs):
    """TRACEレベルのログを出力"""
    if self.isEnabledFor(TRACE):
        self._log(TRACE, message, args, **kwargs)


# Loggerクラスにメソッドを追加
setattr(logging.Logger, 'force', _force)
setattr(logging.Logger, 'time', _time)
setattr(logging.Logger, 'trace', _trace)


# ANSIカラーコード
class LogColors:
    """ログレベルごとの色定義"""
    RESET = "\033[0m"
    TRACE = "\033[90m"    # グレー
    DEBUG = "\033[36m"    # シアン
    INFO = "\033[32m"     # 緑
    TIME = "\033[34m"     # 青
    WARNING = "\033[33m"  # 黄色
    ERROR = "\033[31m"    # 赤
    CRITICAL = "\033[35m" # マゼンタ
    FORCE = "\033[1;35m"  # 太字マゼンタ


class ColoredFormatter(logging.Formatter):
    """色付きログフォーマッター（行全体を色分け）"""

    COLORS = {
        TRACE: LogColors.TRACE,
        logging.DEBUG: LogColors.DEBUG,
        logging.INFO: LogColors.INFO,
        TIME: LogColors.TIME,
        logging.WARNING: LogColors.WARNING,
        logging.ERROR: LogColors.ERROR,
        logging.CRITICAL: LogColors.CRITICAL,
        FORCE: LogColors.FORCE,
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelno, LogColors.RESET)
        message = super().format(record)
        return f"{color}{message}{LogColors.RESET}"


class LevelFilter(logging.Filter):
    """特定のログレベルのみを許可するフィルター"""

    def __init__(self, allowed_levels: list[int]) -> None:
        """
        Args:
            allowed_levels: 許可するログレベルのリスト
        """
        super().__init__()
        self._allowed_levels = set(allowed_levels)

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno in self._allowed_levels


def setup_logger(
    name: str = "PythonOpenGL",
    level: int = logging.DEBUG,
    log_to_file: bool = False,
    log_dir: str = "logs",
    log_file_timestamp: bool = False,
    allowed_levels: list[int] | None = None
) -> logging.Logger:
    """
    ロガーをセットアップする

    Args:
        name: ロガー名
        level: ログレベル（logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR）
              allowed_levelsが指定されていない場合、このレベル以上を出力
        log_to_file: ファイルにログを出力するか
        log_dir: ログファイルの出力ディレクトリ
        log_file_timestamp: ログファイル名にタイムスタンプを付けるか
        allowed_levels: 許可するログレベルのリスト（指定時はlevelより優先）
                       例: [FORCE, logging.INFO, TIME] でこれらのみ出力
    """
    logger = logging.getLogger(name)

    # 既にハンドラーが設定されている場合はクリアして再設定
    if logger.handlers:
        logger.handlers.clear()

    # allowed_levelsが指定されている場合は最小レベルを設定
    if allowed_levels:
        logger.setLevel(min(allowed_levels))
    else:
        logger.setLevel(level)

    # フォーマッターの設定
    console_formatter = ColoredFormatter(
        "[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_formatter = logging.Formatter(
        "[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # コンソールハンドラーの設定
    console_handler = logging.StreamHandler(sys.stdout)
    if allowed_levels:
        console_handler.setLevel(min(allowed_levels))
        console_handler.addFilter(LevelFilter(allowed_levels))
    else:
        console_handler.setLevel(level)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # ファイルハンドラーの設定
    if log_to_file:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        if log_file_timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = log_path / f"{name}_{timestamp}.log"
        else:
            log_file = log_path / f"{name}.log"

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        if allowed_levels:
            file_handler.setLevel(min(allowed_levels))
            file_handler.addFilter(LevelFilter(allowed_levels))
        else:
            file_handler.setLevel(level)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        logger.info(f"Log file: {log_file}")

    return logger


# デフォルトのロガー（後でsetup_logger()で再設定可能）
logger = setup_logger()
