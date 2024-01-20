import glob
import os
import shutil
import datetime
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, Future
from typing import List, Dict, Any, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import IntEnum, auto
from pathlib import Path
import hashlib
import json
from collections import defaultdict
import warnings
import time

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from jinja2 import Environment, FileSystemLoader

class CustomException(Exception):
    """ライブラリ内で使う例外の基底クラス"""
    pass

class InvalidPathException(CustomException):
    """与えられたパスが正しくない場合の例外"""
    def __init__(self, message):
        super().__init__(message)

class NoTestcaseFileException(CustomException):
    """テストケースファイルが1つもない場合の例外"""
    def __init__(self, message):
        super().__init__(message)

class ResultStatus(IntEnum):
    """テストケースを実行した結果のステータス定義

    結果ファイルに載るだけで特別な処理をするわけではない
    """
    AC = auto()             # Accepted
    WA = auto()             # Wrong Answer
    RE = auto()             # 実行時エラー
    TLE = auto()            # 実行時間制限超過

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

@dataclass
class _RunnerSettings:
    input_file_path: str
    repeat_count: int
    measure_time: bool
    copy_target_files: List[str]
    parallel_processing_method: str
    stdout_file_output: bool
    stderr_file_output: bool
    log_folder_name: str

class _TestCaseRunner:
    def __init__(self,
                 handler: Callable[[TestCase], TestCaseResult],
                 setting: _RunnerSettings,
                 ):
        self.settings = setting
        self.input_file_path = self.settings.input_file_path
        self.handler = handler
        if not self.is_valid_path():
            raise InvalidPathException(f"テストケースファイルへのパス{self.input_file_path}は無効なパスです。")
        self.log_manager = _LogManager(setting)
    
    def is_valid_path(self) -> bool:
        return Path(self.input_file_path).is_dir()
    
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
                stdout_file = os.path.join(self.log_manager.stdout_log_path, basename)
                stderr_file = os.path.join(self.log_manager.stderr_log_path, basename)
                testcase_name = os.path.basename(input_file)
                testcase = TestCase(testcase_name, input_file, stdout_file, stderr_file, testcase_index)
                test_cases.append(testcase)
                testcase_index += 1
        return test_cases
    
    def run(self) -> None:
        futures:List[Future] = []
        test_cases: List[TestCase] = []
        files = glob.glob(os.path.join(self.input_file_path, "*"))
        if len(files) == 0:
            raise NoTestcaseFileException(f"{self.input_file_path}ディレクトリにファイルが1つもありません。")
        test_cases = self.make_testcases(files)
        if self.settings.parallel_processing_method.lower() == "process":
            executor_class = ProcessPoolExecutor
        elif self.settings.parallel_processing_method.lower() == "thread":
            executor_class = ThreadPoolExecutor
        else:
            raise ValueError("引数parallel_processing_methodの値が不正です。")
        with executor_class() as executor:
            for testcase in test_cases:
                future = executor.submit(self.run_testcase, testcase)
                futures.append(future)

        results: List[TestCase] = []
        for future in futures:
            results.append(future.result())
        
        self.make_log(results)
    
    def run_testcase(self, testcase: TestCase) -> Tuple[TestCase, TestCaseResult]:
        start_time = time.time()
        test_result: TestCaseResult = self.handler(testcase)
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
    
    def make_log(self, results: List[Tuple[TestCase, TestCaseResult]]) -> None:
        self.log_manager.make_result_log(results)
        self.log_manager.finalize()

class _LogManager:
    @dataclass
    class Column:
        title: str
        getter: Callable[[int], str]

    log_dir_path = "log"
    js_file_path = "js"
    stdout_dir_path = "stdout"
    stderr_dir_path = "stderr"
    def __init__(self, settings: _RunnerSettings):
        self.base_dir = os.path.split(__file__)[0]
        self.settings = settings
        if self.log_dir_path not in glob.glob("*"):
            os.mkdir(self.log_dir_path)
        self.log_path = self.determine_log_path_name()
        os.mkdir(self.log_path)
        self.fig_dir_path = os.path.join(self.log_path, "fig")
        os.mkdir(self.fig_dir_path)
        self.stdout_log_path = os.path.join(self.log_path, self.stdout_dir_path)
        os.mkdir(self.stdout_log_path)
        self.stderr_log_path = os.path.join(self.log_path, self.stderr_dir_path)
        os.mkdir(self.stderr_log_path)

        loader = FileSystemLoader(os.path.join(self.base_dir, r"templates"))
        self.environment = Environment(loader=loader)

    attributes_display_priority = {
        "in": -8,
        "out": -7,
        "stdout": -6,
        "testcase": -5,
        "status": -4,
        "stderr": -3,
        "score": -2,
        "time": -1,
    }
    def get_attribute_priority(self, attribute):
        return self.attributes_display_priority.get(attribute, 0)

    def determine_log_path_name(self) -> str:
        name = os.path.join(self.log_dir_path, self.settings.log_folder_name)
        i = 1
        while os.path.exists(name):
            name = os.path.join(self.log_dir_path, f"{self.settings.log_folder_name}-{i}")
            i += 1
        return name

    def sortup_attributes(self) -> List[str]:
        attributes = dict() # setだと順番が保持されないのでdictにする
        for test_result in self.results:
            for attribute in test_result.attribute.keys():
                attributes[attribute] = ""
        return list(attributes.keys())
    
    def get_in(self, attribute: Any, row: int) -> str:
        template = self.environment.get_template("cell_with_file_link.j2")
        data = {
            "link": self.testcases[row].input_file_path,
            "value": "+",
            }
        return template.render(data)
    def get_stdout(self, attribute: Any, row: int) -> str:
        template = self.environment.get_template("cell_with_file_link.j2")
        rel_path = os.path.relpath(self.testcases[row].stdout_file_path, self.log_path)
        data = {
            "link": rel_path,
            "value": "+",
            }
        return template.render(data)
    def get_testcase_name(self, attribute: Any, row: int) -> str:
        template = self.environment.get_template("cell.j2")
        data = {
            "value": self.testcases[row].testcase_name,
            }
        return template.render(data)
    def get_stderr(self, attribute: Any, row: int) -> str:
        template = self.environment.get_template("cell_with_file_link.j2")
        rel_path = os.path.relpath(self.testcases[row].stderr_file_path, self.log_path)
        data = {
            "link": rel_path,
            "value": "+",
            }
        return template.render(data)
    status_texts = {
        ResultStatus.AC: ("AC", "lime"),
        ResultStatus.WA: ("WA", "gold"),
        ResultStatus.RE: ("RE", "gold"),
        ResultStatus.TLE: ("TLE", "gold"),
    }
    def get_status(self, attribute: Any, row: int) -> str:
        status = self.results[row].error_status
        text, color = self.status_texts.get(status, ("IE", "red"))
        template = self.environment.get_template("cell_with_color.j2")
        data = {
            "color": color,
            "value": text,
            }
        return template.render(data)
    def get_other(self, _: Any, attribute: str, row: int) -> None:
        attributes = self.results[row].attribute
        if attribute not in attributes:
            value = "---"
        else:
            value = attributes[attribute]
            if type(value) is float:
                value = round(value, 3)
        template = self.environment.get_template("cell.j2")
        data = {
            "value": value,
            }
        return template.render(data)

    columns = [
        Column("in", get_in),
        Column("out", get_stdout),
        Column("stdout", get_stderr),
        Column("testcase", get_testcase_name),
        Column("status", get_status),
    ]
    def analyze_result(self, results: List[Tuple[TestCase, TestCaseResult]]) -> None:
        self.testcases: List[TestCase] = []
        self.results: List[TestCaseResult] = []
        for t, r in results:
            self.testcases.append(t)
            self.results.append(r)
        self.attributes = self.sortup_attributes()

        self.average_score = None
        if "score" not in self.attributes:
            return ""

        file_name_list, scores_list = [], []
        for testcase, result in zip(self.testcases, self.results):
            file_name_list.append(testcase.testcase_name)
            s = 0
            if result.error_status == ResultStatus.AC:
                if "score" in result.attribute:
                    s = result.attribute["score"]
            scores_list.append(s)
        self.average_score = sum(scores_list)/len(self.testcases)

    def make_result_log(self, results: List[Tuple[TestCase, TestCaseResult]]) -> None:
        self.analyze_result(results)
        self.make_json_file()
        self.make_html()
    
    histgram_fig_name = 'histgram.png'
    heatmap_fig_name = 'heatmap.png'
    def make_figure(self) -> str:
        # ヒストグラムを描画
        self.df.hist()
        plt.savefig(os.path.join(self.fig_dir_path, self.histgram_fig_name))
        plt.close()

        # 相関係数のヒートマップ
        corr = self.df.corr(numeric_only=True)
        heatmap = sns.heatmap(corr, annot=True)
        heatmap.set_title('Correlation Coefficient Heatmap')
        plt.savefig(os.path.join(self.fig_dir_path, self.heatmap_fig_name))
        
        ret = []
        template = self.environment.get_template("figure.j2")
        fig = template.render({"link": os.path.join("fig", self.histgram_fig_name)})
        ret.append(fig)
        fig = template.render({"link": os.path.join("fig", self.heatmap_fig_name)})
        ret.append(fig)
        return "".join(ret)

    html_file_name = "result.html"
    def make_html(self) -> None:
        for attribute in self.attributes:
            self.columns.append(self.Column(attribute, self.get_other))
        
        template = self.environment.get_template("main.j2")
        data = {
            "date": datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
            "summary": f"<pre>{self.df.describe()}</pre>",
            "script_list": self.make_script_list(),
            "figures": self.make_figure(),
            "css_list": self.make_css_list(),
            "table": self.make_table(),
            }
        html_file_path = os.path.join(self.log_path, self.html_file_name)
        with open(html_file_path, mode="w") as f:
            f.write(template.render(data))
    
    def make_table(self) -> Dict[str, str]:
        ret = []
        self.columns = sorted(self.columns, key=lambda x: self.get_attribute_priority(x.title))
        for row in range(len(self.results)):
            d = {}
            for column in self.columns:
                d[column.title] = column.getter(self, column.title, row)
            ret.append(d)
        return ret
    
    def make_script_list(self) -> List[str]:
        template = self.environment.get_template("script.j2")
        ret = [
            template.render({"link": r"js/Table.js"}),
        ]
        return ret
    
    def make_css_list(self) -> List[str]:
        template = self.environment.get_template("css.j2")
        ret = [
            template.render({"link": r"js/SortTable.css"}),
            template.render({"link": r"https://newcss.net/new.min.css"}),
        ]
        return ret

    def finalize(self) -> None:
        """html, csv, main, in, outファイルをコピーしてlog以下に保存する"""
        path = os.path.join(self.log_dir_path, self.settings.log_folder_name)
        for file in self.settings.copy_target_files:
            file_path = Path(file)
            if file_path.is_file():
                shutil.copy(file, path)
            elif file_path.is_dir():
                warnings.warn(f"{file}はディレクトリパスです。コピーは行いません。")
            else:
                warnings.warn(f"{file}が見つかりません。コピーは行いません。")
        shutil.copytree(self.settings.input_file_path, os.path.join(path, "in"))
        shutil.copytree(os.path.join(self.base_dir, self.js_file_path), os.path.join(path, self.js_file_path))
    
    json_file_name = "result.json"
    def make_json_file(self) -> None:
        file_hash = ""
        file_names = ""
        contents = defaultdict(list)
        for testcase, result in zip(self.testcases, self.results):
            path = testcase.input_file_path
            file_names += file_names
            file_hash += self.calculate_file_hash(path)
            contents["input_file"].append(testcase.input_file_path)
            contents["stdout_file"].append(testcase.stdout_file_path)
            contents["stderr_file"].append(testcase.stderr_file_path)
            contents["status"].append(self.status_texts[result.error_status][0])
            for key in self.attributes:
                value = result.attribute[key] if key in result.attribute else None
                contents[key].append(value)
        
        file_content_hash = self.calculate_string_hash(file_hash)
        file_name_hash = self.calculate_string_hash(file_names)
        
        json_file = {
            "created_date": datetime.datetime.now().strftime("%Y/%m/%d %H:%M"),
            "testcase_num": len(self.testcases),
            "file_content_hash": file_content_hash,
            "file_name_hash": file_name_hash,
            "has_score": "score" in self.attributes,
            "average_score": self.average_score,
            "contents": contents,
        }
        self.df = pd.DataFrame(contents)
        json_file_path = os.path.join(self.log_path, self.json_file_name)
        with open(json_file_path, 'w') as f:
            json.dump(json_file, f, indent=2)

    def calculate_file_hash(self, file_path: str, hash_algorithm: str ='sha256') -> str:
        hash_obj = hashlib.new(hash_algorithm)
        with open(file_path, 'rb') as file:
            while chunk := file.read(4096):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()

    def calculate_string_hash(self, input_string: str, hash_algorithm: str ='sha256') -> str:
        encoded_string = input_string.encode('utf-8')
        hash_obj = hashlib.new(hash_algorithm)
        hash_obj.update(encoded_string)
        return hash_obj.hexdigest()

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
    if repeat_count <= 0:
        raise ValueError("引数repeat_countの値は1以上の整数である必要があります。")
    if log_folder_name is None:
        log_folder_name = str(datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
    setting = _RunnerSettings(
        input_file_path,
        repeat_count,
        measure_time,
        copy_target_files,
        parallel_processing_method,
        stdout_file_output,
        stderr_file_output,
        log_folder_name,
    )
    runner = _TestCaseRunner(handler, setting)
    runner.run()

# 公開するメンバーを制御する
__all__ = [
    "InvalidPathException",
    "NoTestcaseFileException",
    "ResultStatus",
    "TestCaseResult",
    "TestCase",
    "run",
]
