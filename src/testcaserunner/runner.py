import glob
import os
import shutil
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, Future
from typing import List, Dict, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import IntEnum, auto
from pathlib import Path
import warnings
import time

from tqdm import tqdm

from .exceptions import InvalidPathException, NoTestcaseFileException

class ResultStatus(IntEnum):
    """テストケースを実行した結果のステータス定義

    結果ファイルに載るだけで特別な処理をするわけではない
    """
    AC = auto()             # Accepted
    WA = auto()             # Wrong Answer
    RE = auto()             # 実行時エラー
    TLE = auto()            # 実行時間制限超過
    IE = auto()             # 内部エラー

@dataclass
class TestCaseResult:
    """テストケースの結果をまとめて管理するクラス"""
    error_status: ResultStatus = ResultStatus.AC # 終了のステータス
    stdout: str = ""                             # 標準出力(なければ空文字でいい)
    stderr: str = ""                             # 標準エラー出力(なければ空文字でいい)
    attribute: Dict[str, Union[int, float]] \
        = field(default_factory=dict)            # 結果ファイルに乗せたい情報の一覧

@dataclass(frozen=True)
class TestCase:
    testcase_name: str
    input_file_path: str
    stdout_file_path: str
    stderr_file_path: str
    testcase_index: int

    def read_testcase_lines(self):
        """テストケースファイルの内容を1行ずつ取得するジェネレータ

        Yields:
            str: ファイルの各行の内容
        """
        with open(self.input_file_path, mode="r") as file:
            for line in file:
                yield line.strip()

class RunnerSettings:
    stdout_dir_path = "stdout"
    stderr_dir_path = "stderr"
    log_dir_path = "log"
    def __init__(
        self,
        input_file_path: str,
        repeat_count: int,
        measure_time: bool,
        copy_target_files: List[str],
        parallel_processing_method: str,
        stdout_file_output: bool,
        stderr_file_output: bool,
        log_folder_name: str,
    ):
        self.input_file_path: str = input_file_path
        self.repeat_count: int = repeat_count
        self.measure_time: bool = measure_time
        self.copy_target_files: List[str] = copy_target_files
        self.parallel_processing_method: str = parallel_processing_method
        self.stdout_file_output: bool = stdout_file_output
        self.stderr_file_output: bool = stderr_file_output
        self.log_folder_name: str = log_folder_name

        if not Path(self.input_file_path).is_dir():
            raise InvalidPathException(f"テストケースファイルへのパス{self.input_file_path}は無効なパスです。")

        if self.log_dir_path not in glob.glob("*"):
            os.mkdir(self.log_dir_path)
        self.log_path = self.determine_log_path_name()
        os.mkdir(self.log_path)
        self.stdout_log_path = os.path.join(self.log_path, self.stdout_dir_path)
        os.mkdir(self.stdout_log_path)
        self.stderr_log_path = os.path.join(self.log_path, self.stderr_dir_path)
        os.mkdir(self.stderr_log_path)
        self.input_file_copy_path = os.path.join(self.log_dir_path, self.log_folder_name, "in")
        shutil.copytree(self.input_file_path, self.input_file_copy_path)
        self.fig_dir_path = os.path.join(self.log_path, "fig")
        os.mkdir(self.fig_dir_path)

    def determine_log_path_name(self) -> str:
        name = os.path.join(self.log_dir_path, self.log_folder_name)
        i = 1
        while os.path.exists(name):
            name = os.path.join(self.log_dir_path, f"{self.log_folder_name}-{i}")
            i += 1
        return name

class TestCaseRunner:
    def __init__(self,
                 handler: Callable[[TestCase], TestCaseResult],
                 setting: RunnerSettings,
                 ):
        self.settings = setting
        self.input_file_path = self.settings.input_file_copy_path
        self.handler = handler
    
    def make_testcases(self, files: List[str]) -> List[TestCase]:
        test_cases = []
        testcase_index = 0
        for input_file in sorted(files):
            for rep in range(self.settings.repeat_count):
                if self.settings.repeat_count != 0:
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
    
    def run(self) -> List[Tuple[TestCase, TestCaseResult]]:
        futures:List[Future] = []
        test_cases: List[TestCase] = []
        files = glob.glob(os.path.join(self.input_file_path, "*"))
        if len(files) == 0:
            raise NoTestcaseFileException(f"{self.input_file_path}ディレクトリにファイルが1つもありません。")
        test_cases = self.make_testcases(files)
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

        results: List[TestCase] = []
        if parallel:
            with tqdm(total=len(test_cases)) as progress:
                with executor_class() as executor:
                    for testcase in test_cases:
                        future = executor.submit(self.run_testcase, testcase)
                        future.add_done_callback(lambda p: progress.update())
                        futures.append(future)
                
                for future in futures:
                    results.append(future.result())
        else:
            for testcase in tqdm(test_cases):
                result = self.run_testcase(testcase)
                results.append(result)
        
        return results
    
    def run_testcase(self, testcase: TestCase) -> Tuple[TestCase, TestCaseResult]:
        start_time = time.time()
        try:
            test_result: TestCaseResult = self.handler(testcase)
        except Exception as e:
            msg = f"テストケース{os.path.basename(testcase.input_file_path)}において、\
                引数で渡された関数の中で例外が発生しました。\n{str(e)}"
            warnings.warn(msg)
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

# 公開するメンバーを制御する
__all__ = [
    "TestCaseResult",
    "TestCase",
]
