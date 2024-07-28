import glob
import os
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, Future, Executor
from typing import Callable
import time

from tqdm import tqdm

from .runner_defines import RunnerSettings, TestCase, TestCaseResult, ResultStatus, NoTestcaseFileException
from .testcase_logger import RunnerLogManager, RunnerLog
from .runner_logger import RunnerLogger

class TestCaseRunner:
    logger = RunnerLogger("TestCaseRunner")
    def __init__(self,
                 handler: Callable[[TestCase], TestCaseResult],
                 setting: RunnerSettings,
                 ) -> None:
        self.settings = setting
        if self.settings.debug:
            self.logger.enable_debug_mode()
        self.input_file_path = self.settings.input_file_copy_path
        self.handler = handler
    
    @logger.function_tracer
    def make_testcases(self, files: list[str]) -> list[TestCase]:
        test_cases = []
        testcase_index = 0
        for input_file in sorted(files):
            for rep in range(self.settings.repeat_count):
                if self.settings.repeat_count != 1:
                    name, extension = os.path.splitext(os.path.basename(input_file))
                    basename = f"{name}_{rep+1}{extension}"
                else:
                    basename = os.path.basename(input_file)
                stdout_file = os.path.join(self.settings.stdout_log_path, basename)
                stderr_file = os.path.join(self.settings.stderr_log_path, basename)
                testcase_name = os.path.basename(input_file)
                testcase = TestCase(testcase_name, input_file, stdout_file, stderr_file, testcase_index)
                test_cases.append(testcase)
                testcase_index += 1
        return test_cases

    @logger.function_tracer
    def run(self) -> list[tuple[TestCase, TestCaseResult]]:
        futures:list[Future] = []
        test_cases: list[TestCase] = []
        files = glob.glob(os.path.join(self.input_file_path, "*"))
        if len(files) == 0:
            raise NoTestcaseFileException(f"{self.input_file_path}ディレクトリにファイルが1つもありません。")
        test_cases = self.make_testcases(files)
        executor_class: type[Executor] | None = None
        if self.settings.parallel_processing_method.lower() == "process":
            parallel = True
            executor_class = ProcessPoolExecutor
        elif self.settings.parallel_processing_method.lower() == "thread":
            parallel = True
            executor_class = ThreadPoolExecutor
        elif self.settings.parallel_processing_method.lower() == "single":
            parallel = False
        else:
            raise ValueError("引数parallel_processing_methodの値が不正です。")

        self.logger.debug("start testcase run process.")
        results: list[tuple[TestCase, TestCaseResult]] = []
        if parallel:
            self.logger.debug("paralle")
            assert executor_class is not None, "変数executor_classがNoneだよ"
            with tqdm(total=len(test_cases)) as progress:
                with executor_class() as executor:
                    for testcase in test_cases:
                        future = executor.submit(self.run_testcase, testcase)
                        future.add_done_callback(lambda p: progress.update())
                        futures.append(future)
                
                    for future in futures:
                        results.append(future.result())
        else:
            self.logger.debug("single")
            for testcase in tqdm(test_cases):
                result = self.run_testcase(testcase)
                results.append(result)
        
        return results
    
    def run_testcase(self, testcase: TestCase) -> tuple[TestCase, TestCaseResult]:
        start_time = time.time()
        try:
            test_result: TestCaseResult = self.handler(testcase)
        except Exception as e:
            self.logger.warning(f"テストケース{os.path.basename(testcase.input_file_path)}において、\
                引数で渡された関数の中で例外が発生しました。\n{str(e)}")
            test_result = TestCaseResult(error_status=ResultStatus.IE, stderr=str(e))
        erapsed_time = time.time() - start_time
        if self.settings.measure_time:
            test_result.attribute["time"] = erapsed_time
        if self.settings.stdout_file_output:
            with open(testcase.stdout_file_path, mode='w') as f:
                f.write(test_result.stdout)
        if self.settings.stderr_file_output:
            with open(testcase.stderr_file_path, mode='w') as f:
                f.write(test_result.stderr)
        return testcase, test_result

def run(
        handler: Callable[[TestCase], TestCaseResult],
        input_file_path: str,
        repeat_count: int = 1,
        measure_time: bool = True,
        copy_target_files: list[str] = [],
        parallel_processing_method: str = "process",
        stdout_file_output: bool = True,
        stderr_file_output: bool = True,
        log_folder_name: str | None = None,
        _debug: bool = False,
        ) -> None:
    """ランナーを実行する

    Args:
        handler (Callable[[TestCase], TestCaseResult]): 並列実行する関数
        input_file_path (str): 入力ファイル群が置いてあるディレクトリへのパス
        repeat_count (int, optional): それぞれのテストケースを何回実行するか. Defaults to 1.
        measure_time (bool, optional): 処理時間を計測して記録するかどうか. Defaults to True.
        copy_target_files (list[str], optional): コピーしたいファイルパスのリスト. Defaults to [].
        parallel_processing_method (str, optional): 並列化の方法(プロセスかスレッドか). Defaults to 'process'.
        stdout_file_output (bool, optional): 標準出力をファイルで保存するかどうか. Defaults to True.
        stderr_file_output (bool, optional): 標準エラー出力をファイルで保存するかどうか. Defaults to True.
        log_folder_name (str | None, optional): ログフォルダの名前(Noneだと現在時刻'YYYYMMDDHHMMSS'形式になる). Defaults to None.
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
        _debug,
    )
    runner = TestCaseRunner(handler, setting)
    result = runner.run()
    log_manager = RunnerLogManager(result, setting)
    log_manager.make_html()

# 公開するメンバーを制御する
__all__ = [
    "run",
]
