from typing import List, Union, Callable

from .runner import TestCase, TestCaseResult, RunnerSettings, TestCaseRunner
from .testcase_logger import LogManager

def run(
        handler: Callable[[TestCase], TestCaseResult],
        input_file_path: str,
        repeat_count: int = 1,
        measure_time: bool = True,
        copy_target_files: List[str] = [],
        parallel_processing_method: str = "process",
        stdout_file_output: bool = True,
        stderr_file_output: bool = True,
        log_folder_name: Union[str, None] = None,
        ) -> None:
    """ランナーを実行する

    Args:
        handler (Callable[[TestCase], TestCaseResult]): 並列実行する関数
        input_file_path (str): 入力ファイル群が置いてあるディレクトリへのパス
        repeat_count (int, optional): それぞれのテストケースを何回実行するか. Defaults to 1.
        measure_time (bool, optional): 処理時間を計測して記録するかどうか. Defaults to True.
        copy_target_files (List[str], optional): コピーしたいファイルパスのリスト. Defaults to [].
        parallel_processing_method (str, optional): 並列化の方法(プロセスかスレッドか). Defaults to 'process'.
        stdout_file_output (bool, optional): 標準出力をファイルで保存するかどうか. Defaults to True.
        stderr_file_output (bool, optional): 標準エラー出力をファイルで保存するかどうか. Defaults to True.
        log_folder_name (Union[str, None], optional): ログフォルダの名前(Noneだと現在時刻'YYYYMMDDHHMMSS'形式になる). Defaults to None.
    """
    setting = RunnerSettings(
        input_file_path,
        repeat_count,
        measure_time,
        copy_target_files,
        parallel_processing_method,
        stdout_file_output,
        stderr_file_output,
        log_folder_name,
    )
    runner = TestCaseRunner(handler, setting)
    result = runner.run()
    log_manager = LogManager(setting)
    log_manager.make_result_log(result)
    log_manager.finalize()

# 公開するメンバーを制御する
__all__ = [
    "run",
]
