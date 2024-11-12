import subprocess
import sys
import time
sys.path.append(r"..\src")

from testcaserunner import (
    run,
    ResultStatus,
    TestCaseResult,
    TestCase,
    )

def run_program(testcase: TestCase):
    """プログラムを走らせる処理をここに書く
    
    Args:
        testcase(TestCases): TestCaseクラス
    
    Returns:
        TestCaseResult: テストケースの結果
    
    TestCaseResultのattributesメンバにDict[str, int | float]で値を書いておくと
    結果として出力されるHTMLファイルに結果が載る
    
    keyとして`score`があると、スコアの平均/最大値/最小値がHTMLファイルに載る
    """
    cmd = f"python main.py < {testcase.input_file_path}"
    proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    err_stat = ResultStatus.AC
    with open(testcase.input_file_path, mode="r") as file:
        line = file.readline().strip()
    n,m = map(int, line.split())
    score = n+m
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr)
        err_stat = ResultStatus.RE
    attribute = {
        "score": score,
        "n": n,
        "m": m,
    }
    time.sleep(1)
    return TestCaseResult(err_stat, proc.stdout, proc.stderr, attribute)

if __name__ == "__main__":
    run(run_program, "in", _debug=True)
