import glob
import os
import shutil
import datetime
from concurrent.futures import ProcessPoolExecutor, Future
from typing import List, Dict, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import IntEnum, auto
from pathlib import Path
import hashlib
import json
from collections import defaultdict

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from jinja2 import Environment, FileSystemLoader

output_file_path = "out"
log_file_path = "log"
js_file_path = "js"
html_file_name = "result.html"
json_file_name = "result.json"

class ResultStatus(IntEnum):
    """テストケースを実行した結果のステータス定義

    結果ファイルに載るだけで特別な処理をするわけではない
    """
    AC = auto()             # Accepted
    WA = auto()             # Wrong Answer
    RE = auto()             # 実行時エラー
    TLE = auto()            # 実行時間制限超過
    RUNNER_ERROR = auto()   # runnerプログラムのエラー(テストケースの結果ではないが都合がいいのでここで定義しちゃう)

@dataclass
class TestCaseResult:
    """テストケースの結果をまとめて管理するクラス"""
    error_status: ResultStatus = ResultStatus.AC # 終了のステータス
    stdout: str = ""                             # 標準出力(なければ空文字でいい)
    stderr: str = ""                             # 標準エラー出力(なければ空文字でいい)
    attribute: Dict[str, Union[int, float]] \
        = field(default_factory=dict)            # 結果ファイルに乗せたい情報の一覧

@dataclass(frozen=True)
class RunnerSettings:
    """ランナーの設定
    
    input_file_path: 入力ファイル群が置いてあるディレクトリへのパス
    copy_source_file: ソースファイルをコピーするかどうか
    source_file_path: コピーするソースファイルへのパス
    stdout_file_output: 標準出力をファイル出力するかどうか
    stderr_file_output: 標準エラー出力をファイル出力するかどうか
    log_folder_name: logを保存するフォルダの名前
    """
    input_file_path: str = "in"
    copy_source_file: bool = False
    source_file_path: str = ""
    stdout_file_output: bool = True
    stderr_file_output: bool = True
    log_folder_name: str = str(datetime.datetime.now().strftime('%Y%m%d%H%M%S'))

@dataclass(frozen=True)
class TestCase:
    testcase_name: str
    input_file: str
    stdout_file: str
    stderr_file: str

class TestCaseRunner:
    def __init__(self,
                 handler: Callable[[TestCase], TestCaseResult],
                 setting: RunnerSettings = RunnerSettings(),
                 ):
        self.settings = setting
        self.input_file_path = self.settings.input_file_path
        self.handler = handler
        self.log_manager = LogManager(setting)
    
    def run(self):
        futures:List[Future] = []
        test_cases: List[TestCase] = []
        for input_file in sorted(glob.glob(os.path.join(self.input_file_path, "*"))):
            stdout_file = os.path.join(output_file_path, os.path.basename(input_file))
            path, base_name = os.path.split(stdout_file)
            stderr_file = os.path.join(path, "stdout" + base_name)
            testcase_name = os.path.basename(input_file)
            testcase = TestCase(testcase_name, input_file, stdout_file, stderr_file)
            test_cases.append(testcase)
        with ProcessPoolExecutor() as executor:
            for testcase in test_cases:
                future = executor.submit(self._run_testcase, testcase)
                futures.append(future)

        results: List[TestCase] = []
        for future in futures:
            results.append(future.result())
        
        self.__make_log(results)
    
    def _run_testcase(self, testcase: TestCase)->Tuple[TestCase, TestCaseResult]:
        test_result: TestCaseResult = self.handler(testcase)
        if self.settings.stdout_file_output:
            with open(testcase.stdout_file, mode='w') as f:
                f.write(test_result.stdout)
        if self.settings.stderr_file_output:
            with open(testcase.stderr_file, mode='w') as f:
                f.write(test_result.stderr)
        return testcase, test_result
    
    def __make_log(self, results):
        self.log_manager.make_result_log(results)
        self.log_manager.finalize()

class LogManager:
    @dataclass
    class Column:
        title: str
        getter: Callable[[int], str]

    def __init__(self, settings: RunnerSettings):
        self.base_dir = os.path.split(__file__)[0]
        self.settings = settings
        shutil.rmtree(output_file_path, ignore_errors=True)
        os.mkdir(output_file_path)
        loader = FileSystemLoader(os.path.join(self.base_dir, r"templates"))
        print(os.path.join(self.base_dir, r"templates"))
        self.environment = Environment(loader=loader)
    
    def sortup_attributes(self):
        attributes = dict() # setだと順番が保持されないのでdictにする
        for test_result in self.results:
            for attribute in test_result.attribute.keys():
                attributes[attribute] = ""
        return list(attributes.keys())
    
    def get_in(self, attribute, row: int):
        template = self.environment.get_template("cell_with_file_link.j2")
        data = {
            "link": self.testcases[row].input_file,
            "value": "+",
            }
        return template.render(data)
    def get_stdout(self, attribute, row: int):
        template = self.environment.get_template("cell_with_file_link.j2")
        data = {
            "link": self.testcases[row].stdout_file,
            "value": "+",
            }
        return template.render(data)
    def get_testcase_name(self, attribute, row: int):
        template = self.environment.get_template("cell.j2")
        data = {
            "value": self.testcases[row].testcase_name,
            }
        return template.render(data)
    def get_stderr(self, attribute, row: int):
        template = self.environment.get_template("cell_with_file_link.j2")
        data = {
            "link": self.testcases[row].stderr_file,
            "value": "+",
            }
        return template.render(data)
    status_texts = {
        ResultStatus.AC: ("AC", "lime"),
        ResultStatus.WA: ("WA", "gold"),
        ResultStatus.RE: ("RE", "gold"),
        ResultStatus.TLE: ("TLE", "gold"),
        ResultStatus.RUNNER_ERROR: ("IE", "red"),
    }
    def get_status(self, attribute, row: int):
        status = self.results[row].error_status
        if status not in self.status_texts:
            status = ResultStatus.RUNNER_ERROR
        text, color = self.status_texts[status]
        template = self.environment.get_template("cell_with_color.j2")
        data = {
            "color": color,
            "value": text,
            }
        return template.render(data)
    def get_other(self, _, attribute: str, row: int):
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
    def analyze_result(self, results):
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

    def make_result_log(self, results: List[Tuple[TestCase, TestCaseResult]]):
        self.analyze_result(results)
        self.make_json_file()
        self.make_html()
    
    def make_figure(self):
        # ヒストグラムを描画
        self.df.hist()
        plt.savefig('histgram.png')
        plt.close()

        # 相関係数のヒートマップ
        corr = self.df.corr(numeric_only=True)
        heatmap = sns.heatmap(corr, annot=True)
        heatmap.set_title('Correlation Coefficient Heatmap')
        plt.savefig('heatmap.png')
        
        ret = []
        template = self.environment.get_template("figure.j2")
        fig = template.render({"link": os.path.join("fig", "histgram.png")})
        ret.append(fig)
        fig = template.render({"link": os.path.join("fig", "heatmap.png")})
        ret.append(fig)
        return "".join(ret)

    def make_html(self):
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
        output = template.render(data)
        with open("result.html", mode="w") as f:
            f.write(output)
    
    def make_table(self):
        ret = []
        for row in range(len(self.results)):
            d = {}
            for column in self.columns:
                d[column.title] = column.getter(self, column.title, row)
            ret.append(d)
        return ret
    
    def make_script_list(self):
        template = self.environment.get_template("script.j2")
        ret = [
            template.render({"link": r"js/Table.js"}),
        ]
        return ret
    
    def make_css_list(self):
        template = self.environment.get_template("css.j2")
        ret = [
            template.render({"link": r"js/SortTable.css"}),
            template.render({"link": r"https://newcss.net/new.min.css"}),
        ]
        return ret

    def finalize(self):
        """html, csv, main, in, outファイルをコピーしてlog以下に保存する"""
        if log_file_path not in glob.glob("*"):
            os.mkdir(log_file_path)
        path = os.path.join(log_file_path, self.settings.log_folder_name)
        i = 1
        while os.path.exists(path):
            path = os.path.join(log_file_path, f"{self.settings.log_folder_name}_{i}")
            i += 1
        os.mkdir(path)
        # mainファイルコピー
        if self.settings.copy_source_file:
            source_file_path = Path(self.settings.source_file_path)
            if source_file_path.is_file():
                shutil.copy(source_file_path, path)
        # htmlファイルコピー
        shutil.copy(html_file_name, path)
        shutil.copy(json_file_name, path)
        os.remove(html_file_name) #ファイル削除
        os.remove(json_file_name) #ファイル削除
        # inファイルコピー
        shutil.copytree(self.settings.input_file_path, os.path.join(path, "in"))
        # outディレクトリのファイルをコピーしてディレクトリを消す
        shutil.copytree(output_file_path, os.path.join(path, "out"))
        shutil.rmtree(output_file_path, ignore_errors=True)

        #HTMLの表示に必要なファイルをコピーする
        shutil.copytree(os.path.join(self.base_dir, js_file_path), os.path.join(path, js_file_path))
        
        # 画像をコピー
        fig_dir = os.path.join(path, "fig")

        os.mkdir(fig_dir)
        fr = "histgram.png"
        to = os.path.join(fig_dir, "histgram.png")
        shutil.copy(fr, to)
        os.remove(fr)

        fr = "heatmap.png"
        to = os.path.join(fig_dir, "heatmap.png")
        shutil.copy(fr, to)
        os.remove(fr)
    
    def make_json_file(self):
        file_hash = ""
        file_names = ""
        contents = defaultdict(list)
        for testcase, result in zip(self.testcases, self.results):
            path = testcase.input_file
            file_names += file_names
            file_hash += self.calculate_file_hash(path)
            contents["input_file"].append(testcase.input_file)
            contents["stdout_file"].append(testcase.stdout_file)
            contents["stderr_file"].append(testcase.stderr_file)
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
        with open(json_file_name, 'w') as f:
            json.dump(json_file, f, indent=2)

    def calculate_file_hash(self, file_path, hash_algorithm='sha256'):
        hash_obj = hashlib.new(hash_algorithm)
        with open(file_path, 'rb') as file:
            while chunk := file.read(4096):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    
    def calculate_string_hash(self, input_string: str, hash_algorithm='sha256'):
        encoded_string = input_string.encode('utf-8')
        hash_obj = hashlib.new(hash_algorithm)
        hash_obj.update(encoded_string)
        return hash_obj.hexdigest()

def run(
        handler: Callable[[TestCase], TestCaseResult],
        input_file_path: str = "in",
        copy_source_file: bool = False,
        source_file_path: str = "",
        stdout_file_output: bool = True,
        stderr_file_output: bool = True,
        log_folder_name: str = str(datetime.datetime.now().strftime('%Y%m%d%H%M%S')),
        ):
    """ランナーを実行する

    Args:
        handler (Callable[[TestCase], TestCaseResult]): 並列実行する関数
        input_file_path (str, optional): 入力ファイル群が置いてあるディレクトリへのパス. Defaults to "in".
        copy_source_file (bool, optional): ログファイルを作るときにソースファイルをコピーするかどうか. Defaults to False.
        source_file_path (str, optional): コピーするファイルへのパス. Defaults to "".
        stdout_file_output (bool, optional): 標準出力をファイルで保存するかどうか. Defaults to True.
        stderr_file_output (bool, optional): 標準エラー出力をファイルで保存するかどうか. Defaults to True.
        log_folder_name (str, optional): ログフォルダの名前. Defaults to str(datetime.datetime.now().strftime('%Y%m%d%H%M%S')).
    """
    setting = RunnerSettings(
        input_file_path,
        copy_source_file,
        source_file_path,
        stdout_file_output,
        stderr_file_output,
        log_folder_name,
    )
    runner = TestCaseRunner(handler, setting)
    runner.run()
