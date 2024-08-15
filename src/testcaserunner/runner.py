import glob
import os
from typing import Callable
import time
from typing import Optional
import shutil
from pathlib import Path
import datetime
from dataclasses import dataclass

from .runner_defines import TestCase, TestCaseResult, ResultStatus, NoTestcaseFileException, InvalidPathException
from .logger import RunnerLogger
from .testccase_executor import TestcaseExecutor, ProcessTestcaseExecutor, ThreadTestcaseExecutor, SingleTestcaseExecutor
from .html_builder import make_html
from .testcase_logger import make_log

@dataclass
class TestCaseRunner:
    testcase_handler: Callable[[TestCase], TestCaseResult]
    input_file_path: str
    log_folder_name: str
    repeat_count: int
    copy_target_files: list[str]
    parallel_processing_method: str
    stdout_file_output: bool
    stderr_file_output: bool
    debug: bool
    def __post_init__(self) -> None:
        self.logger = RunnerLogger("TestCaseRunner")
        self.init_parameters()
        self.init_folders()
        if self.debug:
            self.logger.enable_debug_mode()
        self.input_file_path = self.input_file_copy_path

    def make_folder(self, path: str) -> None:
        os.makedirs(path, exist_ok=True)

    def copy_folder(self, src: str, dst: str) -> None:
        shutil.copytree(src, dst)

    def copy_file(self, src: str, dst: str) -> None:
        shutil.copy(src, dst)
    
    def copy_files(self) -> None:
        for file in self.copy_target_files:
            file_path = Path(file)
            if file_path.is_file():
                self.copy_file(file, self.log_folder_name)
            elif file_path.is_dir():
                self.logger.warning(f"{file}はディレクトリパスです。コピーは行いません。")
            else:
                self.logger.warning(f"{file}が見つかりません。コピーは行いません。")

    def init_folders(self) -> None:
        self.make_folder(self.log_folder_name)
        self.make_folder(self.stdout_log_path)
        self.make_folder(self.stderr_log_path)
        self.make_folder(self.stdout_log_path)
        self.copy_folder(self.input_file_path, self.input_file_copy_path)
        self.copy_files()

    def get_executor(self) -> type[TestcaseExecutor]:
        match self.parallel_processing_method.lower():
            case "process":
                return ProcessTestcaseExecutor
            case "thread":
                return ThreadTestcaseExecutor
            case "single":
                return SingleTestcaseExecutor
            case _:
                raise ValueError("引数parallel_processing_methodの値が不正です。")

    def init_parameters(self) -> None:
        self.stdout_log_path = os.path.join(self.log_folder_name, "stdout")
        self.stderr_log_path = os.path.join(self.log_folder_name, "stderr")
        self.input_file_copy_path = os.path.join(self.log_folder_name, "in")
        self.Executor = self.get_executor()

        if self.repeat_count <= 0 or type(self.repeat_count) is not int:
            raise ValueError("引数repeat_countの値は1以上の整数である必要があります。")
        if not Path(self.input_file_path).is_dir():
            raise InvalidPathException(f"テストケースファイルへのパス{self.input_file_path}は無効なパスです。")
        if len(glob.glob(os.path.join(self.input_file_path, "*"))) == 0:
            raise NoTestcaseFileException(f"{self.input_file_path}ディレクトリにファイルが1つもありません。")
    
    def make_testcases(self) -> list[TestCase]:
        files = glob.glob(os.path.join(self.input_file_path, "*"))
        test_cases = []
        testcase_index = 0
        for input_file in sorted(files):
            for rep in range(self.repeat_count):
                if self.repeat_count != 1:
                    name, extension = os.path.splitext(os.path.basename(input_file))
                    basename = f"{name}_{rep+1}{extension}"
                else:
                    basename = os.path.basename(input_file)
                stdout_file = os.path.join(self.stdout_log_path, basename)
                stderr_file = os.path.join(self.stderr_log_path, basename)
                testcase_name = os.path.basename(input_file)
                testcase = TestCase(testcase_name, input_file, stdout_file, stderr_file, testcase_index)
                test_cases.append(testcase)
                testcase_index += 1
        return test_cases

    def start(self) -> list[tuple[TestCase, TestCaseResult]]:
        test_cases: list[TestCase] = self.make_testcases()

        self.logger.debug("start testcase run process.")
        with self.Executor(len(test_cases)) as executor:
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
        if self.stdout_file_output:
            with open(testcase.stdout_file_path, mode='w') as f:
                f.write(test_result.stdout)
        if self.stderr_file_output:
            with open(testcase.stderr_file_path, mode='w') as f:
                f.write(test_result.stderr)
        return test_result

def get_log_file_path() -> str:
    log_name = str(datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
    name = os.path.join("log", log_name)
    i = 1
    while os.path.exists(name):
        name = os.path.join("log", f"{log_name}-{i}")
        i += 1
    return name

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
    log_folder_name = get_log_file_path()
    runner = TestCaseRunner(
        testcase_handler,
        input_file_path,
        log_folder_name,
        repeat_count,
        copy_target_files,
        parallel_processing_method,
        stdout_file_output,
        stderr_file_output,
        _debug,
    )
    result = runner.start()
    log = make_log(result, log_folder_name, _debug)
    file = os.path.join(log_folder_name, "result.html")
    make_html(file, log, _debug)

# 公開するメンバーを制御する
__all__ = [
    "run",
]
