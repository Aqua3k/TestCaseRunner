from typing import Iterator
from dataclasses import dataclass, field
from enum import IntEnum, auto

@dataclass(frozen=True)
class RunnerMetadata:
    LIB_NAME: str = "testcaserunner"
    LIB_VERSION: str = "1.0.0"

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

@dataclass
class TestCaseResult:
    """テストケースの結果をまとめて管理するクラス"""
    attribute: dict[str, int | float] \
        = field(default_factory=dict)    # 結果ファイルに乗せたい情報の一覧
    stdout: str|None = None              # 標準出力(なければ空文字でいい)
    stderr: str|None = None              # 標準エラー出力(なければ空文字でいい)
    error_status: str|None = None        # エラーステータス
    result_description: str|None = None  # 実行結果の詳細な説明(任意)

@dataclass(frozen=True)
class TestCase:
    testcase_name: str
    input_file_path: str
    stdout_file_path: str
    stderr_file_path: str
    testcase_index: int
