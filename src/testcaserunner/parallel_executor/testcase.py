from dataclasses import dataclass, field

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
