from dataclasses import dataclass, field

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
    """テストケースの結果情報を管理するクラス"""
    attribute: dict[str, int | float] \
        = field(default_factory=dict)    # 結果ファイルに乗せたい情報の一覧
    stdout: str|None = None              # 標準出力
    stderr: str|None = None              # 標準エラー出力
    error_status: str|None = None        # エラーステータス
    result_description: str|None = None  # 実行結果の詳細な説明

@dataclass(frozen=True)
class TestCase:
    testcase_name: str
    input_file_path: str
    stdout_file_path: str
    stderr_file_path: str
    testcase_index: int
