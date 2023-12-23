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

@dataclass
class TestCaseResult:
    error_status: ResultStatus
    stdout: str
    stderr: str
    result: Dict[str, Union[int, float]]

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
    make_results(results)

if __name__ == "__main__":
    main()
