import glob
import os
import shutil
import datetime
from concurrent.futures import ProcessPoolExecutor, Future
from typing import List, Dict, Union, Callable
from dataclasses import dataclass
from enum import Enum, auto
import configparser

from runner_.html_templates import *

class ResultStatus(Enum):
    """テストケースを実行した結果のステータス定義"""
    AC = auto()             # 正常終了
    RE = auto()             # 実行時エラー
    TLE = auto()            # 実行時間制限超過
    RUNNER_ERROR = auto()   # runnerプログラムのエラー(テストケースの結果ではないが都合がいいのでここで定義しちゃう)

@dataclass
class TestCaseResult:
    """テストケースの結果をまとめて管理するクラス"""
    error_status: ResultStatus              # 終了のステータス
    stdout: str                             # 標準出力(なければ空文字でいい)
    stderr: str                             # 標準エラー出力(なければ空文字でいい)
    attribute: Dict[str, Union[int, float]] # 結果ファイルに乗せたい情報の一覧

@dataclass
class Settings:
    input_file_path: str
    output_file_path: str
    log_file_path: str

config = None
def get_config():
    global config
    if config == None:
        config = configparser.ConfigParser()
        config.read(r'runner_/config.ini', encoding='utf-8')
    return config

def get_setting():
    config = get_config()
    input_file_path = config["path"]["in"]
    output_file_path = config["path"]["out"]
    log_file_path = config["path"]["log"]

    return Settings(input_file_path, output_file_path, log_file_path)

class TestCaseRunner:
    def __init__(self, settings: Settings, handler: Callable[[str, str], TestCaseResult]):
        self.input_file_path = settings.input_file_path
        self.output_file_path = settings.output_file_path
        self.handler = handler
    
    def run(self)->List[List[Union[str, TestCaseResult]]]:
        futures:List[Future] = []
        results: List[TestCase] = []
        test_cases: List[TestCase] = []
        for input_file in glob.glob(os.path.join(self.input_file_path, "*")):
            output_file = os.path.join(self.output_file_path, os.path.basename(input_file))
            test_case = TestCase(input_file, output_file, self.handler)
            test_cases.append(test_case)
        with ProcessPoolExecutor() as executor:
            for test_case in test_cases:
                future = executor.submit(test_case.run_test_case)
                futures.append(future)
        
        for future in futures:
            results.append(future.result())
        return results

class TestCase:
    def __init__(self, input_file, output_file, run_handler: Callable[[str, str], TestCaseResult]):
        self.input_file = input_file
        self.stdout_file = output_file
        path, base_name = os.path.split(output_file)
        self.stderr_file = os.path.join(path, "stdout" + base_name)
        self.test_case_name = os.path.basename(self.input_file)
        self.handler = run_handler
    
    def run_test_case(self)->'TestCase':
        self.test_result: TestCaseResult = self.handler(self.input_file, self.stdout_file)
        with open(self.stdout_file, mode='w') as f:
            f.write(self.test_result.stdout)
        with open(self.stderr_file, mode='w') as f:
            f.write(self.test_result.stderr)
        return self

class HtmlMaker:
    @dataclass
    class Column:
        title: str
        getter: Callable[[int], str]

    def __init__(self, results: List[TestCase]):
        self.results = results
        self.attributes = self.sortup_attributes()
    
    def sortup_attributes(self):
        attributes = dict() # setだと順番が保持されないのでdictにする
        for result in self.results:
            test_result = result.test_result
            for attribute in test_result.attribute.keys():
                attributes[attribute] = ""
        return list(attributes.keys())
    
    def get_in(self, attribute, row: int):
        return table_cell.format(text=html_link_str.format(path=self.results[row].input_file, string="+"))
    def get_stdout(self, attribute, row: int):
        return table_cell.format(text=html_link_str.format(path=self.results[row].stdout_file, string="+"))
    def get_testcase_name(self, attribute, row: int):
        return table_cell.format(text=self.results[row].test_case_name)
    def get_stderr(self, attribute, row: int):
        return table_cell.format(text=html_link_str.format(path=self.results[row].stderr_file, string="+"))
    status_texts = {
        ResultStatus.AC: ("AC", "lime"),
        ResultStatus.RE: ("RE", "gold"),
        ResultStatus.TLE: ("TLE", "gold"),
        ResultStatus.RUNNER_ERROR: ("IE", "red"),
    }
    def get_status(self, attribute, row: int):
        status = self.results[row].test_result.error_status
        if status not in self.status_texts:
            status = ResultStatus.RUNNER_ERROR
        text, color = self.status_texts[status]
        return table_colored_cell.format(color=color, text=text)
    def get_other(self, _, attribute: str, row: int):
        attributes = self.results[row].test_result.attribute
        if attribute not in attributes:
            value = "---"
        else:
            value = attributes[attribute]
            if type(value) is float:
                value = round(value, 3)
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

        result_file_name = "result.html"
        with open(result_file_name ,'w', encoding='utf-8', newline='\n') as html:
            text = html_text.format(body=body, title="Result")
            text = self.insert_text_into_html_head("<body>", text, css_link1)
            text = self.insert_text_into_html_head("<body>", text, css_link2)
            text = self.insert_text_into_html_head("<body>", text, script_link)
            html.writelines(text)

    def make_summary(self) -> str:
        """サマリ情報を作る"""
        string = []
        string.append("Input file number: " + str(len(self.results)))
        if "score" not in self.attributes:
            return "<br>\n".join(string)

        file_name_list, scores_list = [], []
        for result in self.results:
            file_name_list.append(result.test_case_name)
            s = 0
            if result.test_result.error_status == ResultStatus.AC:
                if "score" in result.test_result.attribute:
                    s = result.test_result.attribute["score"]
            scores_list.append(s)

        string.append("Average Score: " + str(sum(scores_list)/len(self.results)))
        string.append("")
        string.append("Max Score: " + str(max(scores_list)))
        string.append("FileName: " + file_name_list[scores_list.index(max(scores_list))])
        string.append("")
        string.append("Minimum Score: " + str(min(scores_list)))
        string.append("FileName: " + file_name_list[scores_list.index(min(scores_list))])
        string.append("")
        return "<br>\n".join(string)
    
    def insert_text_into_html_head(self, tag: str, html_str: str, text: str) -> str:
        """HTMLの文字列のtagの中に別の文字列を挿入する"""
        html_str_list = html_str.split("\n")
        html_str_list.insert(html_str_list.index(tag) + 1, text)
        return "\n".join(html_str_list)

def init_log() -> None:
    """Logフォルダの初期化"""
    settings = get_setting()
    shutil.rmtree(settings.output_file_path, ignore_errors=True)
    os.mkdir(settings.output_file_path)

def make_log() -> None:
    """html, csv, main, in, outファイルをコピーしてlog以下に保存する"""
    settings = get_setting()
    if settings.log_file_path not in glob.glob("*"):
        os.mkdir(settings.log_file_path)
    path = os.path.join(settings.log_file_path, str(datetime.datetime.now().strftime('%Y%m%d%H%M%S')))
    os.mkdir(path)

    # mainファイルコピー
    shutil.copy("main.py", path)
    # htmlファイルコピー
    shutil.copy("result.html", path)
    os.remove("result.html") #ファイル削除
    # inファイルコピー
    shutil.copytree("in", os.path.join(path, "in"))
    # outファイルコピー
    shutil.copytree("out", os.path.join(path, "out"))

def run(run_handler: Callable[[str, str], TestCaseResult]):
    init_log()
    setting = get_setting()
    runner = TestCaseRunner(setting, run_handler)
    results = runner.run()
    html_maker = HtmlMaker(results)
    html_maker.make()
    make_log()
