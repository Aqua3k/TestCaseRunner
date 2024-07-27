import shutil
from pathlib import Path
import datetime
from typing import Union, Iterator
import os
import glob
from dataclasses import dataclass, field
from enum import IntEnum, auto

class CustomException(Exception):
    """ライブラリ内で使う例外の基底クラス"""
    pass

class InvalidPathException(CustomException):
    """与えられたパスが正しくない場合の例外"""
    def __init__(self, message) -> None:
        super().__init__(message)

class NoTestcaseFileException(CustomException):
    """テストケースファイルが1つもない場合の例外"""
    def __init__(self, message) -> None:
        super().__init__(message)

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
    attribute: dict[str, Union[int, float]] \
        = field(default_factory=dict)            # 結果ファイルに乗せたい情報の一覧

@dataclass(frozen=True)
class TestCase:
    testcase_name: str
    input_file_path: str
    stdout_file_path: str
    stderr_file_path: str
    testcase_index: int

    def read_testcase_lines(self) -> Iterator[str]:
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
        copy_target_files: list[str],
        parallel_processing_method: str,
        stdout_file_output: bool,
        stderr_file_output: bool,
        log_folder_name: Union[str, None],
        debug: bool,
    ) -> None:
        self.debug = debug
        self.input_file_path: str = input_file_path
        self.repeat_count: int = repeat_count
        self.measure_time: bool = measure_time
        self.copy_target_files: list[str] = copy_target_files
        self.parallel_processing_method: str = parallel_processing_method
        self.stdout_file_output: bool = stdout_file_output
        self.stderr_file_output: bool = stderr_file_output
        self.datetime = datetime.datetime.now()
        self.log_folder_name: str = self.get_log_file_path(log_folder_name)

        if repeat_count <= 0:
            raise ValueError("引数repeat_countの値は1以上の整数である必要があります。")

        if not Path(self.input_file_path).is_dir():
            raise InvalidPathException(f"テストケースファイルへのパス{self.input_file_path}は無効なパスです。")

        if self.log_dir_path not in glob.glob("*"):
            os.mkdir(self.log_dir_path)
        os.mkdir(self.log_folder_name)
        self.stdout_log_path = os.path.join(self.log_folder_name, self.stdout_dir_path)
        os.mkdir(self.stdout_log_path)
        self.stderr_log_path = os.path.join(self.log_folder_name, self.stderr_dir_path)
        os.mkdir(self.stderr_log_path)
        self.input_file_copy_path = os.path.join(self.log_folder_name, "in")
        shutil.copytree(self.input_file_path, self.input_file_copy_path)
        self.fig_dir_path = os.path.join(self.log_folder_name, "fig")
        os.mkdir(self.fig_dir_path)

    def get_log_file_path(self, log_folder_name: Union[str, None]) -> str:
        if log_folder_name is None:
            log_folder_name = str(self.datetime.strftime('%Y%m%d%H%M%S'))
        name = os.path.join(self.log_dir_path, log_folder_name)
        i = 1
        while os.path.exists(name):
            name = os.path.join(self.log_dir_path, f"{log_folder_name}-{i}")
            i += 1
        return name
