import glob
import os
import shutil
import datetime
from concurrent.futures import ProcessPoolExecutor, Future
from typing import List
import time
import subprocess
import configparser

from mysrc.config import get_setting
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

class TestCaseRunner:
    def __init__(self, input_file_path, output_file_path):
        self.input_file_path = input_file_path
        self.output_file_path = output_file_path
        self.handler = None
    
    def set_handler(self, handler):
        self.handler = handler
    
    def run_all_test_case(self):
        futures:List[Future]  = []
        results = ResultInfoAll()
        test_cases: List[TestCase] = []
        for input_file in glob.glob(os.path.join(self.input_file_path, "*")):
            basename = os.path.split(input_file)[1]
            output_file = os.path.join(self.output_file_path, basename)
            test_case = TestCase(input_file, output_file, self.handler)
            test_cases.append(test_case)
        with ProcessPoolExecutor() as executor:
            for test_case in test_cases:
                future = executor.submit(test_case.run)
                futures.append(future)
        
        for future in futures:
            results.add_result(future.result())
        
        return results

class TestCaseResult:
    def __init__(self, score, error_status, stdout, stderr):
        self.score = score
        self.error_status = error_status
        self.stdout = stdout
        self.stderr = stderr

class TestCase:
    def __init__(self, input_file, output_file, run_handler):
        assert run_handler is not None
        self.input_file = input_file
        self.stdout_file = output_file
        path, base_name = os.path.split(output_file)
        self.stderr_file = os.path.join(path, "stdout" + base_name)
        self.handler = run_handler
    
    def run(self):
        start_time = time.time()
        test_result: TestCaseResult = self.handler(self.input_file, self.stdout_file)
        erapsed_time = time.time() - start_time
        with open(self.stderr_file, mode='w') as f:
            f.write(test_result.stderr)
        result = ResultInfo(os.path.basename(self.input_file), test_result.score, erapsed_time, test_result.error_status, test_result.stdout)
        return result

def test_handler(input, output):
    print(f"{input} {output}")
    cmd = f"cargo run --release --bin tester python main.py < {input} > {output}"
    proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    err_stat = ResultInfo.AC
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr)
        err_stat = ResultInfo.RE
    score = 0

    return TestCaseResult(score, err_stat, proc.stdout, proc.stderr)

def main():
    init_log()
    config = configparser.ConfigParser()
    config.read(r'mysrc\config.ini', encoding='utf-8')
    in_path = config["path"]["in"]
    out_path = config["path"]["out"]
    runner = TestCaseRunner(in_path, out_path)
    runner.set_handler(test_handler)
    results = runner.run_all_test_case()
    make_results(results)

if __name__ == "__main__":
    main()
