import subprocess
import time
import sys
import os
sys.path.append(os.path.join("..", "src"))

from testcaserunner import (
    run,
    get_log,
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
    with open(testcase.input_file_path, mode="r") as file:
        line = file.readline().strip()
    n,m = map(int, line.split())
    score = n+m
    if testcase.testcase_index % 4 == 0:
        raise(TypeError("エラー"))
    elif testcase.testcase_index % 4 == 1:
        print(proc.stdout)
        print(proc.stderr)
        return TestCaseResult({}, proc.stdout, proc.stderr, "Error")
    elif testcase.testcase_index % 4 == 2:
        print(proc.stdout)
        print(proc.stderr)
        return TestCaseResult({}, proc.stdout, proc.stderr, "Error", "this is description.")
    attribute = {
        "score": score,
        "n": n,
        "m": m,
    }
    time.sleep(1)
    return TestCaseResult(attribute, proc.stdout, proc.stderr)

if __name__ == "__main__":
    run(run_program, "in", _debug=True)
    logs = get_log()
