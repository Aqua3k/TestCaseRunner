import glob
import os
import shutil
import datetime
from concurrent.futures import ProcessPoolExecutor, Future
from typing import List, Dict, Union, Callable
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path

from testcase_runner.html_templates import *

output_file_path = "out"
log_file_path = "log"
html_file_name = "result.html"

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
class RunnerSettings:
    input_file_path: str
    source_file_path: str
    stdout_file_output: bool
    stderr_file_output: bool

class DefaultRunnerSettings(RunnerSettings):
    """ランナーのデフォルト設定

    runのオプション引数でRunnerSettingsを渡さないとこの設定が使われる
    """
    def __init__(self):
        super().__init__(
            "in",
            "main.py",
            True,
            True,
        )

runner_setting = DefaultRunnerSettings()
def set_setting(setting):
    global runner_setting
    runner_setting = setting

def get_setting()->RunnerSettings:
    return runner_setting

class TestCaseRunner:
    def __init__(self, handler: Callable[[str, str], TestCaseResult]):
        settings = get_setting()
        self.input_file_path = settings.input_file_path
        self.handler = handler
    
    def run(self)->List[List[Union[str, TestCaseResult]]]:
        futures:List[Future] = []
        test_cases: List[TestCase] = []
        for input_file in glob.glob(os.path.join(self.input_file_path, "*")):
            output_file = os.path.join(output_file_path, os.path.basename(input_file))
            test_case = TestCase(input_file, output_file, self.handler)
            test_cases.append(test_case)
        with ProcessPoolExecutor() as executor:
            for test_case in test_cases:
                future = executor.submit(test_case.run_test_case)
                futures.append(future)

        results: List[TestCase] = []
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
        settings = get_setting()
        if settings.stdout_file_output:
            with open(self.stdout_file, mode='w') as f:
                f.write(self.test_result.stdout)
        if settings.stderr_file_output:
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

        with open(html_file_name ,'w', encoding='utf-8', newline='\n') as html:
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

        string.append(f"Average Score: {sum(scores_list)/len(self.results)}")
        string.append("")
        string.append(f"Max Score: {max(scores_list)}")
        string.append(f"FileName: {file_name_list[scores_list.index(max(scores_list))]}")
        string.append("")
        string.append(f"Minimum Score: {min(scores_list)}")
        string.append(f"FileName: {file_name_list[scores_list.index(min(scores_list))]}")
        string.append("")
        return "<br>\n".join(string)
    
    def insert_text_into_html_head(self, tag: str, html_str: str, text: str) -> str:
        """HTMLの文字列のtagの中に別の文字列を挿入する"""
        html_str_list = html_str.split("\n")
        html_str_list.insert(html_str_list.index(tag) + 1, text)
        return "\n".join(html_str_list)

def init_log() -> None:
    """Logフォルダの初期化"""
    shutil.rmtree(output_file_path, ignore_errors=True)
    os.mkdir(output_file_path)

def make_log() -> None:
    """html, csv, main, in, outファイルをコピーしてlog以下に保存する"""
    settings = get_setting()
    if log_file_path not in glob.glob("*"):
        os.mkdir(log_file_path)
    path = os.path.join(log_file_path, str(datetime.datetime.now().strftime('%Y%m%d%H%M%S')))
    os.mkdir(path)

    settings = get_setting()
    # mainファイルコピー
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

def run(run_handler: Callable[[str, str], TestCaseResult],
        runner_setting:RunnerSettings=DefaultRunnerSettings()):
    """run_handlerで指定した関数の処理を並列実行して結果をHTMLファイルにまとめる

    Args:
        run_handler (Callable[[str, str], TestCaseResult]):
            並列実行したい処理
            run_handlerとして渡す関数の形式について
                引数は 入力ファイルへのパス, 出力ファイルへのパス の2つ
                戻り値はTestCaseResultクラス 実行結果を各メンバに登録して返す
        runner_setting (RunnerSettings, optional): _description_. Defaults to DefaultRunnerSettings().
            ランナーを実行するときの設定
            オプション引数を渡さないとDefaultRunnerSettingsクラスの設定になる
    """
    set_setting(runner_setting)
    init_log()
    runner = TestCaseRunner(run_handler)
    results = runner.run()
    html_maker = HtmlMaker(results)
    html_maker.make()
    make_log()
