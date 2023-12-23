import glob
import os
import shutil
import datetime
from concurrent.futures import ProcessPoolExecutor, Future
from typing import List, Dict, Any, Union, Callable
import time
import subprocess
from dataclasses import dataclass
from enum import Enum, auto

from mysrc.config import get_setting, Settings
from mysrc.result_classes import ResultInfoAll, ResultInfo

def make_results(results: ResultInfoAll) -> None:
    """ファイルに出力処理のまとめ"""
    results.make_html_file()
    make_log()

def init_log() -> None:
    """Logフォルダの初期化"""
    settings = get_setting()
    shutil.rmtree(settings.output_file_path, ignore_errors=True)
    os.mkdir(settings.output_file_path)

def make_log() -> None:
    """html, csv, main, in, outファイルをコピーしてlog以下に保存する"""
    timeInfo = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    settings = get_setting()
    if settings.log_file_path not in glob.glob("*"):
        os.mkdir(settings.log_file_path)
    path =  os.path.join(settings.log_file_path, str(timeInfo))
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

class ResultStatus(Enum):
    AC = auto()
    RE = auto()
    TLE = auto()
    RUNNER_ERROR = auto()

@dataclass
class TestCaseResult:
    error_status: ResultStatus
    stdout: str
    stderr: str
    attribute: Dict[str, Union[int, float]]

class TestCaseRunner:
    def __init__(self, settings: Settings, handler: Callable[[str, str], Any]):
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
    def __init__(self, input_file, output_file, run_handler: Callable[[str, str], Any]):
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

from mysrc.html_templates import *
class HtmlMaker:
    @dataclass
    class Column:
        title: str
        getter: Callable[[int], str]

    def __init__(self, results: List[TestCase]):
        self.results = results
    
    def sortup_attributes(self):
        attributes = set()
        for result in self.results:
            test_result = result.test_result
            for attribute in test_result.attribute.keys():
                attributes.add(attribute)
        return list(attributes)
    
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
        attributes = self.sortup_attributes()
        for attribute in attributes:
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
        now = datetime.datetime.now()
        body = f'<h6>Creation date and time: {now.strftime("%Y/%m/%d %H:%M:%S")}</h6>'
        
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
        return ""
        file_name_list, scores_list = [], []
        for result in self.result_all:
            file_name_list.append(os.path.basename(result.name))
            scores_list.append(0 if result.score == "None" or result.err_stat != ResultInfo.AC else int(result.score))

        string = []
        string.append("Input file number: " + str(len(self.result_all)))
        string.append("Average Score: " + str(sum(scores_list)/len(self.result_all)))
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

def test_handler(input, output):
    cmd = f"cargo run --release --bin tester python main.py < {input}"
    start_time = time.time()
    proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    erapsed_time = time.time() - start_time
    err_stat = ResultStatus.AC
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr)
        err_stat = ResultStatus.RE
    score = 0
    result = {
        "score": score,
        "time": erapsed_time,
    }
    return TestCaseResult(err_stat, proc.stdout, proc.stderr, result)

def main():
    init_log()
    setting = get_setting()
    runner = TestCaseRunner(setting, test_handler)
    results = runner.run()
    html_maker = HtmlMaker(results)
    html_maker.make()
    #make_results(results)

if __name__ == "__main__":
    main()
