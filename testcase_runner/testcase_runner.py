import glob
import os
import shutil
import datetime
from concurrent.futures import ProcessPoolExecutor, Future
from typing import List, Dict, Union, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from testcase_runner.html_templates import *

output_file_path = "out"
log_file_path = "log"
html_file_name = "result.html"

class ResultStatus(Enum):
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
    input_file_path: str = "in"
    copy_source_file: bool = True
    source_file_path: str = "main.py"
    stdout_file_output: bool = True
    stderr_file_output: bool = True

@dataclass(frozen=True)
class TestCase:
    testcase_name: str
    input_file: str
    stdout_file: str
    stderr_file: str

runner_setting = RunnerSettings()
def set_setting(setting):
    global runner_setting
    runner_setting = setting

def get_setting()->RunnerSettings:
    return runner_setting

class TestCaseRunner:
    def __init__(self, handler: Callable[[TestCase], TestCaseResult]):
        settings = get_setting()
        self.input_file_path = settings.input_file_path
        self.handler = handler
    
    def run_all_testcase(self)->List[List[Union[TestCase, TestCaseResult]]]:
        futures:List[Future] = []
        test_cases: List[TestCase] = []
        for input_file in glob.glob(os.path.join(self.input_file_path, "*")):
            stdout_file = os.path.join(output_file_path, os.path.basename(input_file))
            path, base_name = os.path.split(stdout_file)
            stderr_file = os.path.join(path, "stdout" + base_name)
            testcase_name = os.path.basename(input_file)
            testcase = TestCase(testcase_name, input_file, stdout_file, stderr_file)
            test_cases.append(testcase)
        with ProcessPoolExecutor() as executor:
            for testcase in test_cases:
                future = executor.submit(self.run_testcase, testcase)
                futures.append(future)

        results: List[TestCase] = []
        for future in futures:
            results.append(future.result())
        return results
    
    def run_testcase(self, testcase: TestCase)->TestCaseResult:
        test_result: TestCaseResult = self.handler(testcase)
        settings = get_setting()
        if settings.stdout_file_output:
            with open(testcase.stdout_file, mode='w') as f:
                f.write(test_result.stdout)
        if settings.stderr_file_output:
            with open(testcase.stderr_file, mode='w') as f:
                f.write(test_result.stderr)
        return testcase, test_result

class HtmlMaker:
    @dataclass
    class Column:
        title: str
        getter: Callable[[int], str]

    def __init__(self, results: List[List[Union[TestCase, TestCaseResult]]]):
        self.testcases: List[TestCase] = []
        self.results: List[TestCaseResult] = []
        for t, r in results:
            self.testcases.append(t)
            self.results.append(r)
        self.attributes = self.sortup_attributes()
        loader = FileSystemLoader(r"testcase_runner\templates")
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
        return table_cell.format(text=html_link_str.format(path=self.testcases[row].input_file, string="+"))
    def get_stdout(self, attribute, row: int):
        template = self.environment.get_template("cell_with_file_link.j2")
        data = {
            "link": self.testcases[row].stdout_file,
            "value": "+",
            }
        return template.render(data)
        return table_cell.format(text=html_link_str.format(path=self.testcases[row].stdout_file, string="+"))
    def get_testcase_name(self, attribute, row: int):
        template = self.environment.get_template("cell.j2")
        data = {
            "value": self.testcases[row].testcase_name,
            }
        return template.render(data)
        return table_cell.format(text=self.testcases[row].testcase_name)
    def get_stderr(self, attribute, row: int):
        template = self.environment.get_template("cell_with_file_link.j2")
        data = {
            "link": self.testcases[row].stderr_file,
            "value": "+",
            }
        return template.render(data)
        return table_cell.format(text=html_link_str.format(path=self.testcases[row].stderr_file, string="+"))
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
        return table_colored_cell.format(color=color, text=text)
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
        return table_cell.format(text=str(value))

    columns = [
        Column("in", get_in),
        Column("out", get_stdout),
        Column("stdout", get_stderr),
        Column("testcase", get_testcase_name),
        Column("status", get_status),
    ]
    def make(self):
        for attribute in self.attributes:
            self.columns.append(self.Column(attribute, self.get_other))
        
        table_body = []
        # テーブルのタイトルを作る
        table = ""
        for column in self.columns:
            table += f'<th>{column.title}</th>'
        table_body.append(table_line.format(text=table))

        # テーブル本体を作る
        for row in range(len(self.results)):
            body = ""
            for column in self.columns:
                body += column.getter(self, column.title, row)
            table_body.append(table_line.format(text=body))
        
        table_all = "<h2>Table</h2>"
        table_all += table_heading.format(body="\n".join(table_body))
        body = f'<h6>Creation date and time: {datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")}</h6>'
        
        body += "<h2>Summary</h2>"
        body += self.make_summary()
        body += table_all

        with open(html_file_name ,'w', encoding='utf-8', newline='\n') as html:
            text = html_text.format(body=body, title="Result")
            text = self.insert_text_into_html_head("<body>", text, css_link1)
            text = self.insert_text_into_html_head("<body>", text, css_link2)
            text = self.insert_text_into_html_head("<body>", text, script_link)
            html.writelines(text)
        self.jinja_test()

    def make_summary(self) -> str:
        """サマリ情報を作る"""
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

        template = self.environment.get_template("score_summary.j2")
        data = {
            "average": sum(scores_list)/len(self.testcases),
            "max_score": max(scores_list),
            "max_score_case": file_name_list[scores_list.index(max(scores_list))],
            "max_score": min(scores_list),
            "min_score": file_name_list[scores_list.index(min(scores_list))],
            }
        return template.render(data)
    
    def insert_text_into_html_head(self, tag: str, html_str: str, text: str) -> str:
        """HTMLの文字列のtagの中に別の文字列を挿入する"""
        html_str_list = html_str.split("\n")
        html_str_list.insert(html_str_list.index(tag) + 1, text)
        return "\n".join(html_str_list)
    
    def get_row(self):
        ret = []
        for row in range(len(self.results)):
            d = {}
            for column in self.columns:
                d[column.title] = column.getter(self, column.title, row)
            ret.append(d)
        return ret
    
    def jinja_test(self):

        # テンプレートをロード
        template = self.environment.get_template("main.j2")  # ファイル名を指定

        # テンプレートに渡すデータ
        data = {
            "date": datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
            "summary": self.make_summary(),
            "testcase_num": 10,
            "data": self.get_row()
            }

        # テンプレートをレンダリング
        output = template.render(data)
        with open("jinja_test.html", mode="w") as f:
            f.write(output)

def init_log():
    """Logフォルダの初期化"""
    shutil.rmtree(output_file_path, ignore_errors=True)
    os.mkdir(output_file_path)

def make_log():
    """html, csv, main, in, outファイルをコピーしてlog以下に保存する"""
    settings = get_setting()
    if log_file_path not in glob.glob("*"):
        os.mkdir(log_file_path)
    path = os.path.join(log_file_path, str(datetime.datetime.now().strftime('%Y%m%d%H%M%S')))
    os.mkdir(path)

    settings = get_setting()
    # mainファイルコピー
    if settings.copy_source_file:
        source_file_path = Path(settings.source_file_path)
        if source_file_path.is_file():
            shutil.copy(source_file_path, path)
    # htmlファイルコピー
    shutil.copy(html_file_name, path)
    os.remove(html_file_name) #ファイル削除
    # inファイルコピー
    shutil.copytree(settings.input_file_path, os.path.join(path, "in"))
    # outディレクトリのファイルをコピーしてディレクトリを消す
    shutil.copytree(output_file_path, os.path.join(path, "out"))
    shutil.rmtree(output_file_path, ignore_errors=True)

def run_testcase(run_handler: Callable[[TestCase], TestCaseResult],
        runner_setting:RunnerSettings=RunnerSettings()):
    """run_handlerで指定した関数の処理を並列実行して結果をHTMLファイルにまとめる

    Args:
        run_handler (Callable[[TestCase], TestCaseResult]):
            並列実行したい処理
            run_handlerとして渡す関数の形式について
                引数は テストケース クラス
                戻り値はTestCaseResultクラス 実行結果を各メンバに登録して返す
        runner_setting (RunnerSettings, optional): Defaults to RunnerSettings().
            ランナーを実行するときの設定
            オプション引数を渡さないとデフォルトのRunnerSettingsクラスの設定になる
    """
    set_setting(runner_setting)
    init_log()
    runner = TestCaseRunner(run_handler)
    results = runner.run_all_testcase()
    html_maker = HtmlMaker(results)
    html_maker.make()
    make_log()
