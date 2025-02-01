import glob
import os
from typing import Callable
import time
import shutil
from pathlib import Path
from dataclasses import dataclass
import traceback

from ..debug import RunnerLogger
from ..defines import TestCase, TestCaseResult, NoTestcaseFileException, InvalidPathException
from .executor_worker import BaseExecutor, ProcessParallelExecutor, ThreadParallelExecutor, SerialExecutor
from ..defines import InternalError

@dataclass
class ParallelExecutor:
    testcase_handler: Callable[[TestCase], TestCaseResult|None]
    input_file_path: str
    log_folder_name: str
    repeat_count: int
    copy_target_files: list[str]
    parallel_processing_method: str
    time_limit_: int|float|None
    debug: bool
    def __post_init__(self) -> None:
        self.logger = RunnerLogger("ParallelExecutor")
        self.init_parameters()
        self.init_folders()
        if self.debug:
            self.logger.enable_debug_mode()
        self.input_file_path = self.input_file_copy_path
        if self.time_limit_ is None:
            self.time_limit = float("inf")
        else:
            self.time_limit = self.time_limit_

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

    def get_executor(self) -> type[BaseExecutor]:
        match self.parallel_processing_method.lower():
            case "process":
                return ProcessParallelExecutor
            case "thread":
                return ThreadParallelExecutor
            case "single":
                return SerialExecutor
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
            results: list[TestCaseResult|None] = executor.wait_and_get_results()
        
        parsed_results: list[TestCaseResult] = []
        for result in results:
            if result is None:
                result = TestCaseResult(
                    error_status="Canceled",
                    result_description="The program was interrupted (via Ctrl+C).",
                    )
            parsed_results.append(result)
        
        if  len(test_cases) != len(results):
            raise InternalError("入力と出力の数が一致しません。")
        return list(zip(test_cases, parsed_results))
    
    def run_testcase(self, testcase: TestCase) -> TestCaseResult:
        def unwrap_result(result: TestCaseResult|None) -> TestCaseResult:
            return result if result is not None else TestCaseResult()
        start_time = time.time()
        has_error = False
        try:
            test_result: TestCaseResult|None = self.testcase_handler(testcase)
        except Exception as e:
            error_details = traceback.format_exc()
            has_error = True
            self.logger.warning(f"テストケース{os.path.basename(testcase.input_file_path)}において、\
                引数で渡された関数の中で例外が発生しました。\n{str(e)}")
            test_result = TestCaseResult(
                stderr=error_details,
                error_status="Callback Error",
                result_description="An exception occurred in the provided callback function. Please check your callback implementation for errors. For more details, refer to `stderr`.",
                )
        test_result = unwrap_result(test_result)
        erapsed_time = time.time() - start_time
        if not has_error and test_result.error_status is None:
            if self.time_limit < erapsed_time:
                # 時間制限超過はエラーが発生していない時だけ記録する
                test_result.error_status = "TLE"
                test_result.result_description = "Your program has exceeded the time limit."
            
        test_result.attribute["time"] = erapsed_time
        if test_result.stdout is not None:
            with open(testcase.stdout_file_path, mode='w') as f:
                f.write(test_result.stdout)
        if test_result.stderr is not None:
            with open(testcase.stderr_file_path, mode='w') as f:
                f.write(test_result.stderr)
        return test_result
