import os
from typing import Callable
import datetime

from .defines import TestCase, TestCaseResult
from .parallel_executor import start_executor
from .renderer import make_html

def get_log_file_path() -> str:
    log_name = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_LOG"
    return os.path.join("log", log_name)

def run(
        testcase_handler: Callable[[TestCase], TestCaseResult|None],
        input_file_path: str,
        repeat_count: int = 1,
        copy_target_files: list[str] = [],
        parallel_processing_method: str = "process",
        time_limit: int|float|None = None,
        _debug: bool = False,
        ) -> None:
    """ランナーを実行する

    Args:
        testcase_handler (Callable[[TestCase], TestCaseResult]): 並列実行する関数
        input_file_path (str): 入力ファイル群が置いてあるディレクトリへのパス
        repeat_count (int, optional): それぞれのテストケースを何回実行するか. Defaults to 1.
        copy_target_files (list[str], optional): コピーしたいファイルパスのリスト. Defaults to [].
        parallel_processing_method (str, optional): 並列化の方法(プロセスかスレッドか). Defaults to 'process'.
    """
    log_folder_name = get_log_file_path()
    log = start_executor(
        testcase_handler,
        input_file_path,
        log_folder_name,
        repeat_count,
        copy_target_files,
        parallel_processing_method,
        time_limit,
        _debug,
    )
    file = os.path.join(log_folder_name, "result.html")
    make_html(file, log, _debug)

# 公開するメンバーを制御する
__all__ = [
    "run",
]
