import glob
import os
from typing import Callable
import time
from typing import Optional

from .runner_settings import RunnerSettings
from .runner_defines import TestCase, TestCaseResult, ResultStatus
from .logger import RunnerLogger

class TestCaseRunner:
    logger = RunnerLogger("TestCaseRunner")
    def __init__(self,
                 testcase_handler: Callable[[TestCase], TestCaseResult],
                 setting: RunnerSettings,
                 ) -> None:
        self.settings = setting
        if self.settings.debug:
            self.logger.enable_debug_mode()
        self.input_file_path = self.settings.input_file_copy_path
        self.testcase_handler = testcase_handler
    
    @logger.function_tracer
    def make_testcases(self) -> list[TestCase]:
        files = glob.glob(os.path.join(self.input_file_path, "*"))
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
    def start(self) -> list[tuple[TestCase, TestCaseResult]]:
        test_cases: list[TestCase] = self.make_testcases()

        self.logger.debug("start testcase run process.")
        with self.settings.Executor(len(test_cases)) as executor:
            executor.submit(self.run_testcase, test_cases)
            results: list[Optional[TestCaseResult]] = executor.wait_and_get_results()
        
        parsed_results: list[TestCaseResult] = []
        for result in results:
            if result is None:
                result = TestCaseResult(ResultStatus.CAN)
            parsed_results.append(result)
        
        assert len(test_cases) == len(results)
        return list(zip(test_cases, parsed_results))
    
    def run_testcase(self, testcase: TestCase) -> TestCaseResult:
        start_time = time.time()
        try:
            test_result: TestCaseResult = self.testcase_handler(testcase)
        except Exception as e:
            self.logger.warning(f"テストケース{os.path.basename(testcase.input_file_path)}において、\
                引数で渡された関数の中で例外が発生しました。\n{str(e)}")
            test_result = TestCaseResult(error_status=ResultStatus.IE, stderr=str(e))
        erapsed_time = time.time() - start_time
        test_result.attribute["time"] = erapsed_time
        if self.settings.stdout_file_output:
            with open(testcase.stdout_file_path, mode='w') as f:
                f.write(test_result.stdout)
        if self.settings.stderr_file_output:
            with open(testcase.stderr_file_path, mode='w') as f:
                f.write(test_result.stderr)
        return test_result

from .html_builder import make_html  # 循環import対策
from .testcase_logger import make_log

def run(
        testcase_handler: Callable[[TestCase], TestCaseResult],
        input_file_path: str,
        repeat_count: int = 1,
        copy_target_files: list[str] = [],
        parallel_processing_method: str = "process",
        stdout_file_output: bool = True,
        stderr_file_output: bool = True,
        _debug: bool = False,
        ) -> None:
    """ランナーを実行する

    Args:
        testcase_handler (Callable[[TestCase], TestCaseResult]): 並列実行する関数
        input_file_path (str): 入力ファイル群が置いてあるディレクトリへのパス
        repeat_count (int, optional): それぞれのテストケースを何回実行するか. Defaults to 1.
        copy_target_files (list[str], optional): コピーしたいファイルパスのリスト. Defaults to [].
        parallel_processing_method (str, optional): 並列化の方法(プロセスかスレッドか). Defaults to 'process'.
        stdout_file_output (bool, optional): 標準出力をファイルで保存するかどうか. Defaults to True.
        stderr_file_output (bool, optional): 標準エラー出力をファイルで保存するかどうか. Defaults to True.
    """
    setting = RunnerSettings(
        input_file_path,
        repeat_count,
        copy_target_files,
        parallel_processing_method,
        stdout_file_output,
        stderr_file_output,
        _debug,
    )
    runner = TestCaseRunner(testcase_handler, setting)
    result = runner.start()
    log = make_log(result, setting)
    file = os.path.join(setting.log_folder_name, "result.html")
    make_html(file, log, setting.debug)

# 公開するメンバーを制御する
__all__ = [
    "run",
]
